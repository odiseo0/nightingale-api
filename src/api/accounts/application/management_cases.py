from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountDetails,
    AccountDetailsPatch,
    AccountDeviceResponse,
    AccountEffect,
    AccountPolicyPayload,
    AccountResponse,
    MemberResponse,
    MembershipStatusPayload,
    ProfessionalPayload,
    ProfessionalQuery,
    ProfessionalResponse,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.accounts.repository.dao import (
    dao_account_devices,
    dao_accounts,
    dao_memberships,
    dao_professionals,
)
from src.api.authorization.application.authorization_cases import (
    authenticate,
    device_details,
    device_summaries,
    identified_users,
)
from src.api.authorization.domain.errors import AccessDenied
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel, PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def lock_professional(db: AsyncSession, account_id: UUID) -> None:
    await dao_professionals.lock_for_account(db, account_id)


async def catalog_accounts(
    db: AsyncSession, user_id: UUID, account_id: UUID
) -> list[UUID]:
    """Call after locking the account's professional, before account controls."""
    return await dao_professionals.catalog_accounts(db, user_id, account_id)


async def own_professional(
    db: AsyncSession, user_id: UUID
) -> Result[ProfessionalResponse, AccountObjectNotFound]:
    row = await dao_professionals.get_by(
        db, where={"user_id": user_id}, execution_options={"populate_existing": True}
    )

    if row is Empty:
        return Err(AccountObjectNotFound())

    return Ok(ProfessionalResponse.model_validate(row))


async def account_professional(
    db: AsyncSession,
    context: AccountContext,
    professional_id: UUID,
    *,
    own: bool = False,
) -> Result[ProfessionalResponse, AccountObjectNotFound | AccessDenied]:
    row = await dao_professionals.scoped(db, context.account.id, professional_id)

    if row is None:
        return Err(AccountObjectNotFound())

    professional, link_status, membership_status = row

    if own and professional.user_id != context.actor.user_id:
        return Err(AccountObjectNotFound())

    identity = await identified_users(db, [professional.user_id])

    if (
        professional.status != "active"
        or link_status != "active"
        or membership_status != "active"
        or identity[professional.user_id].status != "active"
    ):
        return Err(AccessDenied())

    return Ok(ProfessionalResponse.model_validate(professional))


