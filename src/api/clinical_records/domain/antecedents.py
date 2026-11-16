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

from src.api.clinical_records.domain.clinical import ClinicalSourceType
from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant

type AntecedentCategory = Literal["personal", "family", "other"]


class AntecedentFields(BaseModel):
    category: AntecedentCategory
    content: str = Field(min_length=1)
    related_person_description: str | None = Field(default=None, min_length=1)
    occurrence_date: ClinicalDate | None = None
    source_type: ClinicalSourceType = "unknown"
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def related_person(self) -> Self:
        if self.category == "family" and self.related_person_description is None:
            raise ValueError("El antecedente familiar requiere la persona relacionada")

        return self


class CreatePatientAntecedentPayload(AntecedentFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class UpdatePatientAntecedentPayload(AntecedentFields):
    category: AntecedentCategory | None = None
    content: str | None = Field(default=None, min_length=1)
    source_type: ClinicalSourceType | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("category", "content", "source_type"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class InvalidatePatientAntecedentPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientAntecedentResponse(AntecedentFields):
    antecedent_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
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


class PatientAntecedentHistoryResponse(AntecedentFields):
    antecedent_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
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


class AntecedentQuery(PageQuery):
    category: AntecedentCategory | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None
