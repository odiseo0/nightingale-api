from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.clinical_records.domain.allergies import (
    AllergyQuery,
    PatientAllergyIntoleranceResponse,
)
from src.api.clinical_records.domain.antecedents import (
    AntecedentQuery,
    PatientAntecedentResponse,
)
from src.api.clinical_records.domain.conditions import (
    ConditionQuery,
    PatientConditionResponse,
)
from src.api.clinical_records.domain.history import ClinicalHistoryQuery
from src.api.clinical_records.domain.immunizations import (
    ImmunizationQuery,
    PatientImmunizationResponse,
)
from src.api.clinical_records.domain.measurements import (
    MeasurementQuery,
    PatientMeasurementResponse,
)
from src.api.clinical_records.domain.notes import NoteQuery, PatientNoteResponse
from src.api.encounters.domain.encounters import PatientEncounterResponse
from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .allergies import PatientAllergyIntolerance, PatientAllergyIntoleranceHistory
from .conditions import (
    PatientClinicalSectionReview,
    PatientClinicalSectionReviewHistory,
    PatientCondition,
    PatientConditionHistory,
)
from .models import (
    PatientAntecedent,
    PatientAntecedentHistory,
    PatientClinicalProfile,
    PatientClinicalProfileHistory,
    PatientClinicalTimeline,
    PatientImmunization,
    PatientImmunizationHistory,
    PatientMeasurement,
    PatientMeasurementHistory,
    PatientNote,
    PatientNoteHistory,
)


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


