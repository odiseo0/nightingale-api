from typing import Literal

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.api.clinical_records.domain.clinical import ClinicalSourceType
from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery

type AllergyType = Literal["allergy", "intolerance", "unknown"]
type AllergyClinicalStatus = Literal["active", "inactive", "resolved"]
type AllergyVerificationStatus = Literal[
    "unconfirmed", "presumed", "confirmed", "refuted", "entered-in-error"
]


class AllergyFields(BaseModel):
    substance: str = Field(min_length=1)
    type: AllergyType = "unknown"
    reaction_description: str | None = Field(default=None, min_length=1)
    clinical_status: AllergyClinicalStatus = "active"
    verification_status: AllergyVerificationStatus = "unconfirmed"
    onset_date: ClinicalDate | None = None
    last_occurrence_date: ClinicalDate | None = None
    source_type: ClinicalSourceType = "unknown"
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CreatePatientAllergyIntolerancePayload(AllergyFields):
    patient_id: UUID7

    @field_validator("verification_status")
    @classmethod
    def no_initial_invalidation(cls, value: AllergyVerificationStatus):
        if value == "entered-in-error":
            raise ValueError("La anulación requiere su acción específica")

        return value


class UpdatePatientAllergyIntolerancePayload(AllergyFields):
    substance: str | None = Field(default=None, min_length=1)
    type: AllergyType | None = None
    clinical_status: AllergyClinicalStatus | None = None
    verification_status: AllergyVerificationStatus | None = None
    source_type: ClinicalSourceType | None = None

    @field_validator("verification_status")
    @classmethod
    def no_invalidation_through_patch(cls, value: AllergyVerificationStatus | None):
        if value == "entered-in-error":
            raise ValueError("La anulación requiere su acción específica")

        return value

    @model_validator(mode="after")
    def present_fields(self):
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in (
            "substance",
            "type",
            "clinical_status",
            "verification_status",
            "source_type",
        ):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class InvalidatePatientAllergyIntolerancePayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class PatientAllergyIntoleranceResponse(AllergyFields):
    allergy_id: UUID7
    patient_id: UUID7
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class PatientAllergyIntoleranceHistoryResponse(AllergyFields):
    allergy_id: UUID7
    patient_id: UUID7
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int


class AllergyQuery(PageQuery):
    clinical_status: AllergyClinicalStatus | None = None
    verification_status: AllergyVerificationStatus | None = None
    type: AllergyType | None = None
    include_entered_in_error: bool = False
