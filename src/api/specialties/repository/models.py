from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base, Date


class SpecialtyTemplate(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(Text)
    specialty: Mapped[str] = mapped_column(Text, server_default="dentistry")
    template_status: Mapped[str] = mapped_column(Text, server_default="active")
    change_note: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class SpecialtyTemplateHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    specialty: Mapped[str] = mapped_column(Text)
    template_status: Mapped[str] = mapped_column(Text)
    change_note: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class SpecialtyTemplateFieldRow(Base):
    __tablename__ = "specialty_template_fields"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    template_id: Mapped[UUID]
    template_version: Mapped[int]
    field_key: Mapped[str] = mapped_column(Text)
    label: Mapped[str] = mapped_column(Text)
    field_kind: Mapped[str] = mapped_column(Text)
    required: Mapped[bool]
    options: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int]


class SpecialtyRecord(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    template_id: Mapped[UUID]
    template_version: Mapped[int]
    recorded_at: Mapped[datetime]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class SpecialtyRecordHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    template_id: Mapped[UUID]
    template_version: Mapped[int]
    recorded_at: Mapped[datetime]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class SpecialtyRecordValueRow(Base):
    __tablename__ = "specialty_record_values"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    record_id: Mapped[UUID]
    record_version: Mapped[int]
    field_key: Mapped[str] = mapped_column(Text)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric)
    value_boolean: Mapped[bool | None]
    value_date: Mapped[str | None] = mapped_column(Text)


class DentalFinding(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    tooth_fdi: Mapped[int]
    surface: Mapped[str | None] = mapped_column(Text)
    finding_kind: Mapped[str] = mapped_column(Text)
    finding_status: Mapped[str] = mapped_column(Text, server_default="active")
    note: Mapped[str | None] = mapped_column(Text)
    recorded_date: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class DentalFindingHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    tooth_fdi: Mapped[int]
    surface: Mapped[str | None] = mapped_column(Text)
    finding_kind: Mapped[str] = mapped_column(Text)
    finding_status: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    recorded_date: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class DentalTreatment(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    finding_id: Mapped[UUID]
    treatment_kind: Mapped[str] = mapped_column(Text)
    treatment_status: Mapped[str] = mapped_column(Text, server_default="planned")
    note: Mapped[str | None] = mapped_column(Text)
    performed_date: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class DentalTreatmentHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    finding_id: Mapped[UUID]
    treatment_kind: Mapped[str] = mapped_column(Text)
    treatment_status: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    performed_date: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
