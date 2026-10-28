from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import UUID7, AwareDatetime, field_serializer

from src.api.sync.domain.downloads import SyncPosition
from src.core.schema import BaseModel
from src.core.schema.http import SerializedInstant


class ChangesAvailable(BaseModel):
    account_id: UUID7
    cursor: str


class Heartbeat(BaseModel):
    server_time: AwareDatetime

    @field_serializer("server_time", when_used="json")
    def utc_server_time(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class StreamEvent(BaseModel):
    event: Literal["changes_available", "heartbeat", "access_revoked"]
    data: ChangesAvailable | Heartbeat | None = None
    event_id: str | None = None


@dataclass(frozen=True, slots=True)
class EventConnection:
    lease_id: UUID
    position: SyncPosition


class EventStatus(BaseModel):
    sequence: int
    cursor: str
    server_time: AwareDatetime
