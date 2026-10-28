from datetime import UTC, date, datetime, timedelta
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from src.api.appointments.domain.appointments import AppointmentHistoryProjection
from src.api.schedule.domain.schedule import AbsoluteInterval, ScheduleRuleFields
from src.api.sync.domain import operations as projections
from src.api.sync.domain.operations import OperationState
from src.core.schema import BaseModel
from src.core.schema.http import SerializedInstant

PROJECTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "account": projections.AccountResponse,
    "account_device": projections.AccountDeviceResponse,
    "membership": projections.MemberResponse,
    "invitation": projections.InvitationResponse,
    "professional": projections.ProfessionalResponse,
    "patient_profile": projections.PatientProfileResponse,
    "patient_identifier": projections.PatientIdentifierResponse,
    "contact_person": projections.ContactResponse,
    "patient_contact": projections.RelationshipResponse,
    "service": projections.ServiceResponse,
    "service_offer": projections.ServiceOfferResponse,
    "schedule_rule": projections.ScheduleRuleResponse,
    "schedule_exception": projections.ScheduleExceptionResponse,
    "schedule_block": projections.ScheduleBlockResponse,
    "appointment": projections.AppointmentResponse,
    "appointment_history": AppointmentHistoryProjection,
}


class SyncWindow(AbsoluteInterval):
    appointments_from: date
    appointments_until: date
    time_zone: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_window(self) -> Self:
        if not 0 < (self.appointments_until - self.appointments_from).days <= 366:
            raise ValueError("La ventana debe incluir entre 1 y 366 días")

        return self


class SyncPosition(BaseModel):
    contract_version: Literal[1] = 1
    account_id: UUID7
    user_id: UUID7
    device_id: UUID7
    audience: Literal["members", "owner"]
    permission_epoch: int = Field(strict=True, ge=1)
    sequence: int = Field(strict=True, ge=0)
    window: SyncWindow
    issued_at: AwareDatetime
    expires_at: AwareDatetime

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def bounded_lifetime(self) -> Self:
        if not timedelta(0) < self.expires_at - self.issued_at <= timedelta(days=90):
            raise ValueError("El cursor requiere un vencimiento de hasta 90 días")

        return self


class ChangeQuery(BaseModel):
    cursor: str = Field(min_length=1, max_length=8192)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class SyncChange(BaseModel):
    entity_type: str
    entity_key: UUID7 | dict[str, UUID7]
    entity_version: int = Field(ge=1)
    change_kind: Literal["upsert", "remove"]
    state: OperationState | AppointmentHistoryProjection | None

    @model_validator(mode="after")
    def state_matches_kind(self) -> Self:
        if (self.change_kind == "remove") != (self.state is None):
            raise ValueError("La retirada no contiene estado")

        schema = PROJECTION_SCHEMAS.get(self.entity_type)

        if (
            schema is None
            or self.state is not None
            and not isinstance(self.state, schema)
        ):
            raise ValueError("El estado no corresponde al tipo de entidad")

        return self


class ChangeGroup(BaseModel):
    group_id: UUID7
    operation_id: UUID7
    changes: list[SyncChange]
    accepted_at: AwareDatetime

    @field_serializer("accepted_at", when_used="json")
    def utc_acceptance(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ChangePage(BaseModel):
    groups: list[ChangeGroup]
    next_cursor: str
    has_more: bool


class SnapshotRequest(BaseModel):
    appointments_from: date | None = None
    appointments_until: date | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("appointments_from", "appointments_until", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        if value is None:
            raise ValueError("Una fecha presente no puede ser nula")

        return ScheduleRuleFields.calendar_date(value)

    @model_validator(mode="after")
    def bounded_dates(self) -> Self:
        if (
            self.appointments_from is not None
            and self.appointments_until is not None
            and not (0 < (self.appointments_until - self.appointments_from).days <= 366)
        ):
            raise ValueError("La ventana debe incluir entre 1 y 366 días")

        return self


class SnapshotResponse(BaseModel):
    snapshot_id: UUID7
    account_id: UUID7
    contract_version: Literal[1] = 1
    model_revision: str
    window: SyncWindow
    base_cursor: str
    expires_at: AwareDatetime
    item_count: int = Field(ge=0)

    @field_serializer("expires_at", when_used="json")
    def utc_expiry(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class SyncItem(BaseModel):
    entity_type: str
    entity_key: UUID7 | dict[str, UUID7]
    entity_version: int = Field(ge=1)
    state: OperationState | AppointmentHistoryProjection

    @model_validator(mode="after")
    def typed_state(self) -> Self:
        schema = PROJECTION_SCHEMAS.get(self.entity_type)

        if schema is None or not isinstance(self.state, schema):
            raise ValueError("El estado no corresponde al tipo de entidad")

        return self
