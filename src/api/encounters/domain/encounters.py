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
from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant

type RecordStatus = Literal["valid", "entered-in-error"]


class EncounterFields(BaseModel):
    reason: str | None = Field(default=None, min_length=1)
    reason_source_type: ClinicalSourceType = "unknown"
    history_present_illness: str | None = Field(default=None, min_length=1)
    findings: str | None = Field(default=None, min_length=1)
    assessment: str | None = Field(default=None, min_length=1)
    indications: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CreatePatientEncounterPayload(EncounterFields):
    patient_id: UUID7
    appointment_id: UUID7 | None = None
    attending_professional_id: UUID7
    assistant_user_id: UUID7 | None = None
    occurred_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    captured_at_local: AwareDatetime | None = None


class UpdatePatientEncounterPayload(EncounterFields):
    reason_source_type: ClinicalSourceType | None = None
    occurred_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    captured_at_local: AwareDatetime | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        if (
            "reason_source_type" in self.model_fields_set
            and self.reason_source_type is None
        ):
            raise ValueError("La fuente presente no puede ser nula")

        if "occurred_at" in self.model_fields_set and self.occurred_at is None:
            raise ValueError("El instante presente no puede ser nulo")

        return self


class InvalidatePatientEncounterPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientEncounterResponse(EncounterFields):
    encounter_id: UUID7
    patient_id: UUID7
    appointment_id: UUID7 | None
    attending_professional_id: UUID7
    assistant_user_id: UUID7 | None
    occurred_at: AwareDatetime
    ended_at: AwareDatetime | None
    captured_at_local: AwareDatetime | None
    record_status: RecordStatus
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    @field_serializer(
        "occurred_at",
        "ended_at",
        "captured_at_local",
        "created_at",
        "updated_at",
        when_used="unless-none",
    )
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class PatientEncounterHistoryResponse(EncounterFields):
    encounter_id: UUID7
    patient_id: UUID7
    appointment_id: UUID7 | None
    attending_professional_id: UUID7
    assistant_user_id: UUID7 | None
    occurred_at: AwareDatetime
    ended_at: AwareDatetime | None
    captured_at_local: AwareDatetime | None
    record_status: RecordStatus
    correction_reason: str | None
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int

    @field_serializer(
        "occurred_at",
        "ended_at",
        "captured_at_local",
        "changed_at",
        when_used="unless-none",
    )
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class EncounterQuery(PageQuery):
    record_status: RecordStatus | None = None
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


class LastVisitResponse(BaseModel):
    encounter_id: UUID7 | None
    occurred_at: AwareDatetime | None
    scope: Literal["account"] = "account"

    @field_serializer("occurred_at", when_used="unless-none")
    def serialize_occurrence(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
