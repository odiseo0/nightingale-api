from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class PatientClinicalProfile(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    sex_at_birth: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientNote(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    body: Mapped[str] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientNoteHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    body: Mapped[str] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class PatientMeasurement(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    kind: Mapped[str] = mapped_column(Text)
    measured_at: Mapped[datetime]
    captured_at_local: Mapped[datetime | None]
    method: Mapped[str | None] = mapped_column(Text)
    body_site: Mapped[str | None] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    systolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    diastolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientMeasurementHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    kind: Mapped[str] = mapped_column(Text)
    measured_at: Mapped[datetime]
    captured_at_local: Mapped[datetime | None]
    method: Mapped[str | None] = mapped_column(Text)
    body_site: Mapped[str | None] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    systolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    diastolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class PatientImmunization(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    vaccine_name: Mapped[str] = mapped_column(Text)
    occurrence_date: Mapped[str] = mapped_column(Text)
    record_kind: Mapped[str] = mapped_column(Text, server_default="unknown")
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    captured_at_local: Mapped[datetime | None]
    product_name: Mapped[str | None] = mapped_column(Text)
    dose_description: Mapped[str | None] = mapped_column(Text)
    lot_number: Mapped[str | None] = mapped_column(Text)
    route: Mapped[str | None] = mapped_column(Text)
    body_site: Mapped[str | None] = mapped_column(Text)
    location_text: Mapped[str | None] = mapped_column(Text)
    administrator_name: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientImmunizationHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    vaccine_name: Mapped[str] = mapped_column(Text)
    occurrence_date: Mapped[str] = mapped_column(Text)
    record_kind: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    product_name: Mapped[str | None] = mapped_column(Text)
    dose_description: Mapped[str | None] = mapped_column(Text)
    lot_number: Mapped[str | None] = mapped_column(Text)
    route: Mapped[str | None] = mapped_column(Text)
    body_site: Mapped[str | None] = mapped_column(Text)
    location_text: Mapped[str | None] = mapped_column(Text)
    administrator_name: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class PatientAntecedent(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    category: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    related_person_description: Mapped[str | None] = mapped_column(Text)
    occurrence_date: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientAntecedentHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    category: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    related_person_description: Mapped[str | None] = mapped_column(Text)
    occurrence_date: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class PatientClinicalTimeline(Base):
    __tablename__: str = "patient_clinical_timeline"

    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    entry_type: Mapped[str] = mapped_column(Text, primary_key=True)
    entry_id: Mapped[UUID] = mapped_column(primary_key=True)
    source_section: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime | None]
    occurrence_date: Mapped[str | None] = mapped_column(Text)
    date_precision: Mapped[str] = mapped_column(Text)
    sort_key: Mapped[str] = mapped_column(Text)
    accepted_at: Mapped[datetime]
    entity_version: Mapped[int]
    record_status: Mapped[str] = mapped_column(Text)


class PatientClinicalProfileHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    sex_at_birth: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
