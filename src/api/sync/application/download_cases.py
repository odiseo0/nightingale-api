from __future__ import annotations

from datetime import timedelta
from itertools import groupby
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.appointments.application.appointments_cases import captured_history
from src.api.appointments.domain.appointments import AppointmentResponse
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.schedule.domain.schedule import (
    ScheduleBlockResponse,
    ScheduleExceptionResponse,
    ScheduleRuleResponse,
)
from src.api.sync.application.operations_cases import authorized_context
from src.api.sync.domain.downloads import (
    ChangeGroup,
    ChangePage,
    SyncChange,
    SyncPosition,
    SyncWindow,
)
from src.api.sync.domain.errors import SyncReadError
from src.api.sync.repository.dao import dao_changes, dao_heads
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.services.sync_signatures import sign_position, verify_position
from src.settings.api_settings import api_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.sync.repository.models import ChangeLog


def visible_change(row: ChangeLog, window: SyncWindow) -> SyncChange | None:
    change = SyncChange.model_validate(
        {
            "entity_type": row.entity_type,
            "entity_key": row.entity_key,
            "entity_version": row.entity_version,
            "change_kind": row.change_kind,
            "state": row.projection_json,
        }
    )
    state = change.state
    if isinstance(state, AppointmentResponse):
        if state.starts_at < window.ends_at and window.starts_at < state.ends_at:
            return change

        if (
            row.previous_starts_at is None
            or row.previous_ends_at is None
            or not (
                row.previous_starts_at < window.ends_at
                and window.starts_at < row.previous_ends_at
            )
        ):
            return None

        return change.model_copy(update={"change_kind": "remove", "state": None})

    in_window = True
    if isinstance(state, ScheduleBlockResponse):
        in_window = (
            state.starts_at < window.ends_at and window.starts_at < state.ends_at
        )
    elif isinstance(state, ScheduleExceptionResponse):
        in_window = (
            window.appointments_from <= state.local_date < window.appointments_until
        )
    elif isinstance(state, ScheduleRuleResponse):
        in_window = state.valid_from < window.appointments_until and (
            state.valid_until is None or window.appointments_from <= state.valid_until
        )

    if not in_window:
        return (
            change.model_copy(update={"change_kind": "remove", "state": None})
            if row.entity_version > 1
            else None
        )

    return change


async def read_changes(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    cursor: str,
) -> Result[
    ChangePage,
    InvalidCredential
    | AccessDenied
    | AccountNotFound
    | AccountObjectNotFound
    | SyncReadError,
]:
    async with transaction(db):
        scope = await authorized_context(db, credential, account_id)
        if isinstance(scope, Err):
            return scope

        context, head = scope.value
        secret = api_settings.sync_signing_key
        if secret is None:
            return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

        key = secret.get_secret_value().encode("utf-8")
        body = verify_position(cursor, key)
        if body is None:
            return Err(SyncReadError("CURSOR_EXPIRED"))

        try:
            position = SyncPosition.model_validate_json(body)
        except ValidationError:
            return Err(SyncReadError("CURSOR_EXPIRED"))

        now = await dao_heads.get_server_time(db)
        if (
            position.account_id != account_id
            or position.user_id != context.actor.user_id
            or position.device_id != context.actor.device_id
            or position.audience != ("owner" if context.owner else "members")
            or position.permission_epoch != head.permission_epoch
            or position.sequence < head.retained_from_sequence - 1
            or position.sequence > head.last_sequence
            or position.expires_at <= now
            or position.issued_at > now
        ):
            return Err(SyncReadError("CURSOR_EXPIRED"))

        rows, has_more = await dao_changes.groups_after(
            db, account_id, position.sequence, head.last_sequence
        )
        groups: list[ChangeGroup] = []
        for _, entries in groupby(rows, key=lambda row: row.sequence):
            group = list(entries)
            changes: list[SyncChange] = []
            for row in group:
                if row.audience == "owner" and not context.owner:
                    continue

                try:
                    change = visible_change(row, position.window)
                except ValidationError as error:
                    raise DAOError("El cambio no cumple su esquema") from error

                if change is not None:
                    changes.append(change)
                    if isinstance(change.state, AppointmentResponse):
                        history = await captured_history(db, change.state)
                        changes.append(
                            SyncChange(
                                entity_type="appointment_history",
                                entity_key=change.entity_key,
                                entity_version=change.entity_version,
                                change_kind="upsert",
                                state=history,
                            )
                        )
                    elif (
                        change.entity_type == "appointment"
                        and change.change_kind == "remove"
                    ):
                        changes.append(
                            SyncChange(
                                entity_type="appointment_history",
                                entity_key=change.entity_key,
                                entity_version=change.entity_version,
                                change_kind="remove",
                                state=None,
                            )
                        )

            if changes:
                groups.append(
                    ChangeGroup(
                        group_id=group[0].group_id,
                        operation_id=group[0].operation_id,
                        accepted_at=group[0].accepted_at,
                        changes=changes,
                    )
                )

        next_position = position.model_copy(
            update={
                "sequence": rows[-1].sequence if rows else head.last_sequence,
                "issued_at": now,
                "expires_at": now + timedelta(days=90),
            }
        )
        response = ChangePage(
            groups=groups,
            has_more=has_more,
            next_cursor=sign_position(
                next_position.model_dump_json(by_alias=True).encode("utf-8"),
                key,
            ),
        )

    return Ok(response)
