from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.domain.offers import ServiceOfferQuery
from src.api.services.domain.services import ServiceQuery
from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType, datetime_now

from .models import ProfessionalService, Service, ServiceOfferPrice, ServicePrice


class ServiceDAO(DAO[Service, BaseModel, BaseModel]):
    async def page(
        self, db: AsyncSession, professional_id: UUID, query: ServiceQuery
    ) -> tuple[list[Service], int]:
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

    async def revise(
        self, db: AsyncSession, row: Service, values: dict[str, object]
    ) -> Service:
        return await self.update(
            db,
            row.id,
            {**values, "version": row.version + 1},
            commit=False,
        )


class ProfessionalServiceDAO(DAO[ProfessionalService, BaseModel, BaseModel]):
    async def create_offer(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> ProfessionalService:
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def for_account_service(
        self, db: AsyncSession, account_id: UUID, service_id: UUID
    ) -> ProfessionalService | EmptyType:
        row = await db.scalar(
            select(self.model)
            .where(
                self.model.account_id == account_id,
                self.model.service_id == service_id,
            )
            .order_by(self.model.professional_id)
            .limit(1)
        )

        return Empty if row is None else row

    async def for_service(
        self, db: AsyncSession, professional_id: UUID, service_id: UUID
    ) -> list[ProfessionalService]:
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

    async def page(
        self, db: AsyncSession, account_id: UUID, query: ServiceOfferQuery
    ) -> tuple[Sequence[Row[ProfessionalService, Service]], int]:
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

    async def revise(
        self, db: AsyncSession, row: ProfessionalService, values: dict[str, object]
    ) -> ProfessionalService:
        for name, value in values.items():
            setattr(row, name, value)

        row.version += 1
        await self.flush(db)

        return row


class ServicePriceDAO(DAO[ServicePrice, BaseModel, BaseModel]):
    async def by_service(
        self, db: AsyncSession, professional_id: UUID, service_id: UUID
    ) -> ServicePrice | EmptyType:
        row = await db.scalar(
            select(ServicePrice).where(
                ServicePrice.professional_id == professional_id,
                ServicePrice.service_id == service_id,
            )
        )

        return Empty if row is None else row

    async def of_services(
        self, db: AsyncSession, professional_ids: list[UUID]
    ) -> list[ServicePrice]:
        rows = await db.scalars(
            select(ServicePrice)
            .where(ServicePrice.professional_id.in_(professional_ids))
            .order_by(ServicePrice.professional_id, ServicePrice.service_id)
        )

        return list(rows)

    async def apply_price(
        self,
        db: AsyncSession,
        professional_id: UUID,
        service_id: UUID,
        amount: Decimal,
        currency: str,
    ) -> ServicePrice:
        """Upsert with optimistic version; the caller already checked the version."""
        row = await self.by_service(db, professional_id, service_id)

        if row is Empty:
            # Composite PK: the generic create() expects an `id` column.
            row = ServicePrice(
                professional_id=professional_id,
                service_id=service_id,
                amount=amount,
                currency=currency,
            )
            db.add(row)
            await self.flush(db)

            return row

        row.amount = amount
        row.currency = currency
        row.version += 1
        row.updated_at = datetime_now()
        await self.flush(db)

        return row


class ServiceOfferPriceDAO(DAO[ServiceOfferPrice, BaseModel, BaseModel]):
    async def by_offer(
        self,
        db: AsyncSession,
        account_id: UUID,
        professional_id: UUID,
        service_id: UUID,
    ) -> ServiceOfferPrice | EmptyType:
        row = await db.scalar(
            select(ServiceOfferPrice).where(
                ServiceOfferPrice.account_id == account_id,
                ServiceOfferPrice.professional_id == professional_id,
                ServiceOfferPrice.service_id == service_id,
            )
        )

        return Empty if row is None else row

    async def of_account(
        self, db: AsyncSession, account_id: UUID
    ) -> list[ServiceOfferPrice]:
        rows = await db.scalars(
            select(ServiceOfferPrice)
            .where(ServiceOfferPrice.account_id == account_id)
            .order_by(ServiceOfferPrice.professional_id, ServiceOfferPrice.service_id)
        )

        return list(rows)

    async def apply_price(
        self,
        db: AsyncSession,
        account_id: UUID,
        professional_id: UUID,
        service_id: UUID,
        amount: Decimal,
        currency: str,
    ) -> ServiceOfferPrice:
        row = await self.by_offer(db, account_id, professional_id, service_id)

        if row is Empty:
            row = ServiceOfferPrice(
                account_id=account_id,
                professional_id=professional_id,
                service_id=service_id,
                amount=amount,
                currency=currency,
            )
            db.add(row)
            await self.flush(db)

            return row

        row.amount = amount
        row.currency = currency
        row.version += 1
        row.updated_at = datetime_now()
        await self.flush(db)

        return row

    async def remove_price(
        self,
        db: AsyncSession,
        account_id: UUID,
        professional_id: UUID,
        service_id: UUID,
    ) -> ServiceOfferPrice | EmptyType:
        """Removing the override returns resolution to the base price (D25)."""
        row = await self.by_offer(db, account_id, professional_id, service_id)

        if row is Empty:
            return Empty

        await db.delete(row)
        await self.flush(db)

        return row


dao_services = ServiceDAO(Service)
dao_offers = ProfessionalServiceDAO(ProfessionalService)
dao_service_prices = ServicePriceDAO(ServicePrice)
dao_offer_prices = ServiceOfferPriceDAO(ServiceOfferPrice)