class ClinicalEntryDAO[Entry: PatientCondition | PatientAllergyIntolerance](
    DAO[Entry, BaseModel, BaseModel]
):
    async def scoped(
        self, db: AsyncSession, account_id: UUID, entry_id: UUID
    ) -> Entry | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id, "id": entry_id},
            execution_options={"populate_existing": True},
        )

    async def revise(
        self, db: AsyncSession, row: Entry, changes: dict[str, object], now: datetime
    ) -> Entry:
        for name, value in changes.items():
            setattr(row, name, value)

        row.version += 1
        row.updated_at = now
        await self.flush(db)

        return row

    async def has_pertinent(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> bool:
        return await db.scalar(
            select(
                select(self.model.id)
                .where(
                    self.model.account_id == account_id,
                    self.model.patient_id == patient_id,
                    self.model.verification_status.not_in(
                        ("refuted", "entered-in-error")
                    ),
                )
                .exists()
            )
        )


class ClinicalHistoryDAO[
    Entry: PatientConditionHistory | PatientAllergyIntoleranceHistory
](DAO[Entry, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        entry_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[Entry], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entry_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class PatientConditionDAO(ClinicalEntryDAO[PatientCondition]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: ConditionQuery,
    ) -> tuple[list[PatientCondition], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.clinical_status is not None:
            statement = statement.where(
                self.model.clinical_status == query.clinical_status
            )

        if query.verification_status is not None:
            statement = statement.where(
                self.model.verification_status == query.verification_status
            )

        if (
            not query.include_entered_in_error
            and query.verification_status != "entered-in-error"
        ):
            statement = statement.where(
                self.model.verification_status != "entered-in-error"
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )
        return list(rows), total

    async def active_count(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> int:
        return (
            await db.scalar(
                select(func.count())
                .select_from(self.model)
                .where(
                    self.model.account_id == account_id,
                    self.model.patient_id == patient_id,
                    self.model.clinical_status.in_(("active", "recurrence", "relapse")),
                    self.model.verification_status.not_in(
                        ("refuted", "entered-in-error")
                    ),
                )
            )
            or 0
        )


class PatientConditionHistoryDAO(ClinicalHistoryDAO[PatientConditionHistory]):
    pass


class PatientClinicalSectionReviewDAO(
    DAO[PatientClinicalSectionReview, BaseModel, BaseModel]
):
    async def scoped(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, section: str
    ) -> PatientClinicalSectionReview | EmptyType:
        return await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": patient_id,
                "section": section,
            },
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


class PatientAllergyIntoleranceDAO(ClinicalEntryDAO[PatientAllergyIntolerance]):
    async def page(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, query: AllergyQuery
    ) -> tuple[list[PatientAllergyIntolerance], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.clinical_status is not None:
            statement = statement.where(
                self.model.clinical_status == query.clinical_status
            )

        if query.verification_status is not None:
            statement = statement.where(
                self.model.verification_status == query.verification_status
            )

        if query.type is not None:
            statement = statement.where(self.model.type == query.type)

        if (
            not query.include_entered_in_error
            and query.verification_status != "entered-in-error"
        ):
            statement = statement.where(
                self.model.verification_status != "entered-in-error"
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )
        return list(rows), total

    async def active_count(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> int:
        return (
            await db.scalar(
                select(func.count())
                .select_from(self.model)
                .where(
                    self.model.account_id == account_id,
                    self.model.patient_id == patient_id,
                    self.model.clinical_status == "active",
                    self.model.verification_status.not_in(
                        ("refuted", "entered-in-error")
                    ),
                )
            )
            or 0
        )


class PatientAllergyIntoleranceHistoryDAO(
    ClinicalHistoryDAO[PatientAllergyIntoleranceHistory]
):
    pass


class PatientNoteDAO(DAO[PatientNote, BaseModel, BaseModel]):
    async def scoped(
        self, db: AsyncSession, account_id: UUID, note_id: UUID, *, lock: bool = False
    ) -> PatientNote | EmptyType:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == note_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row

    async def page(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, query: NoteQuery
    ) -> tuple[list[PatientNote], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        if query.encounter_id is not None:
            statement = statement.where(self.model.encounter_id == query.encounter_id)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.created_at, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[PatientNote]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class PatientNoteHistoryDAO(DAO[PatientNoteHistory, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        note_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientNoteHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == note_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class PatientMeasurementDAO(DAO[PatientMeasurement, BaseModel, BaseModel]):
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        measurement_id: UUID,
        *,
        lock: bool = False,
    ) -> PatientMeasurement | EmptyType:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == measurement_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: MeasurementQuery,
    ) -> tuple[list[PatientMeasurement], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.kind is not None:
            statement = statement.where(self.model.kind == query.kind)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        if query.from_ is not None:
            statement = statement.where(self.model.measured_at >= query.from_)

        if query.until is not None:
            statement = statement.where(self.model.measured_at < query.until)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.measured_at, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[PatientMeasurement]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)

    async def latest_by_kind(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> list[PatientMeasurement]:
        rows = await db.scalars(
            select(self.model)
            .where(
                self.model.account_id == account_id,
                self.model.patient_id == patient_id,
                self.model.record_status == "valid",
            )
            .order_by(
                self.model.kind, self.model.measured_at.desc(), self.model.id.desc()
            )
        )
        latest = {}

        for row in rows:
            latest.setdefault(row.kind, row)

        return list(latest.values())


class PatientMeasurementHistoryDAO(
    DAO[PatientMeasurementHistory, BaseModel, BaseModel]
):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        measurement_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientMeasurementHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == measurement_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class PatientImmunizationDAO(DAO[PatientImmunization, BaseModel, BaseModel]):
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        immunization_id: UUID,
        *,
        lock: bool = False,
    ) -> PatientImmunization | EmptyType:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == immunization_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: ImmunizationQuery,
    ) -> tuple[list[PatientImmunization], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.record_kind is not None:
            statement = statement.where(self.model.record_kind == query.record_kind)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.occurrence_date, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[PatientImmunization]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class PatientImmunizationHistoryDAO(
    DAO[PatientImmunizationHistory, BaseModel, BaseModel]
):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        immunization_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientImmunizationHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == immunization_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class PatientAntecedentDAO(DAO[PatientAntecedent, BaseModel, BaseModel]):
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        antecedent_id: UUID,
        *,
        lock: bool = False,
    ) -> PatientAntecedent | EmptyType:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == antecedent_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query: AntecedentQuery,
    ) -> tuple[list[PatientAntecedent], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.category is not None:
            statement = statement.where(self.model.category == query.category)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.created_at, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[PatientAntecedent]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class PatientAntecedentHistoryDAO(DAO[PatientAntecedentHistory, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        antecedent_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ) -> tuple[list[PatientAntecedentHistory], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == antecedent_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class PatientClinicalTimelineDAO(DAO[PatientClinicalTimeline, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        sections: list[str],
        query: ClinicalHistoryQuery,
    ) -> tuple[list[PatientClinicalTimeline], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id,
            self.model.patient_id == patient_id,
            self.model.source_section.in_(sections),
        )

        if query.entry_types is not None:
            statement = statement.where(self.model.entry_type.in_(query.entry_types))

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        if query.from_ is not None:
            statement = statement.where(
                (self.model.occurred_at >= query.from_)
                | (self.model.occurrence_date >= query.from_.date().isoformat())
            )

        if query.until is not None:
            statement = statement.where(
                (self.model.occurred_at < query.until)
                | (self.model.occurrence_date < query.until.date().isoformat())
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(
                self.model.sort_key, self.model.entry_type, self.model.entry_id
            )
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def project_entry(
        self,
        db: AsyncSession,
        account_id: UUID,
        entry: PatientConditionResponse | PatientAllergyIntoleranceResponse,
    ) -> PatientClinicalTimeline:
        condition = isinstance(entry, PatientConditionResponse)
        entry_type = "condition" if condition else "allergy_intolerance"
        entry_id = entry.condition_id if condition else entry.allergy_id
        day = entry.onset_date
        precision = (
            "reference" if day is None else {4: "year", 7: "month", 10: "day"}[len(day)]
        )
        status = (
            "entered-in-error"
            if entry.verification_status == "entered-in-error"
            else "valid"
        )
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": entry.patient_id,
                "entry_type": entry_type,
                "entry_id": entry_id,
            },
            execution_options={"populate_existing": True},
        )
        values = {
            "occurred_at": entry.updated_at if day is None else None,
            "occurrence_date": day,
            "date_precision": precision,
            "sort_key": day or entry.updated_at.isoformat(),
            "accepted_at": entry.updated_at,
            "entity_version": entry.version,
            "record_status": status,
        }

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=entry.patient_id,
                entry_type=entry_type,
                entry_id=entry_id,
                source_section="conditions" if condition else "allergies",
                **values,
            )
            await self.add(db, row)
        else:
            for name, value in values.items():
                setattr(row, name, value)

            await self.flush(db)

        return row

    async def project_antecedent(
        self, db: AsyncSession, account_id: UUID, antecedent: PatientAntecedentResponse
    ) -> PatientClinicalTimeline:
        day = antecedent.occurrence_date
        precision = (
            "reference" if day is None else {4: "year", 7: "month", 10: "day"}[len(day)]
        )
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": antecedent.patient_id,
                "entry_type": "antecedent",
                "entry_id": antecedent.antecedent_id,
            },
            execution_options={"populate_existing": True},
        )
        values = {
            "occurred_at": antecedent.created_at if day is None else None,
            "occurrence_date": day,
            "date_precision": precision,
            "sort_key": day or antecedent.created_at.isoformat(),
            "accepted_at": antecedent.updated_at,
            "entity_version": antecedent.version,
            "record_status": antecedent.record_status,
        }

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=antecedent.patient_id,
                entry_type="antecedent",
                entry_id=antecedent.antecedent_id,
                source_section="antecedents",
                **values,
            )
            await self.add(db, row)
        else:
            for name, value in values.items():
                setattr(row, name, value)

            await self.flush(db)

        return row

    async def project_immunization(
        self,
        db: AsyncSession,
        account_id: UUID,
        immunization: PatientImmunizationResponse,
    ) -> PatientClinicalTimeline:
        precision = {4: "year", 7: "month", 10: "day"}[
            len(immunization.occurrence_date)
        ]
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": immunization.patient_id,
                "entry_type": "immunization",
                "entry_id": immunization.immunization_id,
            },
            execution_options={"populate_existing": True},
        )
        values = {
            "occurred_at": None,
            "occurrence_date": immunization.occurrence_date,
            "date_precision": precision,
            "sort_key": immunization.occurrence_date,
            "accepted_at": immunization.updated_at,
            "entity_version": immunization.version,
            "record_status": immunization.record_status,
        }

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=immunization.patient_id,
                entry_type="immunization",
                entry_id=immunization.immunization_id,
                source_section="immunizations",
                **values,
            )
            await self.add(db, row)
        else:
            for name, value in values.items():
                setattr(row, name, value)

            await self.flush(db)

        return row

    async def project_measurement(
        self,
        db: AsyncSession,
        account_id: UUID,
        measurement: PatientMeasurementResponse,
    ) -> PatientClinicalTimeline:
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": measurement.patient_id,
                "entry_type": "measurement",
                "entry_id": measurement.measurement_id,
            },
            execution_options={"populate_existing": True},
        )
        values = {
            "occurred_at": measurement.measured_at,
            "occurrence_date": None,
            "date_precision": "instant",
            "sort_key": measurement.measured_at.isoformat(),
            "accepted_at": measurement.updated_at,
            "entity_version": measurement.version,
            "record_status": measurement.record_status,
        }

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=measurement.patient_id,
                entry_type="measurement",
                entry_id=measurement.measurement_id,
                source_section="measurements",
                **values,
            )
            await self.add(db, row)
        else:
            for name, value in values.items():
                setattr(row, name, value)

            await self.flush(db)

        return row

    async def project_note(
        self, db: AsyncSession, account_id: UUID, note: PatientNoteResponse
    ) -> PatientClinicalTimeline:
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": note.patient_id,
                "entry_type": "note",
                "entry_id": note.note_id,
            },
            execution_options={"populate_existing": True},
        )
        values = {
            "occurred_at": note.created_at,
            "occurrence_date": None,
            "date_precision": "reference",
            "sort_key": note.created_at.isoformat(),
            "accepted_at": note.updated_at,
            "entity_version": note.version,
            "record_status": note.record_status,
        }

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=note.patient_id,
                entry_type="note",
                entry_id=note.note_id,
                source_section="notes",
                **values,
            )
            await self.add(db, row)
        else:
            for name, value in values.items():
                setattr(row, name, value)

            await self.flush(db)

        return row

    async def project_encounter(
        self, db: AsyncSession, account_id: UUID, encounter: PatientEncounterResponse
    ) -> PatientClinicalTimeline:
        row = await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": encounter.patient_id,
                "entry_type": "encounter",
                "entry_id": encounter.encounter_id,
            },
            execution_options={"populate_existing": True},
        )

        if row is Empty:
            row = PatientClinicalTimeline(
                account_id=account_id,
                patient_id=encounter.patient_id,
                entry_type="encounter",
                entry_id=encounter.encounter_id,
                source_section="encounters",
                occurred_at=encounter.occurred_at,
                occurrence_date=None,
                date_precision="instant",
                sort_key=encounter.occurred_at.isoformat(),
                accepted_at=encounter.updated_at,
                entity_version=encounter.version,
                record_status=encounter.record_status,
            )
            await self.add(db, row)
        else:
            row.occurred_at = encounter.occurred_at
            row.sort_key = encounter.occurred_at.isoformat()
            row.accepted_at = encounter.updated_at
            row.entity_version = encounter.version
            row.record_status = encounter.record_status
            await self.flush(db)

        return row


