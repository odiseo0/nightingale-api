from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import EmptyType

from src.api.clinical_records.domain.allergies import AllergyQuery
from src.api.clinical_records.domain.conditions import ConditionQuery

from .allergies import PatientAllergyIntolerance, PatientAllergyIntoleranceHistory
from .conditions import (
    PatientClinicalSectionReview,
    PatientClinicalSectionReviewHistory,
    PatientCondition,
    PatientConditionHistory,
)
from .models import PatientClinicalProfile, PatientClinicalProfileHistory


class PatientClinicalProfileDAO(DAO[PatientClinicalProfile, BaseModel, BaseModel]):
    async def scoped(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> PatientClinicalProfile | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id, "patient_id": patient_id},
            execution_options={"populate_existing": True},
        )


class PatientClinicalProfileHistoryDAO(
    DAO[PatientClinicalProfileHistory, BaseModel, BaseModel]
):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientClinicalProfileHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


dao_clinical_profiles = PatientClinicalProfileDAO(PatientClinicalProfile)
dao_clinical_profile_histories = PatientClinicalProfileHistoryDAO(
    PatientClinicalProfileHistory
)


class PatientConditionDAO(DAO[PatientCondition, BaseModel, BaseModel]):
    async def scoped(self, db: AsyncSession, account_id: UUID, condition_id: UUID) -> PatientCondition | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id, "id": condition_id},
            execution_options={"populate_existing": True},
        )

    async def revise(
        self,
        db: AsyncSession,
        row: PatientCondition,
        changes: dict[str, object],
        now: datetime,
    ) -> PatientCondition:
        for name, value in changes.items():
            setattr(row, name, value)

        row.version += 1
        row.updated_at = now
        await self.flush(db)
        return row

    async def page(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, query: ConditionQuery
    ) -> tuple[list[PatientCondition], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )
        if query.clinical_status is not None:
            statement = statement.where(self.model.clinical_status == query.clinical_status)
        if query.verification_status is not None:
            statement = statement.where(self.model.verification_status == query.verification_status)
        if not query.include_entered_in_error and query.verification_status != "entered-in-error":
            statement = statement.where(self.model.verification_status != "entered-in-error")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id).offset((query.page - 1) * query.shows).limit(query.shows)
        )
        return list(rows), total

    async def has_pertinent(self, db: AsyncSession, account_id: UUID, patient_id: UUID) -> bool:
        return await db.scalar(
            select(
                select(self.model.id)
                .where(
                    self.model.account_id == account_id,
                    self.model.patient_id == patient_id,
                    self.model.verification_status.not_in(("refuted", "entered-in-error")),
                )
                .exists()
            )
        )

    async def active_count(self, db: AsyncSession, account_id: UUID, patient_id: UUID) -> int:
        return await db.scalar(
            select(func.count()).select_from(self.model).where(
                self.model.account_id == account_id,
                self.model.patient_id == patient_id,
                self.model.clinical_status.in_(("active", "recurrence", "relapse")),
                self.model.verification_status.not_in(("refuted", "entered-in-error")),
            )
        ) or 0


class PatientConditionHistoryDAO(DAO[PatientConditionHistory, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        condition_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientConditionHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == condition_id
        )
        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )
        return list(rows), total


class PatientClinicalSectionReviewDAO(DAO[PatientClinicalSectionReview, BaseModel, BaseModel]):
    async def scoped(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, section: str
    ) -> PatientClinicalSectionReview | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id, "patient_id": patient_id, "section": section},
            execution_options={"populate_existing": True},
        )


class PatientClinicalSectionReviewHistoryDAO(
    DAO[PatientClinicalSectionReviewHistory, BaseModel, BaseModel]
):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        section: str,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientClinicalSectionReviewHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id,
            self.model.patient_id == patient_id,
            self.model.section == section,
        )
        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )
        return list(rows), total


dao_conditions = PatientConditionDAO(PatientCondition)
dao_condition_histories = PatientConditionHistoryDAO(PatientConditionHistory)
dao_section_reviews = PatientClinicalSectionReviewDAO(PatientClinicalSectionReview)
dao_section_review_histories = PatientClinicalSectionReviewHistoryDAO(
    PatientClinicalSectionReviewHistory
)


class PatientAllergyIntoleranceDAO(DAO[PatientAllergyIntolerance, BaseModel, BaseModel]):
    async def scoped(self, db: AsyncSession, account_id: UUID, allergy_id: UUID) -> PatientAllergyIntolerance | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id, "id": allergy_id},
            execution_options={"populate_existing": True},
        )

    async def revise(
        self,
        db: AsyncSession,
        row: PatientAllergyIntolerance,
        changes: dict[str, object],
        now: datetime,
    ) -> PatientAllergyIntolerance:
        for name, value in changes.items():
            setattr(row, name, value)

        row.version += 1
        row.updated_at = now
        await self.flush(db)
        return row

    async def page(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, query: AllergyQuery
    ) -> tuple[list[PatientAllergyIntolerance], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )
        if query.clinical_status is not None:
            statement = statement.where(self.model.clinical_status == query.clinical_status)
        if query.verification_status is not None:
            statement = statement.where(self.model.verification_status == query.verification_status)
        if query.type is not None:
            statement = statement.where(self.model.type == query.type)
        if not query.include_entered_in_error and query.verification_status != "entered-in-error":
            statement = statement.where(self.model.verification_status != "entered-in-error")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id).offset((query.page - 1) * query.shows).limit(query.shows)
        )
        return list(rows), total

    async def has_pertinent(self, db: AsyncSession, account_id: UUID, patient_id: UUID) -> bool:
        return await db.scalar(
            select(
                select(self.model.id)
                .where(
                    self.model.account_id == account_id,
                    self.model.patient_id == patient_id,
                    self.model.verification_status.not_in(("refuted", "entered-in-error")),
                )
                .exists()
            )
        )

    async def active_count(self, db: AsyncSession, account_id: UUID, patient_id: UUID) -> int:
        return await db.scalar(
            select(func.count()).select_from(self.model).where(
                self.model.account_id == account_id,
                self.model.patient_id == patient_id,
                self.model.clinical_status == "active",
                self.model.verification_status.not_in(("refuted", "entered-in-error")),
            )
        ) or 0


class PatientAllergyIntoleranceHistoryDAO(DAO[PatientAllergyIntoleranceHistory, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        allergy_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientAllergyIntoleranceHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == allergy_id
        )
        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )
        return list(rows), total


dao_allergies = PatientAllergyIntoleranceDAO(PatientAllergyIntolerance)
dao_allergy_histories = PatientAllergyIntoleranceHistoryDAO(PatientAllergyIntoleranceHistory)