async def apply_management_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if not context.owner:
        return Err(AccessDenied())

    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    now = await dao_accounts.get_server_time(db)

    if action in ("UpdateAccountDetails", "UpdateAccountPolicy", "SetAccountStatus"):
        if entity_key != context.account.id:
            return Err(AccountObjectNotFound())

        current = context.account

        if current.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", current.version))

        try:
            if action == "UpdateAccountDetails":
                if not isinstance(payload, AccountDetailsPatch):
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                patch = payload

                if not patch.model_fields_set:
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                changes = patch.model_dump(exclude_unset=True)
                AccountDetails.model_validate(
                    {
                        **{
                            name: getattr(current, name)
                            for name in AccountDetails.model_fields
                        },
                        **changes,
                    }
                )

                if "time_zone" in changes and not await dao_accounts.is_known_time_zone(
                    db, changes["time_zone"]
                ):
                    return Err(AccountRuleError("VALIDATION_ERROR"))
            elif action == "UpdateAccountPolicy":
                if not isinstance(payload, AccountPolicyPayload):
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                changes = payload.model_dump()
            else:
                if not isinstance(payload, MembershipStatusPayload):
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                changes = payload.model_dump()
        except ValidationError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if all(getattr(current, name) == value for name, value in changes.items()):
            return Err(AccountRuleError("NO_CHANGES", current.version))

        row = await dao_accounts.revise(db, entity_key, changes, now)
        state = AccountResponse.model_validate(row)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [
                    AccountChange(
                        "account", str(entity_key), state, state.version, "members"
                    )
                ],
                action == "SetAccountStatus",
            )
        )

    if action == "UpdateProfessionalProfile":
        row = await dao_professionals.get_by(
            db, where={"user_id": context.actor.user_id}
        )

        if row is Empty or row.id != entity_key:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if not isinstance(payload, ProfessionalPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        data = payload

        if data.public_name == row.public_name:
            return Err(AccountRuleError("NO_CHANGES", row.version))

        row = await dao_professionals.rename(db, entity_key, data.public_name, now)
        state = ProfessionalResponse.model_validate(row)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [
                    AccountChange(
                        "professional", str(entity_key), state, state.version, "members"
                    )
                ],
                False,
            )
        )

    if payload is None or payload.model_fields_set:
        return Err(AccountRuleError("VALIDATION_ERROR"))

    row = await dao_account_devices.get_scoped(db, context.account.id, entity_key)

    if row is Empty:
        return Err(AccountObjectNotFound())

    if row.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", row.version))

    target_status = "revoked" if action == "RevokeAccountDevice" else "active"

    if row.status == target_status:
        return Err(AccountRuleError("NO_CHANGES", row.version))

    details = await device_details(db, entity_key)

    if details is None:
        return Err(AccessDenied())

    if target_status == "active":
        users = await identified_users(db, [row.user_id])
        membership = await dao_memberships.get_scoped(
            db, context.account.id, row.user_id
        )

        if (
            details.status != "active"
            or users[row.user_id].status != "active"
            or membership is Empty
            or membership.status != "active"
        ):
            return Err(AccessDenied())

    row = await dao_account_devices.set_status(
        db, row, target_status, context.actor.user_id, now
    )

    state = AccountDeviceResponse(
        device_id=row.device_id,
        display_name=details.display_name,
        status=row.status,
        client_version=details.client_version,
        local_schema_version=details.local_schema_version,
        last_seen_at=details.last_seen_at,
        version=row.version,
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [AccountChange("account_device", str(entity_key), state, state.version)],
            True,
        )
    )


async def get_team(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: PageQuery,
    devices: bool = False,
):
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        scope = await account_context(
            db, identity.value, account_id, require_device=True
        )

        if isinstance(scope, Err):
            return scope

        context = scope.value

        if not context.owner or context.account.status != "active":
            return Err(AccessDenied())

        offset = (query.page - 1) * query.shows

        if devices:
            rows, total = await dao_account_devices.page(
                db, account_id, offset, query.shows
            )
            details = await device_summaries(db, [row.device_id for row in rows])
            items = [
                AccountDeviceResponse(
                    device_id=row.device_id,
                    display_name=details[row.device_id].display_name,
                    status=row.status,
                    client_version=details[row.device_id].client_version,
                    local_schema_version=details[row.device_id].local_schema_version,
                    last_seen_at=details[row.device_id].last_seen_at,
                    version=row.version,
                )
                for row in rows
            ]
            response = PaginatedResponse[AccountDeviceResponse](
                items=items, total=total
            )
        else:
            rows, total = await dao_memberships.page(
                db, account_id, offset, query.shows
            )
            details = await identified_users(db, [row.user_id for row in rows])
            items = [
                MemberResponse(
                    user_id=row.user_id,
                    display_name=details[row.user_id].display_name,
                    role="owner"
                    if row.user_id == context.account.owner_user_id
                    else "assistant",
                    status=row.status,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    version=row.version,
                )
                for row in rows
            ]
            response = PaginatedResponse[MemberResponse](items=items, total=total)

    return Ok(response)


async def get_professionals(
    db: AsyncSession, credential: str | None, account_id: UUID, query: ProfessionalQuery
):
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        scope = await account_context(
            db, identity.value, account_id, require_device=True
        )

        if isinstance(scope, Err):
            return scope

        if scope.value.account.status != "active":
            return Err(AccessDenied())

        rows, total = await dao_professionals.page(
            db, account_id, (query.page - 1) * query.shows, query.shows, query.status
        )
        response = PaginatedResponse[ProfessionalResponse](
            items=[ProfessionalResponse.model_validate(row) for row in rows],
            total=total,
        )

    return Ok(response)
