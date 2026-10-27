import re
from datetime import date, datetime
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
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
