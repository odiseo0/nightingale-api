from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class AuditEvent(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID | None]
    actor_kind: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID | None]
    actor_device_id: Mapped[UUID | None]
    operator_ref: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    object_type: Mapped[str] = mapped_column(Text)
    object_key: Mapped[object | None] = mapped_column(JSONB(none_as_null=True))
    outcome: Mapped[str] = mapped_column(Text)
    operation_id: Mapped[UUID | None]
    correlation_id: Mapped[UUID]
    occurred_at: Mapped[datetime]
