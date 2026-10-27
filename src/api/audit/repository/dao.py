from datetime import datetime
from uuid import UUID

from sqlalchemy import bindparam, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.audit.domain.audit import AuditQuery
from src.core.db import DAO
from src.core.schema import BaseModel

from .models import AuditEvent


class AuditEventDAO(DAO[AuditEvent, BaseModel, BaseModel]):
    async def get_server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def page(
        self, db: AsyncSession, account_id: UUID, query: AuditQuery
    ) -> tuple[list[AuditEvent], int]:
        statement = select(self.model).where(self.model.account_id == account_id)

        if query.from_ is not None:
            statement = statement.where(self.model.occurred_at >= query.from_)

        if query.until is not None:
            statement = statement.where(self.model.occurred_at < query.until)

        if query.action is not None:
            statement = statement.where(self.model.action == query.action)

        if query.object_type is not None:
            statement = statement.where(self.model.object_type == query.object_type)

        if query.object_id is not None:
            statement = statement.where(
                self.model.object_key
                == bindparam("object_key_filter", str(query.object_id), type_=JSONB)
            )

        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.occurred_at, self.model.id)
                .offset((query.page - 1) * query.shows)
                .limit(query.shows)
            )
        ).all()

        return list(rows), total


dao_events = AuditEventDAO(AuditEvent)
