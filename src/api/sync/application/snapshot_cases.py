from __future__ import annotations

import json
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from pydantic import ValidationError

from src.api.accounts.application.snapshot_cases import snapshot_accounts
from src.api.accounts.domain.accounts import AccountContext, ProfessionalResponse
from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.appointments.application.snapshot_cases import snapshot_appointments
from src.api.appointments.domain.appointments import AppointmentHistoryProjection, AppointmentResponse
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.patients.application.snapshot_cases import snapshot_patients
from src.api.schedule.application.snapshot_cases import snapshot_schedule
from src.api.services.application.snapshot_cases import snapshot_services
from src.api.sync.application.operations_cases import authorized_context
from src.api.sync.domain.downloads import SnapshotRequest, SnapshotResponse, SyncItem, SyncPosition, SyncWindow
from src.api.sync.domain.errors import SyncReadError
from src.api.sync.repository.dao import dao_heads, dao_snapshot_items, dao_snapshots
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.schema import PageQuery, PaginatedResponse
from src.core.services.sync_signatures import sign_position
from src.core.utils.utils import Empty
from src.settings.api_settings import api_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.sync.repository.models import SyncSnapshot

type SnapshotError = InvalidCredential | AccessDenied | AccountNotFound | AccountObjectNotFound | SyncReadError


def snapshot_response(row: SyncSnapshot) -> Result[SnapshotResponse, SyncReadError]:
    secret = api_settings.sync_signing_key
    if secret is None:
        return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

    window = SyncWindow(appointments_from=row.appointments_from, appointments_until=row.appointments_until,
                        time_zone=row.window_time_zone, starts_at=row.window_starts_at, ends_at=row.window_ends_at)
    position = SyncPosition(account_id=row.account_id, user_id=row.user_id, device_id=row.device_id, audience=row.audience,
                            permission_epoch=row.permission_epoch, sequence=row.base_sequence, window=window,
                            issued_at=row.created_at, expires_at=row.created_at + timedelta(days=90))
    cursor = sign_position(position.model_dump_json(by_alias=True).encode(), secret.get_secret_value().encode())

    return Ok(SnapshotResponse(snapshot_id=row.id, account_id=row.account_id, model_revision=row.model_revision,
                               window=window, base_cursor=cursor, expires_at=row.expires_at, item_count=row.item_count))


async def create_snapshot(
    db: AsyncSession, credential: str | None, account_id: UUID, request: SnapshotRequest,
) -> Result[SnapshotResponse, SnapshotError]:
    async with transaction(db, isolation_level="REPEATABLE READ"):
        scope = await authorized_context(db, credential, account_id)
        if isinstance(scope, Err):
            return scope

        context, head = scope.value
        if api_settings.sync_signing_key is None:
            return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

        now = await dao_heads.get_server_time(db)
        today = await dao_heads.local_date(db, context.account.time_zone, now)
        start = request.appointments_from or today - timedelta(days=30)
        end = request.appointments_until or today + timedelta(days=181)
        starts_at, ends_at = await dao_heads.window_bounds(db, start, end, context.account.time_zone)
        try:
            window = SyncWindow(appointments_from=start, appointments_until=end, time_zone=context.account.time_zone,
                                starts_at=starts_at, ends_at=ends_at)
        except ValidationError:
            return Err(SyncReadError("VALIDATION_ERROR"))

        items = await snapshot_accounts(db, context)
        appointments = await snapshot_appointments(db, context, window)
        states = [item.state for item in appointments if isinstance(item.state, AppointmentResponse)]
        histories = [entry for item in appointments if isinstance(item.state, AppointmentHistoryProjection) for entry in item.state.items]
        required_contacts = {state.responsible_contact_id for state in [*states, *histories] if state.responsible_contact_id is not None}
        items.extend(await snapshot_patients(db, context, {state.patient_id for state in states}, required_contacts))
        professionals = [item.state for item in items if isinstance(item.state, ProfessionalResponse)]
        items.extend(await snapshot_services(db, context, professionals, {state.service_id for state in states}))
        items.extend(await snapshot_schedule(db, context, window))
        items.extend(appointments)
        items.sort(key=lambda item: (item.entity_type, json.dumps(item.model_dump(mode="json")["entity_key"], sort_keys=True)))
        snapshot_id = uuid7()
        row = await dao_snapshots.create(db, commit=False, obj_in={
            "id": snapshot_id, "account_id": account_id, "user_id": context.actor.user_id,
            "device_id": context.actor.device_id, "contract_version": 1, "model_revision": "api-v1.1",
            "appointments_from": start, "appointments_until": end, "window_time_zone": window.time_zone,
            "window_starts_at": window.starts_at, "window_ends_at": window.ends_at,
            "base_sequence": head.last_sequence, "permission_epoch": head.permission_epoch,
            "audience": "owner" if context.owner else "members", "item_count": len(items),
            "created_at": now, "expires_at": now + timedelta(minutes=15),
        })
        for ordinal, item in enumerate(items, 1):
            value = item.model_dump(mode="json", by_alias=True)
            await dao_snapshot_items.record(db, commit=False, values={
                "snapshot_id": snapshot_id, "ordinal": ordinal, "entity_type": item.entity_type,
                "entity_key": value["entityKey"], "entity_version": item.entity_version, "state_json": value["state"],
            })
        response = snapshot_response(row)

    return response


