from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Text, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from src.core.db.model import Base, Date


class Patient(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)


class AccountPatient(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(Text)
    birth_date: Mapped[date | None]
    phone_code: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    identification_basis: Mapped[str | None] = mapped_column(Text)
    completion_status: Mapped[str] = mapped_column(Text, server_default="draft")
    status: Mapped[str] = mapped_column(Text, server_default="active")
    version: Mapped[int] = mapped_column(server_default="1")
    contact_links: Mapped[list[PatientContactRelationship]] = relationship(
        primaryjoin=lambda: and_(
            AccountPatient.account_id == foreign(PatientContactRelationship.account_id),
            AccountPatient.patient_id == foreign(PatientContactRelationship.patient_id),
        ),
        viewonly=True,
    )


class PatientIdentifier(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    issuing_country: Mapped[str] = mapped_column(Text, server_default="VE")
    document_type: Mapped[str] = mapped_column(Text(collation="C"))
    document_number: Mapped[str] = mapped_column(Text(collation="C"))
    verification_status: Mapped[str] = mapped_column(Text, server_default="declared")
    verified_at: Mapped[datetime | None]
    verified_by_user_id: Mapped[UUID | None]
    version: Mapped[int] = mapped_column(server_default="1")


class ContactPerson(Date, Base):
    __tablename__ = "contact_people"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    full_name: Mapped[str] = mapped_column(Text)
    phone_code: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    issuing_country: Mapped[str | None] = mapped_column(Text)
    document_type: Mapped[str | None] = mapped_column(Text(collation="C"))
    document_number: Mapped[str | None] = mapped_column(Text(collation="C"))
    status: Mapped[str] = mapped_column(Text, server_default="active")
    version: Mapped[int] = mapped_column(server_default="1")


class PatientContactRelationship(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    contact_person_id: Mapped[UUID] = mapped_column(primary_key=True)
    relationship_kind: Mapped[str] = mapped_column(Text)
    is_responsible_contact: Mapped[bool] = mapped_column(server_default="false")
    representation_status: Mapped[str] = mapped_column(
        Text, server_default="unverified"
    )
    verified_at: Mapped[datetime | None]
    verified_by_user_id: Mapped[UUID | None]
    valid_from: Mapped[datetime]
    valid_until: Mapped[datetime | None]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    version: Mapped[int] = mapped_column(server_default="1")
    patient: Mapped[AccountPatient] = relationship(
        primaryjoin=lambda: and_(
            foreign(PatientContactRelationship.account_id) == AccountPatient.account_id,
            foreign(PatientContactRelationship.patient_id) == AccountPatient.patient_id,
        ),
        viewonly=True,
    )
    contact: Mapped[ContactPerson] = relationship(
        primaryjoin=lambda: and_(
            foreign(PatientContactRelationship.account_id) == ContactPerson.account_id,
            foreign(PatientContactRelationship.contact_person_id) == ContactPerson.id,
        ),
        viewonly=True,
    )


class PatientBirthDateChange(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    previous_birth_date: Mapped[date | None]
    new_birth_date: Mapped[date | None]
    patient_version: Mapped[int]
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