dao_antecedents = PatientAntecedentDAO(PatientAntecedent)
dao_antecedent_histories = PatientAntecedentHistoryDAO(PatientAntecedentHistory)
dao_immunizations = PatientImmunizationDAO(PatientImmunization)
dao_immunization_histories = PatientImmunizationHistoryDAO(PatientImmunizationHistory)
dao_measurements = PatientMeasurementDAO(PatientMeasurement)
dao_measurement_histories = PatientMeasurementHistoryDAO(PatientMeasurementHistory)
dao_notes = PatientNoteDAO(PatientNote)
dao_note_histories = PatientNoteHistoryDAO(PatientNoteHistory)
dao_clinical_timeline = PatientClinicalTimelineDAO(PatientClinicalTimeline)
dao_allergies = PatientAllergyIntoleranceDAO(PatientAllergyIntolerance)
dao_allergy_histories = PatientAllergyIntoleranceHistoryDAO(
    PatientAllergyIntoleranceHistory
)
dao_conditions = PatientConditionDAO(PatientCondition)
dao_condition_histories = PatientConditionHistoryDAO(PatientConditionHistory)
dao_section_reviews = PatientClinicalSectionReviewDAO(PatientClinicalSectionReview)
dao_section_review_histories = PatientClinicalSectionReviewHistoryDAO(
    PatientClinicalSectionReviewHistory
)
dao_clinical_profiles = PatientClinicalProfileDAO(PatientClinicalProfile)
dao_clinical_profile_histories = PatientClinicalProfileHistoryDAO(
    PatientClinicalProfileHistory
)