async def snapshot_context(
    db: AsyncSession, credential: str | None, account_id: UUID, snapshot_id: UUID,
    *, release: bool = False,
) -> Result[tuple[AccountContext, SyncSnapshot], SnapshotError]:
    """The caller owns authorization locks and the short read/release transaction."""
    scope = await authorized_context(db, credential, account_id)
    if isinstance(scope, Err):
        return scope

    context, head = scope.value
    row = await dao_snapshots.get(db, snapshot_id)
    if row is Empty:
        return Err(AccountObjectNotFound())

    if row.account_id != account_id or row.user_id != context.actor.user_id or row.device_id != context.actor.device_id:
        return Err(AccountObjectNotFound())

    if not release:
        if row.permission_epoch != head.permission_epoch or row.audience != ("owner" if context.owner else "members"):
            return Err(SyncReadError("SNAPSHOT_SCOPE_CHANGED"))
        if row.expires_at <= await dao_heads.get_server_time(db):
            return Err(SyncReadError("SNAPSHOT_EXPIRED"))

    return Ok((context, row))


async def get_snapshot(
    db: AsyncSession, credential: str | None, account_id: UUID, snapshot_id: UUID,
) -> Result[SnapshotResponse, SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(db, credential, account_id, snapshot_id)
        if isinstance(scope, Err):
            return scope
        response = snapshot_response(scope.value[1])

    return response


async def snapshot_page(
    db: AsyncSession, credential: str | None, account_id: UUID, snapshot_id: UUID, query: PageQuery,
) -> Result[PaginatedResponse[SyncItem], SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(db, credential, account_id, snapshot_id)
        if isinstance(scope, Err):
            return scope

        row = scope.value[1]
        rows = await dao_snapshot_items.page(db, row.id, (query.page - 1) * query.shows, query.shows)
        try:
            response = PaginatedResponse[SyncItem](total=row.item_count, items=[SyncItem.model_validate({
                "entity_type": item.entity_type, "entity_key": item.entity_key,
                "entity_version": item.entity_version, "state": item.state_json,
            }) for item in rows])
        except ValidationError as error:
            raise DAOError("La captura no cumple su esquema") from error

    return Ok(response)


async def release_snapshot(
    db: AsyncSession, credential: str | None, account_id: UUID, snapshot_id: UUID,
) -> Result[None, SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(db, credential, account_id, snapshot_id, release=True)
        if isinstance(scope, Err):
            return scope
        await dao_snapshots.release(db, snapshot_id)

    return Ok(None)
