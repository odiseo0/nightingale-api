from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from anyio import fail_after

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.sync.application.download_cases import position_for_scope
from src.api.sync.application.operations_cases import authorized_context
from src.api.sync.domain.errors import SyncReadError
from src.api.sync.domain.events import (
    ChangesAvailable,
    EventConnection,
    EventStatus,
    Heartbeat,
    StreamEvent,
)
from src.api.sync.repository.dao import dao_heads, dao_streams
from src.core import Err, Ok, Result
from src.core.db import DAOError, session, transaction
from src.core.services.pg_notifications import NotificationSlot, notifications
from src.core.services.sync_signatures import sign_position
from src.settings.api_settings import api_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

type EventError = (
    InvalidCredential
    | AccessDenied
    | AccountNotFound
    | AccountObjectNotFound
    | SyncReadError
)


async def open_events(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    cursor: str,
) -> Result[tuple[EventConnection, NotificationSlot], EventError]:
    if not notifications.ready:
        return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

    # Subscribe before reading the journal. LISTEN must already be confirmed;
    # a commit during this short transaction then leaves a pending hint.
    slot = notifications.subscribe(str(account_id))
    opened = False

    try:
        async with transaction(db):
            scope = await authorized_context(db, credential, account_id)

            if isinstance(scope, Err):
                return scope

            context, head = scope.value
            secret = api_settings.sync_signing_key

            if secret is None or not notifications.ready:
                return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

            now = await dao_heads.get_server_time(db)
            checked = position_for_scope(
                context, head, cursor, secret.get_secret_value().encode(), now
            )

            if isinstance(checked, Err):
                return checked

            lease_id = await dao_streams.acquire(
                db, account_id, context.actor.user_id, context.actor.device_id, now
            )

            if lease_id is None:
                return Err(SyncReadError("CONNECTION_LIMIT"))

            connection = EventConnection(lease_id, checked.value)

        opened = True

        return Ok((connection, slot))
    finally:
        if not opened:
            notifications.unsubscribe(str(account_id), slot)


async def event_status(
    db: AsyncSession,
    credential: str | None,
    connection: EventConnection,
) -> Result[EventStatus, EventError]:
    position = connection.position

    async with transaction(db):
        scope = await authorized_context(db, credential, position.account_id)

        if isinstance(scope, Err):
            return scope

        context, head = scope.value

        if (
            position.user_id != context.actor.user_id
            or position.device_id != context.actor.device_id
            or position.permission_epoch != head.permission_epoch
            or position.audience != ("owner" if context.owner else "members")
        ):
            return Err(AccessDenied())

        secret = api_settings.sync_signing_key

        if secret is None:
            return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

        now = await dao_heads.get_server_time(db)

        if (
            position.expires_at <= now
            or position.sequence < head.retained_from_sequence - 1
        ):
            return Err(SyncReadError("CURSOR_EXPIRED"))

        if not await dao_streams.renew(db, connection.lease_id, now):
            return Err(SyncReadError("STREAM_EXPIRED"))

        # This is a download hint, never an acknowledgment. Keep the supplied
        # applied sequence even when a newer head caused the notification.
        hint = position.model_copy(
            update={"issued_at": now, "expires_at": now + timedelta(days=90)}
        )
        cursor = sign_position(
            hint.model_dump_json(by_alias=True).encode(),
            secret.get_secret_value().encode(),
        )
        status = EventStatus(
            sequence=head.last_sequence, cursor=cursor, server_time=now
        )

    return Ok(status)


async def stream_events(
    credential: str | None,
    connection: EventConnection,
    slot: NotificationSlot,
) -> AsyncGenerator[StreamEvent, None]:
    last_sequence = connection.position.sequence
    loop = asyncio.get_running_loop()
    heartbeat_at = loop.time()

    while not slot.overloaded:
        try:
            with fail_after(3, shield=True):
                async with session() as db:
                    checked = await event_status(db, credential, connection)
        except DAOError, OSError, TimeoutError:
            return

        if isinstance(checked, Err):
            if not isinstance(checked.error, SyncReadError):
                yield StreamEvent(event="access_revoked")

            return

        status = checked.value

        if slot.overloaded:
            return

        if loop.time() >= heartbeat_at:
            yield StreamEvent(
                event="heartbeat", data=Heartbeat(server_time=status.server_time)
            )
            heartbeat_at = loop.time() + 15
            # Reauthorize at the top before sending another event. A burst of
            # hints must not defer the timed access check or heartbeat.
            continue

        if status.sequence != last_sequence:
            yield StreamEvent(
                event="changes_available",
                event_id=str(status.sequence),
                data=ChangesAvailable(
                    account_id=connection.position.account_id, cursor=status.cursor
                ),
            )
            last_sequence = status.sequence

            continue
        try:
            async with asyncio.timeout(max(0, heartbeat_at - loop.time())):
                await slot.pending.get()
        except TimeoutError:
            pass


async def close_events(connection: EventConnection, slot: NotificationSlot) -> None:
    notifications.unsubscribe(str(connection.position.account_id), slot)

    try:
        async with session() as db:
            async with transaction(db):
                await dao_streams.release(db, connection.lease_id)
    except DAOError, OSError, TimeoutError:
        # A failed release does not grant a slot forever: leases expire in 45 s.
        pass
