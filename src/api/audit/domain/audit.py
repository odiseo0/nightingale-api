from datetime import datetime
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from src.core.schema import AdministrativeResponse, BaseModel, PageQuery
from src.core.schema.http import SerializedInstant


class OperationAudit(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)

    account_id: UUID7
    actor_user_id: UUID7
    actor_device_id: UUID7
    action: str
    object_type: str
    object_key: str | dict[str, str]
    outcome: Literal["accepted", "rejected", "conflict"]
    operation_id: UUID7
    correlation_id: UUID7
    occurred_at: AwareDatetime


class ControlAudit(BaseModel):
    account_id: UUID7 | None = None
    actor_user_id: UUID7 | None = None
    actor_device_id: UUID7 | None = None
    operator_ref: str | None = None
    action: str
    object_type: str
    object_key: str | None = None
    outcome: Literal["accepted", "rejected", "conflict"]
    correlation_id: UUID7
    occurred_at: AwareDatetime


class AuditQuery(PageQuery):
    from_: AwareDatetime | None = Field(default=None, alias="from")
    until: AwareDatetime | None = None
    action: str | None = Field(default=None, min_length=1)
    object_type: str | None = Field(default=None, min_length=1)
    object_id: UUID7 | None = None

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if (
            self.from_ is not None
            and self.until is not None
            and self.from_ >= self.until
        ):
            raise ValueError("El inicio debe ser anterior al fin")

        return self


class AuditEventResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7 | None
    actor_kind: Literal["staff", "operator", "anonymous"]
    actor_user_id: UUID7 | None
    actor_device_id: UUID7 | None
    operator_ref: str | None
    action: str
    object_type: str
    object_key: str | dict[str, str] | None
    outcome: Literal["accepted", "rejected", "conflict"]
    operation_id: UUID7 | None
    correlation_id: UUID7
    occurred_at: AwareDatetime

    @field_serializer("occurred_at")
    def serialize_event_instant(self, value: datetime) -> SerializedInstant:
        return self.serialize_instant(value)
