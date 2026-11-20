from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base, Date


class DeclaredMedication(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    medication_name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    start_date: Mapped[str | None] = mapped_column(Text)
    end_date: Mapped[str | None] = mapped_column(Text)
    dose_description: Mapped[str | None] = mapped_column(Text)
    frequency_description: Mapped[str | None] = mapped_column(Text)
    prescriber_name: Mapped[str | None] = mapped_column(Text)
    route_description: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, server_default="declared")
    reviewed_at: Mapped[datetime | None]
    reviewed_by_user_id: Mapped[UUID | None]
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class DeclaredMedicationHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    medication_name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    start_date: Mapped[str | None] = mapped_column(Text)
    end_date: Mapped[str | None] = mapped_column(Text)
    dose_description: Mapped[str | None] = mapped_column(Text)
    frequency_description: Mapped[str | None] = mapped_column(Text)
    prescriber_name: Mapped[str | None] = mapped_column(Text)
    route_description: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None]
    reviewed_by_user_id: Mapped[UUID | None]
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
