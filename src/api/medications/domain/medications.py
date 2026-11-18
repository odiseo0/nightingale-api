from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant

MedicationSourceType = Literal[
    "patient", "caregiver", "other_professional", "document"
]
MedicationReviewStatus = Literal["declared", "reviewed"]


class DeclaredMedicationFields(BaseModel):
    medication_name: str = Field(min_length=1)
    source_type: MedicationSourceType
    start_date: ClinicalDate | None = None
    end_date: ClinicalDate | None = None
    dose_description: str | None = Field(default=None, min_length=1)
    frequency_description: str | None = Field(default=None, min_length=1)
    prescriber_name: str | None = Field(default=None, min_length=1)
    route_description: str | None = Field(default=None, min_length=1)
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def period_order(self) -> Self:
        from datetime import date as date_type

        if self.start_date is None or self.end_date is None:
            return self

        def bounds(value: str) -> tuple[date_type, date_type]:
            year_text, month_text, day_text = (
                value.split("-") + [None, None]
            )[:3]
            year = int(year_text)
            month = int(month_text) if month_text else None
            day = int(day_text) if day_text else None
            start = date_type(year, month or 1, day or 1)
            if month is None:
                end = date_type(year, 12, 31)
            elif day is None:
                end = date_type(
                    year + (month == 12), month % 12 + 1, 1
                ) - date_type.resolution
            else:
                end = start
            return start, end

        start_min, _ = bounds(self.start_date)
        _, end_max = bounds(self.end_date)
        if end_max < start_min:
            raise ValueError("El fin conocido no puede preceder al inicio")
        return self


class DeclarePatientMedicationPayload(DeclaredMedicationFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class UpdatePatientDeclaredMedicationPayload(DeclaredMedicationFields):
    medication_name: str | None = Field(default=None, min_length=1)
    source_type: MedicationSourceType | None = None
    start_date: ClinicalDate | None = None
    end_date: ClinicalDate | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("medication_name", "source_type"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class InvalidatePatientDeclaredMedicationPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class DeclaredMedicationResponse(DeclaredMedicationFields):
    medication_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    review_status: MedicationReviewStatus
    reviewed_at: AwareDatetime | None
    reviewed_by_user_id: UUID7 | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    @field_serializer(
        "captured_at_local", "created_at", "updated_at", when_used="unless-none"
    )
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class DeclaredMedicationHistoryResponse(DeclaredMedicationFields):
    medication_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    review_status: MedicationReviewStatus
    reviewed_at: AwareDatetime | None
    reviewed_by_user_id: UUID7 | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int

    @field_serializer("captured_at_local", "changed_at", when_used="unless-none")
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class DeclaredMedicationQuery(PageQuery):
    record_status: Literal["valid", "entered-in-error"] | None = None
    review_status: MedicationReviewStatus | None = None
    source_type: MedicationSourceType | None = None


__all__ = [
    "DeclaredMedicationFields",
    "DeclaredMedicationHistoryResponse",
    "DeclaredMedicationQuery",
    "DeclaredMedicationResponse",
    "DeclarePatientMedicationPayload",
    "InvalidatePatientDeclaredMedicationPayload",
    "MedicationReviewStatus",
    "MedicationSourceType",
    "UpdatePatientDeclaredMedicationPayload",
]
