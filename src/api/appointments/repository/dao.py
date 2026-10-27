from datetime import datetime
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.appointments.domain.appointments import (
    AppointmentHistoryQuery,
    AppointmentQuery,
)
from src.core.db import DAO
from src.core.db.dao import catch_sqlalchemy_exception
from src.core.schema import BaseModel

from .models import Appointment, AppointmentHistory


class AppointmentDAO(DAO[Appointment, BaseModel, BaseModel]):
    async def server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def revise(
        self,
        db: AsyncSession,
        row: Appointment,
        values: dict[str, object],
        now: datetime,
    ) -> Appointment:
        return await self.update(
            db,
            row.id,
            {**values, "version": row.version + 1, "updated_at": now},
            commit=False,
        )

    async def has_live_overlap(
        self,
        db: AsyncSession,
        professional_id: UUID,
        start: datetime,
        end: datetime,
        account_id: UUID | None,
    ) -> bool:
        statement = select(self.model.id).where(
            self.model.professional_id == professional_id,
            self.model.status.in_(("scheduled", "confirmed")),
            self.model.starts_at < end,
            start < self.model.ends_at,
        )

        if account_id is not None:
            statement = statement.where(self.model.account_id == account_id)

        return await db.scalar(statement.limit(1)) is not None

    async def occupancy(
        self,
        db: AsyncSession,
        professional_id: UUID,
        start: datetime,
        end: datetime,
        excluding: UUID | None = None,
    ) -> list[Appointment]:
        statement = select(self.model).where(
            self.model.professional_id == professional_id,
            self.model.status != "cancelled",
            self.model.starts_at < end,
            start < self.model.ends_at,
        )

        if excluding is not None:
            statement = statement.where(self.model.id != excluding)

        return list(
            (
                await db.scalars(statement.execution_options(populate_existing=True))
            ).all()
        )

    async def commitments(
        self, db: AsyncSession, account_id: UUID
    ) -> list[Appointment]:
        statement = select(self.model).where(
            self.model.status.in_(("scheduled", "confirmed")),
            self.model.account_id == account_id,
        )

        return list(
            (
                await db.scalars(
                    statement.order_by(self.model.id).execution_options(
                        populate_existing=True
                    )
                )
            ).all()
        )

    async def page(
        self, db: AsyncSession, account_id: UUID, query: AppointmentQuery
    ) -> tuple[list[Appointment], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id,
            self.model.starts_at < query.until,
            query.from_ < self.model.ends_at,
        )

        for name in ("professional_id", "service_id", "patient_id", "status"):
            value = getattr(query, name)

            if value is not None:
                statement = statement.where(getattr(self.model, name) == value)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.starts_at, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows.all()), total


class AppointmentHistoryDAO(DAO[AppointmentHistory, BaseModel, BaseModel]):
    async def append(
        self, db: AsyncSession, values: dict[str, object]
    ) -> AppointmentHistory:
        with catch_sqlalchemy_exception():
            return (
                await db.scalars(
                    insert(self.model).values(**values).returning(self.model)
                )
            ).one()

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        appointment_id: UUID,
        query: AppointmentHistoryQuery,
    ) -> tuple[list[AppointmentHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id,
            self.model.appointment_id == appointment_id,
        )

        if query.after_version is not None:
            statement = statement.where(self.model.version > query.after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows.all()), total


dao_appointments = AppointmentDAO(Appointment)
dao_histories = AppointmentHistoryDAO(AppointmentHistory)
