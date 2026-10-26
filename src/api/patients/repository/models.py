from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class Patient(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class AccountPatient(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(Text)
    birth_date: Mapped[date | None]
    phone_code: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    identification_basis: Mapped[str | None] = mapped_column(Text)
    completion_status: Mapped[str] = mapped_column(Text, server_default="draft")
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientIdentifier(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    issuing_country: Mapped[str] = mapped_column(Text, server_default="VE")
    document_type: Mapped[str] = mapped_column(Text(collation="C"))
    document_number: Mapped[str] = mapped_column(Text(collation="C"))
    verification_status: Mapped[str] = mapped_column(Text, server_default="declared")
    verified_at: Mapped[datetime | None]
    verified_by_user_id: Mapped[UUID | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class ContactPerson(Base):
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
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientContactRelationship(Base):
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
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")
