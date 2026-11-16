from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
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
