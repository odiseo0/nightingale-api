from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field

from src.core.schema import BaseModel

MeasurementKind = Literal[
    "weight", "temperature", "oxygen_saturation", "heart_rate", "blood_pressure"
]

RecordStatus = Literal["valid", "entered-in-error"]


class SeriesEntry(BaseModel):
    measurement_id: str
    source_version: int = Field(ge=1)
    kind: MeasurementKind
    measured_at: date
    value: Decimal | None = None
    systolic_value: Decimal | None = None
    diastolic_value: Decimal | None = None
    unit: str
    record_status: RecordStatus

    model_config = ConfigDict(extra="forbid")


class SeriesPoint(BaseModel):
    measurement_kind: MeasurementKind
    measured_at: date
    value: Decimal | None = None
    systolic_value: Decimal | None = None
    diastolic_value: Decimal | None = None
    unit: str
    source_measurement_id: str
    source_version: int

    model_config = ConfigDict(extra="forbid")


class SeriesSelection(BaseModel):
    points: list[SeriesPoint]

    model_config = ConfigDict(extra="forbid")


def select_valid_series(
    entries: list[SeriesEntry], kind: MeasurementKind
) -> SeriesSelection:
    by_identity: dict[str, SeriesEntry] = {}
    for entry in entries:
        if entry.kind != kind or entry.record_status != "valid":
            continue
        by_identity[entry.measurement_id] = entry

    ordered = sorted(
        by_identity.values(),
        key=lambda entry: (entry.measured_at, entry.measurement_id),
    )

    return SeriesSelection(
        points=[
            SeriesPoint(
                measurement_kind=entry.kind,
                measured_at=entry.measured_at,
                value=entry.value,
                systolic_value=entry.systolic_value,
                diastolic_value=entry.diastolic_value,
                unit=entry.unit,
                source_measurement_id=entry.measurement_id,
                source_version=entry.source_version,
            )
            for entry in ordered
        ]
    )


class AgeAtMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age_days: int = Field(ge=0)
    age_months: int = Field(ge=0)
    age_years: int = Field(ge=0)


def age_on(birth_date: date, on: date) -> AgeAtMeasurement | None:
    if on < birth_date:
        return None

    days = (on - birth_date).days
    years = (
        on.year
        - birth_date.year
        - ((on.month, on.day) < (birth_date.month, birth_date.day))
    )
    months = (on.year - birth_date.year) * 12 + on.month - birth_date.month

    if on.day < birth_date.day:
        months -= 1

    months = max(months, 0)

    return AgeAtMeasurement(age_days=days, age_months=months, age_years=years)
