from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base, Date


class Service(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    professional_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(Text)
    default_duration_minutes: Mapped[int]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    version: Mapped[int] = mapped_column(server_default="1")


class ProfessionalService(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    professional_id: Mapped[UUID] = mapped_column(primary_key=True)
    service_id: Mapped[UUID] = mapped_column(primary_key=True)
    duration_minutes_override: Mapped[int | None]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    version: Mapped[int] = mapped_column(server_default="1")
