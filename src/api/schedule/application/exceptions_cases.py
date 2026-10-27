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
from src.api.schedule.application.schedule_cases import weekly_day
from src.api.schedule.domain.schedule import (
    CreateScheduleExceptionPayload,
    MinuteInterval,
    RequiredScheduleInterval,
    ScheduleDay,
    ScheduleExceptionFields,
    ScheduleExceptionPatch,
    ScheduleExceptionQuery,
    ScheduleExceptionResponse,
    ScheduleRuleStatusPayload,
)
from src.api.schedule.repository.dao import dao_exceptions, dao_rules
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.schedule.repository.models import ScheduleException


async def daily_day(
    db: AsyncSession,
    context: AccountContext,
    professional_id: UUID,
    day: date | datetime,
) -> Result[ScheduleDay, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    result = await weekly_day(db, context, professional_id, day)

    if isinstance(result, Err):
        return result

    schedule = result.value
    row = await dao_exceptions.for_day(
        db, context.account.id, professional_id, schedule.local_date
    )

    if row is not None and row.status == "active":
        schedule.intervals = []

        if (
            row.kind == "replacement"
            and row.local_start_minute is not None
            and row.local_end_minute is not None
        ):
            schedule.intervals = [
                MinuteInterval(
                    local_start_minute=row.local_start_minute,
                    local_end_minute=row.local_end_minute,
                )
            ]

    return Ok(schedule)


async def apply_exception_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
    *,
    required_intervals: tuple[RequiredScheduleInterval, ...] = (),
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """Caller holds the professional and account locks; T22 supplies real bookings."""
    if (
        payload is None
        or not isinstance(entity_key, UUID)
        or not (
            action == "CreateScheduleException"
            and isinstance(payload, CreateScheduleExceptionPayload)
            or action == "UpdateScheduleException"
            and isinstance(payload, ScheduleExceptionPatch)
            or action == "SetScheduleExceptionStatus"
            and isinstance(payload, ScheduleRuleStatusPayload)
        )
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    row = await dao_exceptions.get(
        db, entity_key, execution_options={"populate_existing": True}
    )

    if isinstance(payload, CreateScheduleExceptionPayload):
        professional_id = payload.professional_id
    elif row is Empty or row.account_id != context.account.id:
        return Err(AccountObjectNotFound())
    else:
        professional_id = row.professional_id

    scope = await account_professional(db, context, professional_id)

    if isinstance(scope, Err):
        return scope

    now = await dao_rules.server_time(db)

    if isinstance(payload, CreateScheduleExceptionPayload):
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        values = payload.model_dump()
        proposed = ScheduleExceptionResponse(
            **values,
            id=entity_key,
            account_id=context.account.id,
            status="active",
            created_at=now,
            updated_at=now,
            version=1,
        )
        fields = payload
    else:
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        values = payload.model_dump(exclude_unset=True)

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        proposed = ScheduleExceptionResponse.model_validate(row).model_copy(
            update=values
        )

        try:
            fields = ScheduleExceptionFields.model_validate(
                proposed.model_dump(include=set(ScheduleExceptionFields.model_fields))
            )
        except ValidationError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

    existing = await dao_exceptions.for_day(
        db, context.account.id, professional_id, fields.local_date
    )

    if existing is not None and existing.id != entity_key:
        return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

    # Only a controlled server input exists until T22 connects actual occupancy.
    for required in required_intervals:
        if required.local_date != fields.local_date and (
            row is Empty or required.local_date != row.local_date
        ):
            continue

        if proposed.status == "active" and required.local_date == fields.local_date:
            intervals = []

            if (
                fields.kind == "replacement"
                and fields.local_start_minute is not None
                and fields.local_end_minute is not None
            ):
                intervals = [
                    MinuteInterval(
                        local_start_minute=fields.local_start_minute,
                        local_end_minute=fields.local_end_minute,
                    )
                ]
        else:
            regular = await weekly_day(
                db, context, professional_id, required.local_date
            )

            if isinstance(regular, Err):
                return regular

            intervals = regular.value.intervals

        if not any(
            i.local_start_minute <= required.local_start_minute
            and required.local_end_minute <= i.local_end_minute
            for i in intervals
        ):
            return Err(
                AccountRuleError(
                    "SLOT_UNAVAILABLE", None if row is Empty else row.version
                )
            )

    if isinstance(payload, CreateScheduleExceptionPayload):
        row = await dao_exceptions.create(
            db, obj_in=proposed.model_dump(), commit=False
        )
    else:
        row = await dao_exceptions.revise(db, row, values, now)

    state = ScheduleExceptionResponse.model_validate(exception_response(row))

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "schedule_exception",
                    str(entity_key),
                    state,
                    state.version,
                    "members",
                )
            ],
            False,
        )
    )


def exception_response(row: ScheduleException) -> dict[str, object]:
    return {
        "id": row.id,
        "account_id": row.account_id,
        "professional_id": row.professional_id,
        "local_date": row.local_date,
        "kind": row.kind,
        "local_start_minute": row.local_start_minute,
        "local_end_minute": row.local_end_minute,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "version": row.version,
    }


async def read_exceptions(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: ScheduleExceptionQuery | None = None,
    exception_id: UUID | None = None,
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

        if exception_id is not None:
            row = await dao_exceptions.get_by(
                db, where={"id": exception_id, "account_id": account_id}
            )

            if row is Empty:
                return Err(AccountObjectNotFound())

            response = exception_response(row)
        elif query is not None:
            rows, total = await dao_exceptions.page(db, account_id, query)
            response = {
                "items": [exception_response(row) for row in rows],
                "total": total,
            }
        else:
            return Err(AccountObjectNotFound())

    return Ok(response)
