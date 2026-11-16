from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant

type MeasurementKind = Literal[
    "weight", "temperature", "oxygen_saturation", "heart_rate", "blood_pressure"
]
UNITS: dict[MeasurementKind, str] = {
    "weight": "kg",
    "temperature": "Cel",
    "oxygen_saturation": "%",
    "heart_rate": "/min",
    "blood_pressure": "mm[Hg]",
}
RANGES: dict[MeasurementKind, tuple[Decimal, Decimal]] = {
    "weight": (Decimal("0.01"), Decimal(1000)),
    "temperature": (Decimal(20), Decimal(45)),
    "oxygen_saturation": (Decimal(0), Decimal(100)),
    "heart_rate": (Decimal(1), Decimal(300)),
    "blood_pressure": (Decimal(20), Decimal(300)),
}


class MeasurementValues(BaseModel):
    kind: MeasurementKind
    measured_at: AwareDatetime | None = None
    captured_at_local: AwareDatetime | None = None
    method: str | None = Field(default=None, min_length=1)
    body_site: str | None = Field(default=None, min_length=1)
    value: Decimal | None = None
    systolic_value: Decimal | None = None
    diastolic_value: Decimal | None = None
    unit: str

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    @model_validator(mode="after")
    def valid_shape(self) -> Self:
        if self.unit != UNITS[self.kind]:
            raise ValueError("La unidad no corresponde al tipo")

        minimum, maximum = RANGES[self.kind]

        if self.kind == "blood_pressure":
            if (
                self.value is not None
                or self.systolic_value is None
                and self.diastolic_value is None
            ):
                raise ValueError("La presión requiere al menos un componente")

            components = (self.systolic_value, self.diastolic_value)
        else:
            if (
                self.value is None
                or self.systolic_value is not None
                or self.diastolic_value is not None
            ):
                raise ValueError("La medición no corresponde a la forma del tipo")

            components = (self.value,)

        if any(
            value is not None and not minimum <= value <= maximum
            for value in components
        ):
            raise ValueError("El valor excede los límites de captura")

        return self


class RecordPatientMeasurementPayload(MeasurementValues):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class CorrectPatientMeasurementPayload(BaseModel):
    measured_at: AwareDatetime | None = None
    captured_at_local: AwareDatetime | None = None
    method: str | None = Field(default=None, min_length=1)
    body_site: str | None = Field(default=None, min_length=1)
    value: Decimal | None = None
    systolic_value: Decimal | None = None
    diastolic_value: Decimal | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("La corrección requiere al menos un campo")

        return self


class InvalidatePatientMeasurementPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientMeasurementResponse(BaseModel):
    measurement_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    kind: MeasurementKind
    measured_at: AwareDatetime
    captured_at_local: AwareDatetime | None
    method: str | None
    body_site: str | None
    value: Decimal | None
    systolic_value: Decimal | None
    diastolic_value: Decimal | None
    unit: str
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    age_years: int | None
    age_as_of: date
    patient_version: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    @field_serializer(
        "measured_at",
        "captured_at_local",
        "created_at",
        "updated_at",
        when_used="unless-none",
    )
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @field_serializer(
        "value", "systolic_value", "diastolic_value", when_used="unless-none"
    )
    def serialize_decimal(self, value: Decimal) -> int | float:
        return int(value) if value == value.to_integral_value() else float(value)


class PatientMeasurementHistoryResponse(BaseModel):
    measurement_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    kind: MeasurementKind
    measured_at: AwareDatetime
    captured_at_local: AwareDatetime | None
    method: str | None
    body_site: str | None
    value: Decimal | None
    systolic_value: Decimal | None
    diastolic_value: Decimal | None
    unit: str
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int

    @field_serializer(
        "measured_at", "captured_at_local", "changed_at", when_used="unless-none"
    )
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @field_serializer(
        "value", "systolic_value", "diastolic_value", when_used="unless-none"
    )
    def serialize_decimal(self, value: Decimal) -> int | float:
        return int(value) if value == value.to_integral_value() else float(value)


class MeasurementQuery(PageQuery):
    kind: MeasurementKind | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None
    from_: AwareDatetime | None = Field(default=None, alias="from")
    until: AwareDatetime | None = None

    @model_validator(mode="after")
    def ordered_range(self) -> Self:
        if (
            self.from_ is not None
            and self.until is not None
            and self.from_ >= self.until
        ):
            raise ValueError("El rango debe tener inicio anterior al fin")

        return self


class MeasurementSummaryResponse(BaseModel):
    patient_id: UUID7
    items: list[PatientMeasurementResponse]
