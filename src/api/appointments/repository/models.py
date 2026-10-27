from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class Appointment(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    professional_id: Mapped[UUID]
    service_id: Mapped[UUID]
    responsible_contact_id: Mapped[UUID | None]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    status: Mapped[str] = mapped_column(Text, server_default="scheduled")
    confirmed_at: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(server_default="1")
    service_name_snapshot: Mapped[str] = mapped_column(Text)
    offered_duration_minutes_snapshot: Mapped[int]
    professional_name_snapshot: Mapped[str] = mapped_column(Text)
    location_name_snapshot: Mapped[str] = mapped_column(Text)
    location_address_snapshot: Mapped[str] = mapped_column(Text)
    location_country_snapshot: Mapped[str] = mapped_column(Text)
    location_state_snapshot: Mapped[str] = mapped_column(Text)
    location_city_snapshot: Mapped[str] = mapped_column(Text)
    time_zone_snapshot: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class AppointmentHistory(Base):
    appointment_id: Mapped[UUID] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    confirmed_at: Mapped[datetime | None]
    responsible_contact_id: Mapped[UUID | None]
    service_name_snapshot: Mapped[str] = mapped_column(Text)
    offered_duration_minutes_snapshot: Mapped[int]
    professional_name_snapshot: Mapped[str] = mapped_column(Text)
    location_name_snapshot: Mapped[str] = mapped_column(Text)
    location_address_snapshot: Mapped[str] = mapped_column(Text)
    location_country_snapshot: Mapped[str] = mapped_column(Text)
    location_state_snapshot: Mapped[str] = mapped_column(Text)
    location_city_snapshot: Mapped[str] = mapped_column(Text)
    time_zone_snapshot: Mapped[str] = mapped_column(Text)
    actor_kind: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID | None]
    actor_contact_person_id: Mapped[UUID | None]
    change_reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime]
