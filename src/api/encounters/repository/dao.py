from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.encounters.domain.encounters import EncounterQuery
from src.api.encounters.repository.models import (
    ClinicalEncounter,
    ClinicalEncounterHistory,
)
from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType


class ClinicalEncounterDAO(DAO[ClinicalEncounter, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: EncounterQuery,
    ) -> tuple[list[ClinicalEncounter], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        if query.from_ is not None:
            statement = statement.where(self.model.occurred_at >= query.from_)

        if query.until is not None:
            statement = statement.where(self.model.occurred_at < query.until)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.occurred_at, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[ClinicalEncounter]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)

    async def latest_valid(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> ClinicalEncounter | EmptyType:
        row = await db.scalar(
            select(self.model)
            .where(
                self.model.account_id == account_id,
                self.model.patient_id == patient_id,
                self.model.record_status == "valid",
            )
            .order_by(self.model.occurred_at.desc(), self.model.id.desc())
            .limit(1)
        )

        if row is None:
            return Empty

        return row


dao_encounters = ClinicalEncounterDAO(ClinicalEncounter)
dao_encounter_histories = DAO(ClinicalEncounterHistory)
