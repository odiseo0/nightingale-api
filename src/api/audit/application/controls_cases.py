from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.accounts_cases import account_context, audit_scope
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import AuditEventResponse, AuditQuery, ControlAudit
from src.api.audit.repository.dao import dao_events
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied
from src.core import Err, Ok
from src.core.db import transaction
from src.core.schema import PaginatedResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_audit_events(db: AsyncSession, credential: str | None, account_id: UUID, query: AuditQuery):
    async with transaction(db):
        identity = await authenticate(db, credential)
        if isinstance(identity, Err):
            return identity
        scope = await account_context(db, identity.value, account_id, require_device=True)
        if isinstance(scope, Err):
            return scope
        if not scope.value.owner or scope.value.account.status != "active":
            return Err(AccessDenied())
        rows, total = await dao_events.page(db, account_id, query)
        response = PaginatedResponse[AuditEventResponse](items=[AuditEventResponse.model_validate(row) for row in rows], total=total)

    return Ok(response)


async def record_http_denial(db: AsyncSession, credential: str | None, account_id: UUID | None, correlation_id: UUID):
    async with transaction(db):
        identity = await authenticate(db, credential)
        actor = identity.value if isinstance(identity, Ok) else None
        known_account = await audit_scope(db, actor.user_id, account_id) if actor is not None and account_id is not None else False
        now = await dao_events.get_server_time(db)
        await record_control(db, ControlAudit(
            account_id=account_id if known_account else None,
            actor_user_id=None if actor is None else actor.user_id,
            actor_device_id=None if actor is None else actor.device_id,
            action="HttpAccessDenied", object_type="api", outcome="rejected",
            correlation_id=correlation_id, occurred_at=now,
        ))
