from datetime import datetime
from uuid import UUID

from sqlalchemy import Date, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel

from .models import (
    AccountPatient,
    ContactPerson,
    Patient,
    PatientContactRelationship,
    PatientIdentifier,
)


class PatientDAO(DAO[Patient, BaseModel, BaseModel]):
    async def server_time(self, db: AsyncSession):
        return await db.scalar(select(func.clock_timestamp()))

    async def local_today(self, db: AsyncSession, time_zone: str):
        return await db.scalar(
            select(cast(func.timezone(time_zone, func.clock_timestamp()), Date))
        )

    async def local_date(self, db: AsyncSession, time_zone: str, instant: datetime):
        return await db.scalar(select(cast(func.timezone(time_zone, instant), Date)))

    async def reserve_id(self, db: AsyncSession, patient_id: UUID) -> bool:
        # Across accounts, reserve only a new identity. A collision reveals no
        # patient data and never attaches an existing global identity.
        row = await db.scalar(
            text("""
            INSERT INTO nightingale.patients(id,created_at,updated_at)
            VALUES (:id,clock_timestamp(),clock_timestamp())
            ON CONFLICT (id) DO NOTHING RETURNING id
        """),
            {"id": patient_id},
        )

        return row is not None


class AccountPatientDAO(DAO[AccountPatient, BaseModel, BaseModel]):
    async def complete_for_contact(
        self, db: AsyncSession, account_id: UUID, contact_id: UUID
    ):
        rows = await db.scalars(
            select(self.model)
            .join(
                PatientContactRelationship,
                (PatientContactRelationship.account_id == self.model.account_id)
                & (PatientContactRelationship.patient_id == self.model.patient_id),
            )
            .where(
                self.model.account_id == account_id,
                self.model.completion_status == "complete",
                PatientContactRelationship.contact_person_id == contact_id,
            )
            .order_by(self.model.patient_id)
        )

        return list(rows)

    async def create_profile(
        self, db: AsyncSession, values: dict, *, commit: bool = True
    ):
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def scoped(self, db: AsyncSession, account_id: UUID, patient_id: UUID):
        return await self.get_by(
            db,
            where={"account_id": account_id, "patient_id": patient_id},
            execution_options={"populate_existing": True},
        )

    async def revise(
        self, db: AsyncSession, row: AccountPatient, changes: dict, now: datetime
    ):
        for name, value in changes.items():
            setattr(row, name, value)

        row.version += 1
        row.updated_at = now
        await self.flush(db)

        return row

    async def page(self, db: AsyncSession, account_id: UUID, query):
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

    async def page(self, db: AsyncSession, patient_id: UUID, offset: int, shows: int):
        statement = select(self.model).where(self.model.patient_id == patient_id)
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id).offset(offset).limit(shows)
        )

        return list(rows), total


class ContactPersonDAO(DAO[ContactPerson, BaseModel, BaseModel]):
    async def lock_new_id(self, db: AsyncSession, contact_id: UUID):
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": f"contact_person:{contact_id}"},
        )

        return await self.get(db, contact_id)

    async def scoped(self, db: AsyncSession, account_id: UUID, contact_id: UUID):
        return await self.get_by(
            db,
            where={"account_id": account_id, "id": contact_id},
            execution_options={"populate_existing": True},
        )

    async def revise(
        self, db: AsyncSession, row: ContactPerson, changes: dict, now: datetime
    ):
        return await self.update(
            db,
            row.id,
            obj_in={**changes, "updated_at": now, "version": row.version + 1},
            commit=False,
        )

    async def page(self, db: AsyncSession, account_id: UUID, query):
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
    async def candidates(self, db: AsyncSession, account_id: UUID, patient_id: UUID):
        rows = await db.execute(
            select(self.model, ContactPerson)
            .join(
                ContactPerson,
                (ContactPerson.account_id == self.model.account_id)
                & (ContactPerson.id == self.model.contact_person_id),
            )
            .where(
                self.model.account_id == account_id, self.model.patient_id == patient_id
            )
        )

        return list(rows)

    async def scoped(
        self, db: AsyncSession, account_id: UUID, patient_id: UUID, contact_id: UUID
    ):
        return await self.get_by(
            db,
            where={
                "account_id": account_id,
                "patient_id": patient_id,
                "contact_person_id": contact_id,
            },
            execution_options={"populate_existing": True},
        )

    async def create_relationship(
        self, db: AsyncSession, values: dict, *, commit: bool = True
    ):
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def revise(
        self,
        db: AsyncSession,
        row: PatientContactRelationship,
        values: dict,
        now: datetime,
    ):
        for name, value in values.items():
            setattr(row, name, value)

        row.updated_at = now
        row.version += 1
        await self.flush(db)

        return row

    def projection(self, account_id: UUID):
        return (
            select(
                *self.model.__table__.columns,
                AccountPatient.full_name.label("patient_full_name"),
                ContactPerson.full_name.label("contact_full_name"),
                ContactPerson.phone_code,
                ContactPerson.phone,
            )
            .select_from(self.model)
            .join(
                AccountPatient,
                (AccountPatient.account_id == self.model.account_id)
                & (AccountPatient.patient_id == self.model.patient_id),
            )
            .join(
                ContactPerson,
                (ContactPerson.account_id == self.model.account_id)
                & (ContactPerson.id == self.model.contact_person_id),
            )
            .where(self.model.account_id == account_id)
        )

    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        query,
        *,
        patient_id=None,
        contact_id=None,
    ):
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
dao_identifiers = PatientIdentifierDAO(PatientIdentifier)
dao_contacts = ContactPersonDAO(ContactPerson)
dao_relationships = PatientContactRelationshipDAO(PatientContactRelationship)
