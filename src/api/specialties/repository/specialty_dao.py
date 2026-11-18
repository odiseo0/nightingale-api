from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import (
    DentalFinding,
    DentalFindingHistory,
    DentalTreatment,
    DentalTreatmentHistory,
)


class _Scoped:
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        *,
        lock: bool = False,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row


class _HistoryPage:
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class DentalFindingDAO(_Scoped, DAO[DentalFinding, BaseModel, BaseModel]):
    async def page(self, db, account_id: UUID, patient_id: UUID, query):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.tooth_fdi is not None:
            statement = statement.where(self.model.tooth_fdi == query.tooth_fdi)

        if query.finding_kind is not None:
            statement = statement.where(self.model.finding_kind == query.finding_kind)

        if query.finding_status is not None:
            statement = statement.where(self.model.finding_status == query.finding_status)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.tooth_fdi, self.model.surface, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(self, db, account_id: UUID) -> list[DentalFinding]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class DentalFindingHistoryDAO(
    _HistoryPage, DAO[DentalFindingHistory, BaseModel, BaseModel]
):
    pass


class DentalTreatmentDAO(_Scoped, DAO[DentalTreatment, BaseModel, BaseModel]):
    async def for_finding(self, db, account_id: UUID, finding_id: UUID):
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.finding_id == finding_id,
                self.model.record_status == "valid",
            )
        )

        return list(rows)

    async def valid_snapshot(self, db, account_id: UUID) -> list[DentalTreatment]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class DentalTreatmentHistoryDAO(
    _HistoryPage, DAO[DentalTreatmentHistory, BaseModel, BaseModel]
):
    pass


dao_dental_findings = DentalFindingDAO(DentalFinding)
dao_dental_finding_histories = DentalFindingHistoryDAO(DentalFindingHistory)
dao_dental_treatments = DentalTreatmentDAO(DentalTreatment)
dao_dental_treatment_histories = DentalTreatmentHistoryDAO(DentalTreatmentHistory)
