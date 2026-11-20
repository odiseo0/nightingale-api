from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base, Date


class PatientCondition(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(Text)
    clinical_status: Mapped[str] = mapped_column(Text, server_default="active")
    verification_status: Mapped[str] = mapped_column(Text, server_default="unconfirmed")
    onset_date: Mapped[str | None] = mapped_column(Text)
    abatement_date: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientConditionHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    clinical_status: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text)
    onset_date: Mapped[str | None] = mapped_column(Text)
    abatement_date: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class PatientClinicalSectionReview(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    section: Mapped[str] = mapped_column(primary_key=True)
    information_status: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    reviewed_by_user_id: Mapped[UUID]
    reviewed_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class PatientClinicalSectionReviewHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    section: Mapped[str] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    information_status: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
