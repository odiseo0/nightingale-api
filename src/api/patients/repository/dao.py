from collections.abc import Mapping
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, Row, Select, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.patients.domain.contacts import ContactQuery, RelationshipQuery
from src.api.patients.domain.patients import PatientQuery
from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType, datetime_now

from .models import (
    AccountPatient,
    ContactPerson,
    Patient,
    PatientBirthDateChange,
    PatientContactRelationship,
    PatientIdentifier,
)


class PatientDAO(DAO[Patient, BaseModel, BaseModel]):
    async def server_time(self, db: AsyncSession) -> datetime:
        return datetime_now()

    async def local_today(self, db: AsyncSession, time_zone: str) -> date:
        return await self.local_date(db, time_zone, datetime_now())

    async def local_date(
        self, db: AsyncSession, time_zone: str, instant: datetime
    ) -> date:
        return (
            await db.execute(select(cast(func.timezone(time_zone, instant), Date)))
        ).scalar_one()

    async def reserve_id(self, db: AsyncSession, patient_id: UUID) -> bool:
        # Across accounts, reserve only a new identity. A collision reveals no
        # patient data and never attaches an existing global identity.
        now = datetime_now()
        row = await db.scalar(
            text("""
            INSERT INTO nightingale.patients(id,created_at,updated_at)
            VALUES (:id,:now,:now)
            ON CONFLICT (id) DO NOTHING RETURNING id
        """),
            {"id": patient_id, "now": now},
        )

        return row is not None


class AccountPatientDAO(DAO[AccountPatient, BaseModel, BaseModel]):
    async def complete_for_contact(
        self, db: AsyncSession, account_id: UUID, contact_id: UUID
    ) -> list[AccountPatient]:
        rows = await db.scalars(
            select(self.model)
            .join(self.model.contact_links)
            .where(
                self.model.account_id == account_id,
                self.model.completion_status == "complete",
                PatientContactRelationship.contact_person_id == contact_id,
            )
            .order_by(self.model.patient_id)
        )

        return list(rows)

    async def create_profile(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> AccountPatient:
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def revise(
        self,
        db: AsyncSession,
        row: AccountPatient,
        changes: dict[str, object],
        now: datetime,
    ) -> AccountPatient:
        for name, value in changes.items():
            setattr(row, name, value)

        row.version += 1
        row.date_updated = now
        await self.flush(db)

        return row

    async def page(
        self, db: AsyncSession, account_id: UUID, query: PatientQuery
    ) -> tuple[list[AccountPatient], int]:
        statement = select(self.model).where(self.model.account_id == account_id)

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        if query.completion_status is not None:
            statement = statement.where(
                self.model.completion_status == query.completion_status
            )

        if query.q is not None:
            # LIKE metacharacters are literal input, not a client search syntax.
            # https://docs.sqlalchemy.org/en/21/core/sqlelement.html#sqlalchemy.sql.expression.ColumnElement.icontains
            document = (
                select(PatientIdentifier.id)
                .where(
                    PatientIdentifier.patient_id == self.model.patient_id,
                    PatientIdentifier.document_number.icontains(
                        query.q, autoescape=True
                    ),
                )
                .exists()
            )
            statement = statement.where(
                or_(self.model.full_name.icontains(query.q, autoescape=True), document)
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.patient_id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total


class PatientIdentifierDAO(DAO[PatientIdentifier, BaseModel, BaseModel]):
    async def has_document(self, db: AsyncSession, patient_id: UUID) -> bool:
        return await db.scalar(
            select(
                select(self.model.id)
                .where(
                    self.model.patient_id == patient_id,
                    self.model.verification_status.in_(("declared", "verified")),
                )
                .exists()
            )
        )

    async def available_ids(self, db: AsyncSession, identifiers: list[UUID]) -> bool:
        for identifier in sorted(identifiers):
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
                {"key": f"patient_identifier:{identifier}"},
            )

        return not await db.scalar(
            select(select(self.model.id).where(self.model.id.in_(identifiers)).exists())
        )

    async def page(
        self, db: AsyncSession, patient_id: UUID, offset: int, shows: int
    ) -> tuple[list[PatientIdentifier], int]:
        statement = select(self.model).where(self.model.patient_id == patient_id)
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id).offset(offset).limit(shows)
        )

        return list(rows), total


class ContactPersonDAO(DAO[ContactPerson, BaseModel, BaseModel]):
    async def lock_new_id(
        self, db: AsyncSession, contact_id: UUID
    ) -> ContactPerson | EmptyType:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": f"contact_person:{contact_id}"},
        )

        return await self.get(db, contact_id)

    async def revise(
        self,
        db: AsyncSession,
        row: ContactPerson,
        changes: dict[str, object],
        now: datetime,
    ) -> ContactPerson:
        return await self.update(
            db,
            row.id,
            obj_in={**changes, "date_updated": now, "version": row.version + 1},
            commit=False,
        )

    async def page(
        self, db: AsyncSession, account_id: UUID, query: ContactQuery
    ) -> tuple[list[ContactPerson], int]:
        statement = select(self.model).where(self.model.account_id == account_id)

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        if query.q is not None:
            statement = statement.where(
                or_(
                    self.model.full_name.icontains(query.q, autoescape=True),
                    self.model.document_number.icontains(query.q, autoescape=True),
                )
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total


class PatientContactRelationshipDAO(
    DAO[PatientContactRelationship, BaseModel, BaseModel]
):
    async def candidates(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID
    ) -> list[Row[PatientContactRelationship, ContactPerson]]:
        rows = await db.execute(
            select(self.model, ContactPerson)
            .join(self.model.contact)
            .where(
                self.model.account_id == account_id, self.model.patient_id == patient_id
            )
        )

        return list(rows)

    async def create_relationship(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> PatientContactRelationship:
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def revise(
        self,
        db: AsyncSession,
        row: PatientContactRelationship,
        values: dict[str, object],
        now: datetime,
    ) -> PatientContactRelationship:
        for name, value in values.items():
            setattr(row, name, value)

        row.date_updated = now
        row.version += 1
        await self.flush(db)

        return row

    def projection(self, account_id: UUID) -> Select[*tuple[object, ...]]:
        return (
            select(
                *self.model.__table__.columns,
                AccountPatient.full_name.label("patient_full_name"),
                ContactPerson.full_name.label("contact_full_name"),
                ContactPerson.phone_code,
                ContactPerson.phone,
            )
            .select_from(self.model)
            .join(self.model.patient)
            .join(self.model.contact)
            .where(self.model.account_id == account_id)
        )

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        query: RelationshipQuery,
        *,
        patient_id: UUID | None = None,
        contact_id: UUID | None = None,
    ) -> tuple[list[Mapping[str, object]], int]:
        statement = self.projection(account_id)

        if patient_id is not None:
            statement = statement.where(self.model.patient_id == patient_id)

        if contact_id is not None:
            statement = statement.where(self.model.contact_person_id == contact_id)

        if query.status is not None:
            statement = statement.where(self.model.status == query.status)

        total = await self.count(db, statement)
        rows = await db.execute(
            statement.order_by(self.model.patient_id, self.model.contact_person_id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows.mappings()), total


dao_patients = PatientDAO(Patient)
dao_profiles = AccountPatientDAO(AccountPatient)
dao_birth_changes = DAO(PatientBirthDateChange)
dao_identifiers = PatientIdentifierDAO(PatientIdentifier)
dao_contacts = ContactPersonDAO(ContactPerson)
dao_relationships = PatientContactRelationshipDAO(PatientContactRelationship)
