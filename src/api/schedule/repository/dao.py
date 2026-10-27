from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schedule.domain.schedule import ScheduleRuleQuery
from src.core.db import DAO
from src.core.schema import BaseModel

from .models import ScheduleRule


class ScheduleRuleDAO(DAO[ScheduleRule, BaseModel, BaseModel]):
    async def server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def local_date(self, db: AsyncSession, time_zone: str, instant: datetime) -> date:
        return (await db.execute(
            text("SELECT CAST(timezone(:zone,CAST(:instant AS timestamptz)) AS date)"),
            {"zone": time_zone, "instant": instant},
        )).scalar_one()

    async def for_professional(self, db: AsyncSession, account_id: UUID, professional_id: UUID) -> list[ScheduleRule]:
        statement = (
            select(self.model)
            .where(
                self.model.account_id == account_id,
                self.model.professional_id == professional_id,
            )
            .order_by(self.model.id)
            .execution_options(populate_existing=True)
        )

        return list((await db.scalars(statement)).all())

    async def duplicate(self, db: AsyncSession, account_id: UUID, professional_id: UUID, values: dict[str, object], excluding: UUID) -> bool:
        statement = select(self.model.id).where(
            self.model.account_id == account_id,
            self.model.professional_id == professional_id,
            self.model.id != excluding,
        )
        for name in (
            "iso_weekday",
            "local_start_minute",
            "local_end_minute",
            "valid_from",
            "valid_until",
        ):
            statement = statement.where(getattr(self.model, name) == values[name])

        return await db.scalar(statement) is not None

    async def page(self, db: AsyncSession, account_id: UUID, query: ScheduleRuleQuery) -> tuple[list[ScheduleRule], int]:
        statement = select(self.model).where(self.model.account_id == account_id)

        if query.professional_id is not None:
            statement = statement.where(
                self.model.professional_id == query.professional_id
            )

        if query.iso_weekday is not None:
            statement = statement.where(self.model.iso_weekday == query.iso_weekday)

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        if query.from_date is not None:
            statement = statement.where(
                or_(
                    self.model.valid_until.is_(None),
                    self.model.valid_until >= query.from_date,
                )
            )

        if query.until_date is not None:
            statement = statement.where(self.model.valid_from <= query.until_date)

        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.id)
                .offset((query.page - 1) * query.shows)
                .limit(query.shows)
            )
        ).all()

        return list(rows), total

    async def revise(self, db: AsyncSession, row: ScheduleRule, values: dict[str, object], now: datetime) -> ScheduleRule:
        return await self.update(
            db,
            row.id,
            {**values, "version": row.version + 1, "updated_at": now},
            commit=False,
        )


dao_rules = ScheduleRuleDAO(ScheduleRule)
