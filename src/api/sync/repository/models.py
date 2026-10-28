from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, LargeBinary, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class AccountSyncHead(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    last_sequence: Mapped[int] = mapped_column(BigInteger, server_default="0")
    retained_from_sequence: Mapped[int] = mapped_column(BigInteger, server_default="1")
    permission_epoch: Mapped[int] = mapped_column(BigInteger, server_default="1")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class OperationReceipt(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_user_id: Mapped[UUID] = mapped_column(primary_key=True)
    operation_id: Mapped[UUID] = mapped_column(primary_key=True)
    source_device_id: Mapped[UUID]
    contract_version: Mapped[int]
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_key: Mapped[object] = mapped_column(JSONB)
    request_hash: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(Text)
    entity_version: Mapped[int | None]
    result_json: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    completed_at: Mapped[datetime]
    result_expires_at: Mapped[datetime]
    purged_at: Mapped[datetime | None]


class ChangeLog(Base):
    __tablename__ = "change_log"

    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    sequence: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ordinal: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[UUID]
    group_size: Mapped[int]
    source_account_id: Mapped[UUID]
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    entity_type: Mapped[str] = mapped_column(Text)
    entity_key: Mapped[object] = mapped_column(JSONB)
    entity_version: Mapped[int]
    change_kind: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(Text)
    projection_json: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    previous_starts_at: Mapped[datetime | None]
    previous_ends_at: Mapped[datetime | None]
    accepted_at: Mapped[datetime]


class SyncSnapshot(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    user_id: Mapped[UUID]
    device_id: Mapped[UUID]
    contract_version: Mapped[int]
    model_revision: Mapped[str] = mapped_column(Text)
    appointments_from: Mapped[date]
    appointments_until: Mapped[date]
    window_time_zone: Mapped[str] = mapped_column(Text)
    window_starts_at: Mapped[datetime]
    window_ends_at: Mapped[datetime]
    base_sequence: Mapped[int] = mapped_column(BigInteger)
    permission_epoch: Mapped[int] = mapped_column(BigInteger)
    audience: Mapped[str] = mapped_column(Text)
    item_count: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime]
    expires_at: Mapped[datetime]


class SyncSnapshotItem(Base):
    snapshot_id: Mapped[UUID] = mapped_column(primary_key=True)
    ordinal: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_key: Mapped[object] = mapped_column(JSONB)
    entity_version: Mapped[int]
    state_json: Mapped[dict] = mapped_column(JSONB)


class SyncStreamLease(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    user_id: Mapped[UUID]
    device_id: Mapped[UUID]
    expires_at: Mapped[datetime]
