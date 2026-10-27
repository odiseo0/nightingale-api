from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.domain.offers import ServiceOfferQuery
from src.api.services.domain.services import ServiceQuery
from src.core.db import DAO
from src.core.schema import BaseModel

from .models import ProfessionalService, Service


class ServiceDAO(DAO[Service, BaseModel, BaseModel]):
    async def server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def page(self, db: AsyncSession, professional_id: UUID, query: ServiceQuery) -> tuple[list[Service], int]:
        statement = select(self.model).where(
            self.model.professional_id == professional_id
        )

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        if query.q is not None:
            statement = statement.where(
                self.model.name.icontains(query.q, autoescape=True)
            )

        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.id)
                .offset((query.page - 1) * query.shows)
                .limit(query.shows)
            )
        ).all()

        return list(rows), total

    async def revise(self, db: AsyncSession, row: Service, values: dict[str, object], now: datetime) -> Service:
        return await self.update(
            db,
            row.id,
            {
                **values,
                "version": row.version + 1,
                "updated_at": now,
            },
            commit=False,
        )


class ProfessionalServiceDAO(DAO[ProfessionalService, BaseModel, BaseModel]):
    async def create_offer(self, db: AsyncSession, values: dict[str, object], *, commit: bool = True) -> ProfessionalService:
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def for_service(self, db: AsyncSession, professional_id: UUID, service_id: UUID) -> list[ProfessionalService]:
        statement = (
            select(self.model)
            .where(
                self.model.professional_id == professional_id,
                self.model.service_id == service_id,
            )
            .order_by(self.model.account_id)
            .execution_options(populate_existing=True)
        )

        return list((await db.scalars(statement)).all())

    async def page(self, db: AsyncSession, account_id: UUID, query: ServiceOfferQuery) -> tuple[Sequence[Row[ProfessionalService, Service]], int]:
        statement = (
            select(self.model, Service)
            .join(Service, Service.id == self.model.service_id)
            .where(self.model.account_id == account_id)
        )

        if query.professional_id is not None:
            statement = statement.where(
                self.model.professional_id == query.professional_id
            )

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        if query.q is not None:
            statement = statement.where(
                Service.name.icontains(query.q, autoescape=True)
            )

        total = await self.count(db, statement)
        rows = (
            await db.execute(
                statement.order_by(self.model.professional_id, self.model.service_id)
                .offset((query.page - 1) * query.shows)
                .limit(query.shows)
            )
        ).all()

        return rows, total

    async def revise(self, db: AsyncSession, row: ProfessionalService, values: dict[str, object], now: datetime) -> ProfessionalService:
        for name, value in values.items():
            setattr(row, name, value)

        row.version += 1
        row.updated_at = now
        await self.flush(db)

        return row


dao_services = ServiceDAO(Service)
dao_offers = ProfessionalServiceDAO(ProfessionalService)
