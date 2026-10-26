from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Never
from uuid import UUID

from src.api.sync.repository.dao import dao_heads
from src.core import Ok, Result
from src.core.db import DAOError
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def create_head(db: AsyncSession, account_id: UUID, now: datetime) -> Result[None, Never]:
    """The account use case owns the transaction for the complete practice."""
    await dao_heads.create_head(db, account_id, now, commit=False)

    return Ok(None)


async def get_permission_epoch(db: AsyncSession, account_id: UUID) -> Result[int, Never]:
    head = await dao_heads.get_for_account(db, account_id)
    if head is Empty:
        raise DAOError("La cuenta no tiene control de sincronización")

    return Ok(head.permission_epoch)
