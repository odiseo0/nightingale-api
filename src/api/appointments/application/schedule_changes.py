from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.management_cases import apply_management_operation
from src.api.accounts.domain.accounts import (
    AccountContext,
    AccountEffect,
    AccountResponse,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.appointments.domain.appointments import IncompatibleSchedule
from src.api.appointments.repository.dao import dao_appointments
from src.api.authorization.domain.errors import AccessDenied
from src.api.schedule.application.availability_cases import available_schedule
from src.api.schedule.application.blocks_cases import apply_block_operation
from src.api.schedule.application.exceptions_cases import apply_exception_operation
from src.api.schedule.application.schedule_cases import apply_rule_operation
from src.api.schedule.domain.schedule import ScheduleBlockResponse
from src.core import Err, Result
from src.core.db import savepoint
from src.core.schema import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def apply_schedule_change(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """Professional/account locks remain held through the outer acceptance."""
    try:
        async with savepoint(db):
            if "ScheduleBlock" in action:
                effect = await apply_block_operation(
                    db, context, action, entity_key, expected_version, payload
                )
            elif "ScheduleException" in action:
                effect = await apply_exception_operation(
                    db, context, action, entity_key, expected_version, payload
                )
            elif "ScheduleRule" in action:
                effect = await apply_rule_operation(
                    db, context, action, entity_key, expected_version, payload
                )
            elif action == "UpdateAccountDetails" and isinstance(entity_key, UUID):
                effect = await apply_management_operation(
                    db, context, action, entity_key, expected_version, payload
                )
            else:
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if isinstance(effect, Err):
                return effect

            state = effect.value.state

            if (
                isinstance(state, AccountResponse)
                and state.time_zone == context.account.time_zone
            ):
                return effect

            if isinstance(state, ScheduleBlockResponse):
                if state.status == "active" and await dao_appointments.has_live_overlap(
                    db,
                    state.professional_id,
                    state.starts_at,
                    state.ends_at,
                    state.account_id,
                ):
                    raise IncompatibleSchedule()
            else:
                current = (
                    replace(context, account=state)
                    if isinstance(state, AccountResponse)
                    else context
                )
                # Check every live commitment of the changed account. An indexed
                # date filter can replace this scan when account volume needs it.
                for row in await dao_appointments.commitments(db, context.account.id):
                    duration = int((row.ends_at - row.starts_at).total_seconds() // 60)
                    available = await available_schedule(
                        db,
                        current,
                        row.professional_id,
                        row.starts_at,
                        row.ends_at,
                        duration,
                    )

                    if isinstance(available, Err) or not available.value:
                        raise IncompatibleSchedule()

            return effect
    except IncompatibleSchedule:
        return Err(AccountRuleError("SLOT_UNAVAILABLE", expected_version or None))
