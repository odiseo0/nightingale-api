from datetime import datetime
from uuid import UUID

from sqlalchemy import LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class AppUser(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    oidc_issuer: Mapped[str] = mapped_column(Text(collation="C"))
    oidc_subject: Mapped[str] = mapped_column(Text(collation="C"))
    display_name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class Device(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    display_name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    client_version: Mapped[str] = mapped_column(Text)
    local_schema_version: Mapped[int]
    last_seen_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class DeviceToken(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    device_id: Mapped[UUID]
    user_id: Mapped[UUID]
    secret_hash: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    replaced_by_token_id: Mapped[UUID | None]
