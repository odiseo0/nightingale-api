from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base, Date


class ClinicalEncounter(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    appointment_id: Mapped[UUID | None]
    attending_professional_id: Mapped[UUID]
    assistant_user_id: Mapped[UUID | None]
    occurred_at: Mapped[datetime]
    ended_at: Mapped[datetime | None]
    captured_at_local: Mapped[datetime | None]
    reason: Mapped[str | None] = mapped_column(Text)
    reason_source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    history_present_illness: Mapped[str | None] = mapped_column(Text)
    findings: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    indications: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class ClinicalEncounterHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    appointment_id: Mapped[UUID | None]
    attending_professional_id: Mapped[UUID]
    assistant_user_id: Mapped[UUID | None]
    occurred_at: Mapped[datetime]
    ended_at: Mapped[datetime | None]
    captured_at_local: Mapped[datetime | None]
    reason: Mapped[str | None] = mapped_column(Text)
    reason_source_type: Mapped[str] = mapped_column(Text)
    history_present_illness: Mapped[str | None] = mapped_column(Text)
    findings: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    indications: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
