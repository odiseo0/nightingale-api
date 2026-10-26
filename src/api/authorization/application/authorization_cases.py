from __future__ import annotations

import hmac
from datetime import datetime
from typing import TYPE_CHECKING, assert_never
from uuid import UUID, uuid7

from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.domain.authorization import (
    AuthConfigResponse,
    AuthenticatedActor,
    DeviceRegistrationRequest,
    DeviceResponse,
    DeviceTokenIssued,
    ExternalIdentity,
    UserIdentity,
)
from src.api.authorization.domain.errors import (
    AccessDenied,
    DeviceNotFound,
    IdentityProviderUnavailable,
    InvalidCredential,
)
from src.api.authorization.repository.dao import (
    dao_device_tokens,
    dao_devices,
    dao_users,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery, PaginatedResponse
from src.core.services import oidc
from src.core.services.device_tokens import issue_token, parse_token
from src.core.utils.utils import Empty
from src.settings.oidc_settings import oidc_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def get_config() -> Result[AuthConfigResponse, IdentityProviderUnavailable]:
    if not oidc_settings.issuer or not oidc_settings.jwks_uri:
        return Err(IdentityProviderUnavailable())

    return Ok(
        AuthConfigResponse(
            issuer=oidc_settings.issuer,
            public_client_id=oidc_settings.public_client_id,
            audience=oidc_settings.audience,
        )
    )


async def authenticate(
    db: AsyncSession,
    credential: str | None,
    related_device_id: UUID | None = None,
) -> Result[AuthenticatedActor, InvalidCredential]:
    """The caller owns the transaction so identity locks cover its full operation."""
    parsed = parse_token(credential) if credential else None

    if parsed is None:
        return Err(InvalidCredential())

    token_id, fingerprint = parsed
    token = await dao_device_tokens.get(db, token_id)

    if token is Empty or not hmac.compare_digest(token.secret_hash, fingerprint):
        return Err(InvalidCredential())

    if related_device_id is not None:
        related = await dao_devices.get(db, related_device_id)
        await dao_users.lock_identified(
            db, [token.user_id] + ([] if related is Empty else [related.user_id])
        )

    # Keep the established user -> device -> token lock order. The user lock
    # serializes this user's requests; change it only after testing revocation races.
    user = await dao_users.get_for_update(
        db,
        token.user_id,
        execution_options={"populate_existing": True},
    )
    device = await dao_devices.get_owned_for_update(db, token.device_id, token.user_id)

    if related_device_id is not None and related is not Empty:
        await dao_devices.get_owned_for_update(db, related.id, related.user_id)

    token = await dao_device_tokens.get_for_update(
        db,
        token_id,
        execution_options={"populate_existing": True},
    )

    if (
        user is Empty
        or user.status != "active"
        or device is Empty
        or device.status != "active"
        or token is Empty
        or token.revoked_at is not None
    ):
        return Err(InvalidCredential())

    return Ok(AuthenticatedActor(user.id, device.id, token.id))


async def register_device(
    db: AsyncSession,
    credential: str | None,
    obj_in: DeviceRegistrationRequest,
    correlation_id: UUID | None = None,
) -> Result[
    DeviceTokenIssued, InvalidCredential | IdentityProviderUnavailable | AccessDenied
]:
    if not credential:
        return Err(InvalidCredential())

    # The provider call happens before opening the database transaction.
    result = await oidc.verify_identity(credential)

    match result:
        case Ok(value):
            identity = ExternalIdentity(**value)
        case Err(oidc.OIDCError.INVALID_TOKEN):
            return Err(InvalidCredential())
        case Err(oidc.OIDCError.UNAVAILABLE):
            return Err(IdentityProviderUnavailable())
        case unexpected:
            assert_never(unexpected)

    async with transaction(db):
        now = await dao_users.get_server_time(db)
        user = await dao_users.get_or_create(db, identity, now, commit=False)

        if user.status != "active":
            return Err(AccessDenied())

        device = await dao_devices.create(
            db,
            commit=False,
            obj_in={
                "id": uuid7(),
                "user_id": user.id,
                "display_name": obj_in.device_name,
                "client_version": obj_in.client_version,
                "local_schema_version": obj_in.local_schema_version,
                "created_at": now,
                "updated_at": now,
            },
        )
        token_id, secret, fingerprint = issue_token()
        await dao_device_tokens.create(
            db,
            commit=False,
            obj_in={
                "id": token_id,
                "device_id": device.id,
                "user_id": user.id,
                "secret_hash": fingerprint,
                "created_at": now,
            },
        )
        issued = DeviceTokenIssued(
            access_token=secret,
            token_id=token_id,
            device_id=device.id,
            user_id=user.id,
            issued_at=now,
        )
        await record_control(
            db,
            ControlAudit(
                actor_user_id=user.id,
                actor_device_id=device.id,
                action="IssueDeviceToken",
                object_type="device",
                object_key=str(device.id),
                outcome="accepted",
                correlation_id=correlation_id or uuid7(),
                occurred_at=now,
            ),
        )

    return Ok(issued)


async def rotate_token(
    db: AsyncSession,
    credential: str | None,
    device_id: UUID,
    correlation_id: UUID | None = None,
) -> Result[DeviceTokenIssued, InvalidCredential | AccessDenied]:
    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                pass
            case Err(error):
                return Err(error)

        if actor.device_id != device_id:
            return Err(AccessDenied())

        now = await dao_users.get_server_time(db)
        await dao_device_tokens.update(
            db, actor.token_id, {"revoked_at": now}, commit=False
        )
        token_id, secret, fingerprint = issue_token()
        await dao_device_tokens.create(
            db,
            commit=False,
            obj_in={
                "id": token_id,
                "device_id": actor.device_id,
                "user_id": actor.user_id,
                "secret_hash": fingerprint,
                "created_at": now,
            },
        )
        await dao_device_tokens.update(
            db,
            actor.token_id,
            {"replaced_by_token_id": token_id},
            commit=False,
        )
        issued = DeviceTokenIssued(
            access_token=secret,
            token_id=token_id,
            device_id=actor.device_id,
            user_id=actor.user_id,
            issued_at=now,
        )
        await record_control(
            db,
            ControlAudit(
                actor_user_id=actor.user_id,
                actor_device_id=actor.device_id,
                action="RotateDeviceToken",
                object_type="device",
                object_key=str(device_id),
                outcome="accepted",
                correlation_id=correlation_id or uuid7(),
                occurred_at=now,
            ),
        )

    return Ok(issued)


async def revoke_device(
    db: AsyncSession,
    credential: str | None,
    device_id: UUID,
    correlation_id: UUID | None = None,
) -> Result[None, InvalidCredential | DeviceNotFound]:
    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                pass
            case Err(error):
                return Err(error)

        device = await dao_devices.get_owned_for_update(db, device_id, actor.user_id)

        if device is Empty:
            return Err(DeviceNotFound(device_id))

        if device.status == "revoked":
            return Ok(None)

        now = await dao_users.get_server_time(db)
        await dao_devices.update(
            db,
            device.id,
            {
                "status": "revoked",
                "version": device.version + 1,
                "updated_at": now,
            },
            commit=False,
        )
        await dao_device_tokens.revoke_for_device(db, device.id, now, commit=False)
        await record_control(
            db,
            ControlAudit(
                actor_user_id=actor.user_id,
                actor_device_id=actor.device_id,
                action="RevokeDevice",
                object_type="device",
                object_key=str(device_id),
                outcome="accepted",
                correlation_id=correlation_id or uuid7(),
                occurred_at=now,
            ),
        )

    return Ok(None)


async def ensure_identity(
    db: AsyncSession,
    identity: ExternalIdentity,
    now: datetime,
) -> Result[UserIdentity, AccessDenied]:
    """Join the caller's transaction; identifying a person grants no account access."""
    user = await dao_users.get_or_create(db, identity, now, commit=False)

    if user.status != "active":
        return Err(AccessDenied())

    return Ok(UserIdentity.model_validate(user))


async def get_identity(
    db: AsyncSession,
    actor: AuthenticatedActor,
) -> Result[UserIdentity, InvalidCredential]:
    user = await dao_users.get_for_update(
        db,
        actor.user_id,
        execution_options={"populate_existing": True},
    )

    if user is Empty or user.status != "active":
        return Err(InvalidCredential())

    return Ok(UserIdentity.model_validate(user))


async def get_devices(
    db: AsyncSession,
    credential: str | None,
    page: int = 1,
    shows: int = 100,
) -> Result[PaginatedResponse[DeviceResponse], InvalidCredential]:
    query = PageQuery(page=page, shows=shows)

    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                pass
            case Err(error):
                return Err(error)

        devices, total = await dao_devices.get_multi(
            db,
            where={"user_id": actor.user_id},
            page=(query.page - 1) * query.shows,
            shows=query.shows,
            ordering=[("id", False)],
        )
        response = PaginatedResponse[DeviceResponse](items=devices, total=total)

    return Ok(response)


async def get_own_device(
    db: AsyncSession,
    actor: AuthenticatedActor,
) -> Result[DeviceResponse, InvalidCredential]:
    device = await dao_devices.get_owned_for_update(db, actor.device_id, actor.user_id)

    if device is Empty or device.status != "active":
        return Err(InvalidCredential())

    return Ok(DeviceResponse.model_validate(device))


async def identified_users(
    db: AsyncSession, user_ids: list[UUID]
) -> dict[UUID, UserIdentity]:
    """Internal lookup for known IDs; callers must first check their scope."""
    users = await dao_users.get_identified(db, user_ids)

    return {user.id: UserIdentity.model_validate(user) for user in users}


async def device_details(db: AsyncSession, device_id: UUID) -> DeviceResponse | None:
    device = await dao_devices.get(db, device_id)

    return None if device is Empty else DeviceResponse.model_validate(device)


async def device_summaries(
    db: AsyncSession, device_ids: list[UUID]
) -> dict[UUID, DeviceResponse]:
    devices = await dao_devices.get_identified(db, device_ids)

    return {device.id: DeviceResponse.model_validate(device) for device in devices}
