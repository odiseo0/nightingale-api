from datetime import datetime
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class Account(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(Text)
    owner_user_id: Mapped[UUID]
    display_name: Mapped[str] = mapped_column(Text)
    time_zone: Mapped[str] = mapped_column(Text)
    location_name: Mapped[str] = mapped_column(Text)
    location_address: Mapped[str] = mapped_column(Text)
    location_country: Mapped[str] = mapped_column(Text, server_default="VE")
    location_state: Mapped[str] = mapped_column(Text)
    location_city: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    no_show_grace_minutes: Mapped[int] = mapped_column(server_default="15")
    version: Mapped[int] = mapped_column(server_default="1")


class AccountMembership(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class Professional(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    public_name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class AccountProfessional(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    professional_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class AccountDeviceAccess(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    device_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_by_user_id: Mapped[UUID]
    changed_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class AccountInvitation(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    invitee_user_id: Mapped[UUID]
    created_by_user_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(Text, server_default="pending")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    accepted_at: Mapped[datetime | None]
    accepted_operation_id: Mapped[UUID | None]
    version: Mapped[int] = mapped_column(server_default="1")
