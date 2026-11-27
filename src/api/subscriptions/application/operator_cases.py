from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import update as sql_update

from src.api.authorization.domain.errors import (
    AccessDenied,
    IdentityProviderUnavailable,
    InvalidCredential,
)
from src.api.subscriptions.domain.operators import (
    OperatorAccessDeniedError,
    OperatorAction,
    OperatorCreateRequest,
    OperatorPage,
    OperatorResponse,
    OperatorTokenIssued,
    OperatorView,
    PlatformOperator,
    ensure_operator_action,
)
from src.api.subscriptions.repository.dao import (
    dao_operator_credentials,
    dao_platform_operators,
)
from src.api.subscriptions.repository.models import (
    PlatformOperator as PlatformOperatorRow,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.services import oidc
from src.core.services.device_tokens import (
    issue_token,
    parse_token,
)
from src.core.utils.utils import (
    Empty,
    datetime_now,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def authenticate_operator(
    db: AsyncSession, token: str | None, action: OperatorAction
) -> Result[PlatformOperator, InvalidCredential | AccessDenied]:
    """Operator credentials follow the opaque revocable pattern (D23); every
    request re-checks credential, operator status and the platform action."""
    if token is None:
        return Err(InvalidCredential())

    parsed = parse_token(token)

    if parsed is None:
        return Err(InvalidCredential())

    _, digest = parsed
    operator = await dao_platform_operators.by_credential_hash(db, digest.hex())

    if operator is Empty:
        return Err(InvalidCredential())

    try:
        ensure_operator_action(
            PlatformOperator(
                operator_id=operator.id,
                display_name=operator.display_name,
                actions=frozenset(operator.actions),
                status=operator.status,
                version=operator.version,
            ),
            credential_revoked=False,
            action=action,
        )
    except OperatorAccessDeniedError:
        return Err(AccessDenied())

    return Ok(operator)


@dataclass(frozen=True, slots=True)
class OperatorNotFound:
    pass


@dataclass(frozen=True, slots=True)
class OperatorRevoked:
    pass


def operator_view(row) -> OperatorView:
    return OperatorView(
        operator_id=row.id,
        display_name=row.display_name,
        actions=sorted(row.actions),
        status=row.status,
        version=row.version,
    )


async def issue_operator_credential(
    db: AsyncSession, oidc_token: str | None
) -> Result[
    OperatorTokenIssued,
    InvalidCredential
    | IdentityProviderUnavailable
    | OperatorNotFound
    | OperatorRevoked,
]:
    """D23: the operator authenticates in Keycloak with a separate identity and
    API issues the opaque revocable credential; the secret is returned once."""
    if oidc_token is None:
        return Err(InvalidCredential())

    verified = await oidc.verify_identity(oidc_token)

    match verified:
        case Err(oidc.OIDCError.INVALID_TOKEN):
            return Err(InvalidCredential())
        case Err(oidc.OIDCError.UNAVAILABLE):
            return Err(IdentityProviderUnavailable())
        case Ok(identity):
            pass

    async with transaction(db):
        operator = await dao_platform_operators.by_oidc(
            db, identity["issuer"], identity["subject"]
        )

        if operator is Empty:
            return Err(OperatorNotFound())

        if operator.status != "active":
            return Err(OperatorRevoked())

        token_id, secret, digest = issue_token()
        await dao_operator_credentials.insert_credential(
            db, token_id, operator.id, digest.hex()
        )

    return Ok(
        OperatorTokenIssued(
            access_token=secret, operator_id=operator.id, issued_at=datetime_now()
        )
    )


async def list_operators(
    db: AsyncSession, token: str | None, page: int, shows: int
) -> Result[OperatorPage, InvalidCredential | AccessDenied]:
    operator = await authenticate_operator(db, token, "operators")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    rows, total = await dao_platform_operators.page(db, page, shows)

    return Ok(OperatorPage(items=[operator_view(row) for row in rows], total=total))


async def create_operator(
    db: AsyncSession, token: str | None, payload: OperatorCreateRequest
) -> Result[OperatorResponse, InvalidCredential | AccessDenied]:
    async with transaction(db):
        operator = await authenticate_operator(db, token, "operators")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(_):
                pass

        operator_id = uuid7()
        await dao_platform_operators.insert_operator(
            db,
            {
                "id": operator_id,
                "oidc_issuer": payload.oidc_issuer,
                "oidc_subject": payload.oidc_subject,
                "display_name": payload.display_name,
                "actions": sorted(payload.actions),
            },
        )
        row = await dao_platform_operators.get(db, operator_id)

    return Ok(OperatorResponse(operator=operator_view(row)))


async def revoke_operator_by_id(
    db: AsyncSession, token: str | None, operator_id: UUID
) -> Result[OperatorResponse, InvalidCredential | AccessDenied | OperatorNotFound]:
    async with transaction(db):
        operator = await authenticate_operator(db, token, "operators")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(_):
                pass

        row = await dao_platform_operators.get(db, operator_id, for_update=True)

        if row is Empty:
            return Err(OperatorNotFound())

        now = datetime_now()
        await db.execute(
            sql_update(PlatformOperatorRow)
            .where(PlatformOperatorRow.id == operator_id)
            .values(status="revoked", version=row.version + 1, updated_at=now)
        )
        await dao_operator_credentials.revoke_all(db, operator_id, now)
        row = await dao_platform_operators.get(db, operator_id)

    return Ok(OperatorResponse(operator=operator_view(row)))


async def recover_operator_credential(
    db: AsyncSession, token: str | None, operator_id: UUID
) -> Result[
    OperatorTokenIssued,
    InvalidCredential | AccessDenied | OperatorNotFound | OperatorRevoked,
]:
    """Recovery revokes every previous credential and issues a new one; stored
    secrets are never recovered (D23)."""
    async with transaction(db):
        operator = await authenticate_operator(db, token, "operators")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(_):
                pass

        row = await dao_platform_operators.get(db, operator_id, for_update=True)

        if row is Empty:
            return Err(OperatorNotFound())

        if row.status != "active":
            return Err(OperatorRevoked())

        await dao_operator_credentials.revoke_all(db, operator_id, datetime_now())
        token_id, secret, digest = issue_token()
        await dao_operator_credentials.insert_credential(
            db, token_id, operator_id, digest.hex()
        )

    return Ok(
        OperatorTokenIssued(
            access_token=secret, operator_id=operator_id, issued_at=datetime_now()
        )
    )
