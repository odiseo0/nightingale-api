from typing import TYPE_CHECKING

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.domain.operators import (
    OperatorAccessDeniedError,
    OperatorAction,
    PlatformOperator,
    ensure_operator_action,
)
from src.api.subscriptions.repository.dao import dao_platform_operators
from src.core import Err, Ok, Result
from src.core.services.device_tokens import parse_token
from src.core.utils.utils import Empty

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
