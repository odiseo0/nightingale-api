from __future__ import annotations

from typing import TYPE_CHECKING, Never
from uuid import uuid7

from src.api.audit.domain.audit import ControlAudit, OperationAudit
from src.api.audit.repository.dao import dao_events
from src.core import Ok, Result

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def record_operation(db: AsyncSession, event: OperationAudit) -> Result[None, Never]:
    """The caller confirms this event with its receipt and effect."""
    await dao_events.create(
        db, commit=False,
        obj_in={"id": uuid7(), "actor_kind": "staff", "operator_ref": None, **event.model_dump()},
    )

    return Ok(None)


async def record_control(db: AsyncSession, event: ControlAudit) -> Result[None, Never]:
    kind = "operator" if event.operator_ref is not None else "staff" if event.actor_user_id is not None else "anonymous"
    await dao_events.create(db, commit=False, obj_in={
        "id": uuid7(), "actor_kind": kind, "operation_id": None, **event.model_dump(),
    })

    return Ok(None)
