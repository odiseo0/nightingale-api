from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.application.management_cases import (
    account_professional,
    own_professional,
)
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
)
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.schedule.domain.schedule import (
    AbsoluteInterval,
    CreateScheduleBlockPayload,
    ScheduleBlockFields,
    ScheduleBlockPatch,
    ScheduleBlockQuery,
    ScheduleBlockResponse,
    ScheduleRuleStatusPayload,
)
from src.api.schedule.repository.dao import dao_blocks, dao_rules
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.schedule.repository.models import ScheduleBlock


async def block_projection_accounts(
    db: AsyncSession,
    actor: AuthenticatedActor,
    account_id: UUID,
) -> list[UUID]:
    """Called after the professional lock, before sorted account controls."""
    return sorted(
        set(await dao_blocks.projection_accounts(db, account_id, actor.user_id))
        | {account_id}
    )


async def block_permission(
    db: AsyncSession,
    context: AccountContext,
    block_id: UUID,
) -> Result[None, AccessDenied | AccountObjectNotFound]:
    row = await dao_blocks.get(
        db, block_id, execution_options={"populate_existing": True}
    )

    if row is Empty:
        return Ok(None)

    if row.account_id is not None and row.account_id != context.account.id:
        return Err(AccountObjectNotFound())

    scope = await account_professional(
        db, context, row.professional_id, own=row.account_id is None
    )

    if isinstance(scope, Err):
        return scope

    return Ok(None)


async def apply_block_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
    *,
    required_intervals: tuple[AbsoluteInterval, ...] = (),
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """T22 must supply real commitments under the same professional lock."""
    if (
        payload is None
        or not isinstance(entity_key, UUID)
        or not (
            action == "CreateScheduleBlock"
            and isinstance(payload, CreateScheduleBlockPayload)
            or action == "UpdateScheduleBlock"
            and isinstance(payload, ScheduleBlockPatch)
            or action == "SetScheduleBlockStatus"
            and isinstance(payload, ScheduleRuleStatusPayload)
        )
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    row = await dao_blocks.get(
        db, entity_key, execution_options={"populate_existing": True}
    )

    if isinstance(payload, CreateScheduleBlockPayload):
        professional_id, account_id = payload.professional_id, payload.account_id
    elif row is Empty:
        return Err(AccountObjectNotFound())
    else:
        professional_id, account_id = row.professional_id, row.account_id

    if account_id is not None and account_id != context.account.id:
        return Err(AccountObjectNotFound())

    scope = await account_professional(
        db, context, professional_id, own=account_id is None
    )

    if isinstance(scope, Err):
        return scope

    now = await dao_rules.server_time(db)

    if isinstance(payload, CreateScheduleBlockPayload):
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        fields = payload
        values = payload.model_dump()
        proposed = ScheduleBlockResponse(
            **values,
            id=entity_key,
            status="active",
            created_at=now,
            updated_at=now,
            version=1,
        )
    else:
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        values = payload.model_dump(exclude_unset=True)

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        proposed = ScheduleBlockResponse.model_validate(row).model_copy(update=values)

        try:
            fields = ScheduleBlockFields.model_validate(
                proposed.model_dump(include=set(ScheduleBlockFields.model_fields))
            )
        except ValidationError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

    if proposed.status == "active" and any(
        fields.starts_at < interval.ends_at and interval.starts_at < fields.ends_at
        for interval in required_intervals
    ):
        return Err(
            AccountRuleError("SLOT_UNAVAILABLE", None if row is Empty else row.version)
        )

    if isinstance(payload, CreateScheduleBlockPayload):
        row = await dao_blocks.create(db, obj_in=proposed.model_dump(), commit=False)
    else:
        row = await dao_blocks.revise(db, row, values, now)

    state = ScheduleBlockResponse.model_validate(
        block_response(row, reveal_reason=True)
    )
    projected = ScheduleBlockResponse.model_validate(
        block_response(row, reveal_reason=account_id is not None)
    )
    targets = (
        await dao_blocks.projection_accounts(
            db, context.account.id, context.actor.user_id
        )
        if account_id is None
        else [account_id]
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "schedule_block",
                    str(entity_key),
                    projected,
                    state.version,
                    "members",
                    target,
                )
                for target in targets
            ],
            False,
        )
    )


def block_response(row: ScheduleBlock, *, reveal_reason: bool) -> dict[str, object]:
    return {
        "id": row.id,
        "account_id": row.account_id,
        "professional_id": row.professional_id,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
        "reason_code": row.reason_code if reveal_reason else None,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "version": row.version,
    }


async def read_blocks(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: ScheduleBlockQuery | None = None,
    block_id: UUID | None = None,
) -> Result[
    dict[str, object],
    InvalidCredential | AccountNotFound | AccountObjectNotFound | AccessDenied,
]:
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

        if context.account.status != "active":
            return Err(AccessDenied())

        own = await own_professional(db, context.actor.user_id)
        own_id = own.value.id if isinstance(own, Ok) else None

        if block_id is not None:
            row = await dao_blocks.get(db, block_id)

            if (
                row is Empty
                or row.account_id is not None
                and row.account_id != account_id
            ):
                return Err(AccountObjectNotFound())

            professional = await account_professional(db, context, row.professional_id)

            if isinstance(professional, Err):
                return professional

            response = block_response(
                row,
                reveal_reason=row.account_id is not None
                or row.professional_id == own_id,
            )
        elif query is not None:
            rows, total = await dao_blocks.page(db, account_id, query)
            response = {
                "items": [
                    block_response(
                        row,
                        reveal_reason=row.account_id is not None
                        or row.professional_id == own_id,
                    )
                    for row in rows
                ],
                "total": total,
            }
        else:
            return Err(AccountObjectNotFound())

    return Ok(response)
