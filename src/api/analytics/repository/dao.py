from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import AnalyticEtlState, AnalyticMeasurementPoint


class AnalyticPointDAO(DAO[AnalyticMeasurementPoint, BaseModel, BaseModel]):
    async def for_series(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, kind: str
    ) -> list[AnalyticMeasurementPoint]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.patient_id == patient_id,
                self.model.measurement_kind == kind,
            )
        )

        return list(rows)

    async def replace_for_source(
        self, db: AsyncSession, account_id: UUID, source_measurement_id: UUID, point
    ) -> None:
        await db.execute(
            delete(self.model).where(
                self.model.account_id == account_id,
                self.model.source_measurement_id == source_measurement_id,
            )
        )
        await self.add(db, point)

    async def delete_for_source(
        self, db: AsyncSession, account_id: UUID, source_measurement_id: UUID
    ) -> None:
        await db.execute(
            delete(self.model).where(
                self.model.account_id == account_id,
                self.model.source_measurement_id == source_measurement_id,
            )
        )

    async def clear(self, db: AsyncSession) -> None:
        await db.execute(delete(self.model))


class AnalyticEtlStateDAO(DAO[AnalyticEtlState, BaseModel, BaseModel]):
    async def lock(self, db: AsyncSession) -> None:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended('nightingale_analytics_etl',0))")
        )

    async def for_account(
        self, db: AsyncSession, account_id: UUID
    ) -> AnalyticEtlState | EmptyType:
        row = await db.scalar(
            select(self.model).where(self.model.account_id == account_id)
        )

        return Empty if row is None else row

    async def advance(self, db: AsyncSession, account_id: UUID, seq: int) -> None:
        row = await self.for_account(db, account_id)

        if row is Empty:
            await self.add(
                db,
                AnalyticEtlState(account_id=account_id, last_change_seq=seq),
            )
        else:
            row.last_change_seq = seq
            await self.flush(db)


dao_analytic_points = AnalyticPointDAO(AnalyticMeasurementPoint)
dao_analytic_etl_state = AnalyticEtlStateDAO(AnalyticEtlState)
