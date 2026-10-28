import re
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

from src.core.schema import AdministrativeResponse, BaseModel, PageQuery


class MinuteInterval(BaseModel):
    local_start_minute: int = Field(strict=True, ge=0, le=1439)
    local_end_minute: int = Field(strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.local_start_minute >= self.local_end_minute:
            raise ValueError("El inicio debe preceder al fin")

        return self


class ScheduleRuleFields(MinuteInterval):
    iso_weekday: int = Field(strict=True, ge=1, le=7)
    valid_from: date
    valid_until: date | None = None

    @field_validator("valid_from", "valid_until", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        if value is not None and (
            not isinstance(value, (str, date))
            or isinstance(value, datetime)
            or isinstance(value, str)
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None
        ):
            raise ValueError("La fecha debe usar YYYY-MM-DD")

        return value

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("El fin de vigencia no puede preceder al inicio")

        return self


class CreateScheduleRulePayload(ScheduleRuleFields):
    professional_id: UUID7


class ScheduleRulePatch(BaseModel):
    iso_weekday: int | None = Field(default=None, strict=True, ge=1, le=7)
    local_start_minute: int | None = Field(default=None, strict=True, ge=0, le=1439)
    local_end_minute: int | None = Field(default=None, strict=True, ge=1, le=1440)
    valid_from: date | None = None
    valid_until: date | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("valid_from", "valid_until", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        return ScheduleRuleFields.calendar_date(value)

    @field_validator(
        "iso_weekday", "local_start_minute", "local_end_minute", "valid_from"
    )
    @classmethod
    def nonnull(cls, value: int | date | None) -> int | date:
        if value is None:
            raise ValueError("El campo presente no puede ser nulo")

        return value

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class ScheduleRuleStatusPayload(BaseModel):
    status: Literal["active", "inactive"]

    model_config = ConfigDict(extra="forbid")


class ScheduleRuleResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7
    professional_id: UUID7
    iso_weekday: int
    local_start_minute: int
    local_end_minute: int
    valid_from: date
    valid_until: date | None
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    def applies(self, day: date) -> bool:
        return (
            self.status == "active"
            and day.isoweekday() == self.iso_weekday
            and self.valid_from <= day
            and (self.valid_until is None or day <= self.valid_until)
        )


class ScheduleRuleQuery(PageQuery):
    professional_id: UUID7 | None = None
    iso_weekday: int | None = Field(default=None, ge=1, le=7)
    status: Literal["active", "inactive"] | None = None
    from_date: date | None = None
    until_date: date | None = None

    @field_validator("from_date", "until_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        return ScheduleRuleFields.calendar_date(value)

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        if (
            self.from_date is not None
            and self.until_date is not None
            and self.until_date < self.from_date
        ):
            raise ValueError("El rango de fechas está invertido")

        return self


class RequiredScheduleInterval(MinuteInterval):
    local_date: date


class ScheduleDay(BaseModel):
    local_date: date
    time_zone: str
    intervals: list[MinuteInterval]


class ScheduleExceptionFields(BaseModel):
    local_date: date
    kind: Literal["closed", "replacement"]
    local_start_minute: int | None = Field(default=None, strict=True, ge=0, le=1439)
    local_end_minute: int | None = Field(default=None, strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")

    @field_validator("local_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        return ScheduleRuleFields.calendar_date(value)

    @model_validator(mode="after")
    def valid_replacement(self) -> Self:
        if self.kind == "closed":
            if self.local_start_minute is not None or self.local_end_minute is not None:
                raise ValueError("Un cierre no admite extremos")
        elif (
            self.local_start_minute is None
            or self.local_end_minute is None
            or self.local_start_minute >= self.local_end_minute
        ):
            raise ValueError("El reemplazo requiere un intervalo válido")

        return self


class CreateScheduleExceptionPayload(ScheduleExceptionFields):
    professional_id: UUID7


class ScheduleExceptionPatch(BaseModel):
    local_date: date | None = None
    kind: Literal["closed", "replacement"] | None = None
    local_start_minute: int | None = Field(default=None, strict=True, ge=0, le=1439)
    local_end_minute: int | None = Field(default=None, strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")

    @field_validator("local_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        return ScheduleRuleFields.calendar_date(value)

    @field_validator("local_date", "kind")
    @classmethod
    def nonnull(cls, value: date | str | None) -> date | str:
        if value is None:
            raise ValueError("El campo presente no puede ser nulo")

        return value

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class ScheduleExceptionResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7
    professional_id: UUID7
    local_date: date
    kind: Literal["closed", "replacement"]
    local_start_minute: int | None
    local_end_minute: int | None
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class ScheduleExceptionQuery(PageQuery):
    professional_id: UUID7 | None = None
    status: Literal["active", "inactive"] | None = None
    from_date: date
    until_date: date

    @field_validator("from_date", "until_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        return ScheduleRuleFields.calendar_date(value)

    @model_validator(mode="after")
    def bounded_dates(self) -> Self:
        if not 0 <= (self.until_date - self.from_date).days <= 365:
            raise ValueError("El rango debe incluir entre 1 y 366 días")

        return self


class AbsoluteInterval(BaseModel):
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    model_config = ConfigDict(extra="forbid")

    @field_validator("starts_at", "ends_at", mode="before")
    @classmethod
    def explicit_instant(cls, value: object) -> str | datetime:
        if not isinstance(value, (str, datetime)) or (
            isinstance(value, str)
            and re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})",
                value,
            )
            is None
        ):
            raise ValueError("El instante requiere fecha y offset")

        return value

    @model_validator(mode="after")
    def ordered_instants(self) -> Self:
        if self.starts_at >= self.ends_at:
            raise ValueError("El inicio debe preceder al fin")

        return self

    @field_serializer("starts_at", "ends_at", when_used="json")
    def utc_instant(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ScheduleBlockFields(AbsoluteInterval):
    reason_code: Literal["vacation", "administrative", "unavailable"]


class CreateScheduleBlockPayload(ScheduleBlockFields):
    professional_id: UUID7
    account_id: UUID7 | None


class ScheduleBlockPatch(BaseModel):
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    reason_code: Literal["vacation", "administrative", "unavailable"] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("starts_at", "ends_at", mode="before")
    @classmethod
    def explicit_instant(cls, value: object) -> str | datetime:
        return AbsoluteInterval.explicit_instant(value)

    @field_validator("reason_code")
    @classmethod
    def nonnull(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("El campo presente no puede ser nulo")

        return value

    @field_serializer("starts_at", "ends_at", when_used="json")
    def utc_instant(self, value: datetime | None) -> str | None:
        return (
            None
            if value is None
            else value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class ScheduleBlockResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7 | None
    professional_id: UUID7
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    reason_code: Literal["vacation", "administrative", "unavailable"] | None
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    @field_serializer("starts_at", "ends_at", when_used="json")
    def utc_instant(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ScheduleBlockQuery(PageQuery):
    professional_id: UUID7 | None = None
    status: Literal["active", "inactive"] | None = None
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


class AvailabilityQuery(BaseModel):
    professional_id: UUID7
    service_id: UUID7
    from_: AwareDatetime = Field(alias="from")
    until: AwareDatetime
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")

    @field_validator("from_", "until", mode="before")
    @classmethod
    def explicit_instant(cls, value: object) -> str | datetime:
        return AbsoluteInterval.explicit_instant(value)

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def integer_duration(cls, value: object) -> object:
        if isinstance(value, (bool, float)):
            raise ValueError("La duración requiere minutos enteros")

        return value

    @model_validator(mode="after")
    def bounded_instants(self) -> Self:
        if not timedelta(0) < self.until - self.from_ <= timedelta(days=31):
            raise ValueError("El rango debe ser positivo y no superar 31 días")

        return self


class AvailabilityResponse(BaseModel):
    account_id: UUID7
    professional_id: UUID7
    service_id: UUID7
    reference_duration_minutes: int = Field(ge=1, le=1440)
    requested_duration_minutes: int = Field(ge=1, le=1440)
    available_intervals: list[AbsoluteInterval]
