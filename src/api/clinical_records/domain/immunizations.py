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

type RecordKind = Literal["administered_here", "reported", "unknown"]


class ImmunizationFields(BaseModel):
    vaccine_name: str = Field(min_length=1)
    occurrence_date: ClinicalDate
    record_kind: RecordKind = "unknown"
    source_type: ClinicalSourceType = "unknown"
    captured_at_local: AwareDatetime | None = None
    product_name: str | None = Field(default=None, min_length=1)
    dose_description: str | None = Field(default=None, min_length=1)
    lot_number: str | None = Field(default=None, min_length=1)
    route: str | None = Field(default=None, min_length=1)
    body_site: str | None = Field(default=None, min_length=1)
    location_text: str | None = Field(default=None, min_length=1)
    administrator_name: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class RecordPatientImmunizationPayload(ImmunizationFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None

    @model_validator(mode="after")
    def administered_link(self) -> Self:
        if self.record_kind == "administered_here" and self.encounter_id is None:
            raise ValueError("La administración local requiere una atención")

        return self


class UpdatePatientImmunizationPayload(ImmunizationFields):
    vaccine_name: str | None = Field(default=None, min_length=1)
    occurrence_date: ClinicalDate | None = None
    record_kind: RecordKind | None = None
    source_type: ClinicalSourceType | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("vaccine_name", "occurrence_date", "record_kind", "source_type"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class InvalidatePatientImmunizationPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientImmunizationResponse(ImmunizationFields):
    immunization_id: UUID7
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


class PatientImmunizationHistoryResponse(ImmunizationFields):
    immunization_id: UUID7
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


class ImmunizationQuery(PageQuery):
    record_kind: RecordKind | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None
