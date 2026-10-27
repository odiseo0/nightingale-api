from datetime import UTC, datetime, timedelta
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

from src.api.schedule.domain.schedule import AbsoluteInterval
from src.core.schema import AdministrativeResponse, BaseModel, PageQuery


class AppointmentInterval(AbsoluteInterval):
    @model_validator(mode="after")
    def whole_minutes(self) -> Self:
        start, end = self.starts_at.astimezone(UTC), self.ends_at.astimezone(UTC)

        if (
            start.second
            or start.microsecond
            or end.second
            or end.microsecond
            or not timedelta(minutes=1) <= end - start <= timedelta(minutes=1440)
        ):
            raise ValueError("La cita requiere entre 1 y 1440 minutos, sin segundos")

        return self


class CreateAppointmentPayload(AppointmentInterval):
    patient_id: UUID7
    professional_id: UUID7
    service_id: UUID7
    responsible_contact_id: UUID7 | None = None


class EmptyAppointmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppointmentReasonPayload(BaseModel):
    change_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class AppointmentState(AppointmentInterval):
    responsible_contact_id: UUID7 | None
    status: Literal["scheduled", "confirmed", "cancelled", "completed", "no_show"]
    confirmed_at: AwareDatetime | None
    version: int = Field(ge=1)
    service_name_snapshot: str = Field(min_length=1)
    offered_duration_minutes_snapshot: int = Field(ge=1, le=1440)
    professional_name_snapshot: str = Field(min_length=1)
    location_name_snapshot: str = Field(min_length=1)
    location_address_snapshot: str = Field(min_length=1)
    location_country_snapshot: str = Field(min_length=2, max_length=2)
    location_state_snapshot: str = Field(min_length=1)
    location_city_snapshot: str = Field(min_length=1)
    time_zone_snapshot: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_confirmation(self) -> Self:
        if (
            self.status == "scheduled"
            and self.confirmed_at is not None
            or self.status == "confirmed"
            and self.confirmed_at is None
        ):
            raise ValueError("La confirmación no corresponde al estado")

        return self

    @field_serializer("confirmed_at", when_used="json")
    def confirmed_instant(self, value: datetime | None) -> str | None:
        return (
            None
            if value is None
            else value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )


class AppointmentResponse(AdministrativeResponse, AppointmentState):
    id: UUID7
    account_id: UUID7
    patient_id: UUID7
    professional_id: UUID7
    service_id: UUID7
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AppointmentHistoryResponse(AppointmentState):
    appointment_id: UUID7
    account_id: UUID7
    action: Literal[
        "created", "confirmed", "rescheduled", "cancelled", "completed", "no_show"
    ]
    actor_kind: Literal["staff", "patient", "contact"]
    actor_user_id: UUID7 | None
    actor_contact_person_id: UUID7 | None
    change_reason: str | None
    changed_at: AwareDatetime

    @field_serializer("changed_at", when_used="json")
    def changed_instant(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class AppointmentHistoryProjection(AbsoluteInterval):
    appointment_id: UUID7
    account_id: UUID7
    version: int
    items: list[AppointmentHistoryResponse]


class AppointmentQuery(PageQuery):
    professional_id: UUID7 | None = None
    patient_id: UUID7 | None = None
    service_id: UUID7 | None = None
    status: (
        Literal["scheduled", "confirmed", "cancelled", "completed", "no_show"] | None
    ) = None
    from_: AwareDatetime = Field(alias="from")
    until: AwareDatetime

    @field_validator("from_", "until", mode="before")
    @classmethod
    def explicit_instant(cls, value: object) -> str | datetime:
        return AbsoluteInterval.explicit_instant(value)

    @model_validator(mode="after")
    def bounded_instants(self) -> Self:
        if not timedelta(0) < self.until - self.from_ <= timedelta(days=366):
            raise ValueError("El rango debe ser positivo y no superar 366 días")

        return self


class AppointmentHistoryQuery(PageQuery):
    after_version: int | None = Field(default=None, ge=0)


class IncompatibleSchedule(Exception):
    """Revert the proposed schedule while retaining the outer operation receipt."""
