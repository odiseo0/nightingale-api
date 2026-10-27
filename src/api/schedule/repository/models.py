from datetime import date, datetime
from uuid import UUID

from sqlalchemy import SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class ScheduleRule(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    professional_id: Mapped[UUID]
    iso_weekday: Mapped[int] = mapped_column(SmallInteger)
    local_start_minute: Mapped[int] = mapped_column(SmallInteger)
    local_end_minute: Mapped[int] = mapped_column(SmallInteger)
    valid_from: Mapped[date]
    valid_until: Mapped[date | None]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")
