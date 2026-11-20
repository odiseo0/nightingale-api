from decimal import Decimal
from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery


class SpecialtyRecordValue(BaseModel):
    field_key: str = Field(min_length=1)
    value_text: str | None = Field(default=None, min_length=1)
    value_number: Decimal | None = None
    value_boolean: bool | None = None
    value_date: ClinicalDate | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def single_typed_value(self) -> Self:
        present = [
            value
            for value in (
                self.value_text,
                self.value_number,
                self.value_boolean,
                self.value_date,
            )
            if value is not None
        ]

        if len(present) != 1:
            raise ValueError("Cada valor admite exactamente un dato tipado")

        return self


class SpecialtyRecordFields(BaseModel):
    template_id: UUID7
    recorded_at: AwareDatetime | None = None
    values: list[SpecialtyRecordValue]

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CaptureSpecialtyRecordPayload(SpecialtyRecordFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class UpdateSpecialtyRecordPayload(BaseModel):
    recorded_at: AwareDatetime | None = None
    values: list[SpecialtyRecordValue] | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class InvalidateSpecialtyRecordPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class SpecialtyRecordValueResponse(SpecialtyRecordValue):
    pass


class SpecialtyRecordResponse(BaseModel):
    record_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    template_id: UUID7
    template_version: int
    recorded_at: AwareDatetime
    values: list[SpecialtyRecordValueResponse]
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    model_config = ConfigDict(extra="forbid", validate_default=True)


class SpecialtyRecordHistoryResponse(SpecialtyRecordResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class SpecialtyRecordQuery(PageQuery):
    template_id: UUID7 | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None
