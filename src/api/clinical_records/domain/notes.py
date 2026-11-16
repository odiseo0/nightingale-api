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

from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant


class CreatePatientNotePayload(BaseModel):
    patient_id: UUID7
    encounter_id: UUID7 | None = None
    body: str = Field(min_length=1)
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid")


class UpdatePatientNotePayload(BaseModel):
    body: str | None = Field(default=None, min_length=1)
    captured_at_local: AwareDatetime | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        if "body" in self.model_fields_set and self.body is None:
            raise ValueError("El cuerpo presente no puede ser nulo")

        return self


class InvalidatePatientNotePayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientNoteResponse(BaseModel):
    note_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    body: str
    captured_at_local: AwareDatetime | None
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


class PatientNoteHistoryResponse(BaseModel):
    note_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    body: str
    captured_at_local: AwareDatetime | None
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


class NoteQuery(PageQuery):
    record_status: Literal["valid", "entered-in-error"] | None = None
    encounter_id: UUID7 | None = None
