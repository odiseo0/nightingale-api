from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.medications.domain.medications import DeclaredMedicationQuery
from src.core.db import DAO
from src.core.schema import BaseModel

from .models import DeclaredMedication, DeclaredMedicationHistory


class DeclaredMedicationDAO(DAO[DeclaredMedication, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: DeclaredMedicationQuery,
    ) -> tuple[list[DeclaredMedication], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.review_status is not None:
            statement = statement.where(
                self.model.review_status == query.review_status
            )

        if query.source_type is not None:
            statement = statement.where(self.model.source_type == query.source_type)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.date_added, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[DeclaredMedication]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


dao_declared_medications = DeclaredMedicationDAO(DeclaredMedication)
dao_declared_medication_histories = DAO(DeclaredMedicationHistory)
