from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.application.management_cases import account_professional
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
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.schedule.domain.schedule import (
    CreateScheduleRulePayload,
    MinuteInterval,
    RequiredScheduleInterval,
    ScheduleDay,
    ScheduleRuleFields,
    ScheduleRulePatch,
    ScheduleRuleQuery,
    ScheduleRuleResponse,
    ScheduleRuleStatusPayload,
)
from src.api.schedule.repository.dao import dao_rules
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.schedule.repository.models import ScheduleRule


def weekly_intervals(
    rules: list[ScheduleRuleResponse], day: date
) -> list[MinuteInterval]:
    intervals = sorted(
        (row.local_start_minute, row.local_end_minute)
        for row in rules
        if row.applies(day)
    )
    merged = []

    for start, end in intervals:
        if merged and start <= merged[-1].local_end_minute:
            merged[-1].local_end_minute = max(end, merged[-1].local_end_minute)
        else:
            merged.append(
                MinuteInterval(local_start_minute=start, local_end_minute=end)
            )

    return merged


async def weekly_day(
    db: AsyncSession, context, professional_id: UUID, day: date | datetime
):
    """Weekly local intervals only; T21 adds exceptions, blocks and occupancy."""
    scope = await account_professional(db, context, professional_id)

    if isinstance(scope, Err):
        return scope

    if context.account.status != "active":
        return Err(AccessDenied())

    if isinstance(day, datetime):
        if day.tzinfo is None or day.utcoffset() is None:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        day = await dao_rules.local_date(db, context.account.time_zone, day)

    rows = await dao_rules.for_professional(db, context.account.id, professional_id)
    rules = [ScheduleRuleResponse.model_validate(row) for row in rows]

    return Ok(
        ScheduleDay(
            local_date=day,
            time_zone=context.account.time_zone,
            intervals=weekly_intervals(rules, day),
        )
    )


async def apply_rule_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
    *,
    required_intervals: tuple[RequiredScheduleInterval, ...] = (),
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """Caller locks professional then account. Required intervals come from server cases."""
    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if not (
        action == "CreateScheduleRule"
        and isinstance(payload, CreateScheduleRulePayload)
        or action == "UpdateScheduleRule"
        and isinstance(payload, ScheduleRulePatch)
        or action == "SetScheduleRuleStatus"
        and isinstance(payload, ScheduleRuleStatusPayload)
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    data = payload
    row = await dao_rules.get(
        db, entity_key, execution_options={"populate_existing": True}
    )

    if isinstance(data, CreateScheduleRulePayload):
        professional_id = data.professional_id
    elif row is Empty or row.account_id != context.account.id:
        return Err(AccountObjectNotFound())
    else:
        professional_id = row.professional_id
    scope = await account_professional(db, context, professional_id)

    if isinstance(scope, Err):
        return scope

    now = await dao_rules.server_time(db)

    if isinstance(data, CreateScheduleRulePayload):
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        values = data.model_dump()
        proposed = ScheduleRuleResponse(
            **values,
            id=entity_key,
            account_id=context.account.id,
            status="active",
            version=1,
            created_at=now,
            updated_at=now,
        )
    else:
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        values = data.model_dump(exclude_unset=True)

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        proposed = ScheduleRuleResponse.model_validate(row).model_copy(update=values)

        try:
            ScheduleRuleFields.model_validate(
                proposed.model_dump(include=set(ScheduleRuleFields.model_fields))
            )
        except ValidationError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

    if await dao_rules.duplicate(
        db, context.account.id, professional_id, proposed.model_dump(), entity_key
    ):
        return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

    # There are no appointments in this stage. T22 must supply real commitments
    # here, under the same professional lock, before enabling appointment writes.
    if required_intervals:
        rows = await dao_rules.for_professional(db, context.account.id, professional_id)
        rules = [
            ScheduleRuleResponse.model_validate(item)
            for item in rows
            if item.id != entity_key
        ] + [proposed]

        for required in required_intervals:
            if not any(
                interval.local_start_minute <= required.local_start_minute
                and required.local_end_minute <= interval.local_end_minute
                for interval in weekly_intervals(rules, required.local_date)
            ):
                return Err(
                    AccountRuleError(
                        "SLOT_UNAVAILABLE", None if row is Empty else row.version
                    )
                )

    if isinstance(data, CreateScheduleRulePayload):
        row = await dao_rules.create(db, obj_in=proposed.model_dump(), commit=False)
    else:
        row = await dao_rules.revise(db, row, values, now)

    state = ScheduleRuleResponse.model_validate(row)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "schedule_rule", str(entity_key), state, state.version, "members"
                )
            ],
            False,
        )
    )


def rule_response(row: ScheduleRule) -> dict[str, object]:
    return {
        "id": row.id,
        "account_id": row.account_id,
        "professional_id": row.professional_id,
        "iso_weekday": row.iso_weekday,
        "local_start_minute": row.local_start_minute,
        "local_end_minute": row.local_end_minute,
        "valid_from": row.valid_from,
        "valid_until": row.valid_until,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "version": row.version,
    }


async def read_rules(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: ScheduleRuleQuery,
    rule_id: UUID | None = None,
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

        if scope.value.account.status != "active":
            return Err(AccessDenied())

        if rule_id is None:
            rows, total = await dao_rules.page(db, account_id, query)
            response: dict[str, object] = {
                "items": [rule_response(row) for row in rows],
                "total": total,
            }
        else:
            row = await dao_rules.get_by(
                db, where={"id": rule_id, "account_id": account_id}
            )

            if row is Empty:
                return Err(AccountObjectNotFound())

            response = rule_response(row)

    return Ok(response)
