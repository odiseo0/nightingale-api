from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Never
from uuid import UUID

from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.domain.errors import AccessDenied
from src.api.sync.repository.dao import (
    dao_changes,
    dao_heads,
    dao_receipts,
    dao_snapshots,
    dao_streams,
)
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def create_head(
    db: AsyncSession, account_id: UUID, now: datetime
) -> Result[None, Never]:
    """The account use case owns the transaction for the complete practice."""
    await dao_heads.create_head(db, account_id, now, commit=False)

    return Ok(None)


async def get_permission_epoch(
    db: AsyncSession, account_id: UUID
) -> Result[int, Never]:
    head = await dao_heads.get_for_account(db, account_id)

    if head is Empty:
        raise DAOError("La cuenta no tiene control de sincronización")

    return Ok(head.permission_epoch)


async def purge_expired_results(db: AsyncSession) -> Result[int, AccessDenied]:
    from uuid import uuid7

    async with transaction(db):
        if not await dao_receipts.can_purge(db):
            return Err(AccessDenied())

        await dao_changes.purge_expired(db)
        count = await dao_receipts.purge_expired(db)
        await dao_snapshots.purge_expired(db)
        await dao_streams.purge_expired(db)
        now = await dao_heads.get_server_time(db)
        await record_control(
            db,
            ControlAudit(
                operator_ref="administrative-purge-results",
                action="PurgeExpiredResults",
                object_type="result",
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=now,
            ),
        )

    return Ok(count)
