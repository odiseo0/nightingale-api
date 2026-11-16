import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    UUID7,
    AfterValidator,
    AwareDatetime,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.api.clinical_records.domain.clinical import ClinicalSourceType
from src.core.schema import BaseModel, PageQuery


class ClinicalDateValue:
    @classmethod
    def validate(cls, value: str) -> str:
        match = re.fullmatch(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", value)
        if match is None:
            raise ValueError("La fecha clínica debe usar YYYY, YYYY-MM o YYYY-MM-DD")

        year, month, day = match.groups()
        date(int(year), int(month or 1), int(day or 1))
        return value


type ClinicalDate = Annotated[str, AfterValidator(ClinicalDateValue.validate)]
type ConditionClinicalStatus = Literal[
    "active", "recurrence", "relapse", "inactive", "remission", "resolved", "unknown"
]
type ConditionVerificationStatus = Literal[
    "unconfirmed",
    "provisional",
    "differential",
    "confirmed",
    "refuted",
    "entered-in-error",
]


class ConditionFields(BaseModel):
    name: str = Field(min_length=1)
    clinical_status: ConditionClinicalStatus = "active"
    verification_status: ConditionVerificationStatus = "unconfirmed"
    onset_date: ClinicalDate | None = None
    abatement_date: ClinicalDate | None = None
    source_type: ClinicalSourceType = "unknown"
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CreatePatientConditionPayload(ConditionFields):
    patient_id: UUID7

    @field_validator("verification_status")
    @classmethod
    def no_initial_invalidation(cls, value: ConditionVerificationStatus):
        if value == "entered-in-error":
            raise ValueError("La anulación requiere su acción específica")

        return value


class UpdatePatientConditionPayload(ConditionFields):
    name: str | None = Field(default=None, min_length=1)
    clinical_status: ConditionClinicalStatus | None = None
    verification_status: ConditionVerificationStatus | None = None
    source_type: ClinicalSourceType | None = None

    @field_validator("verification_status")
    @classmethod
    def no_invalidation_through_patch(cls, value: ConditionVerificationStatus | None):
        if value == "entered-in-error":
            raise ValueError("La anulación requiere su acción específica")

        return value

    @model_validator(mode="after")
    def present_fields(self):
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("name", "clinical_status", "verification_status", "source_type"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class InvalidatePatientConditionPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class SetPatientClinicalSectionReviewPayload(BaseModel):
    section: Literal["conditions", "allergies"]
    information_status: Literal["not_asked", "unknown", "none_known", "has_entries"]
    source_type: ClinicalSourceType = "unknown"

    model_config = ConfigDict(extra="forbid", validate_default=True)


class PatientConditionResponse(ConditionFields):
    condition_id: UUID7
    patient_id: UUID7
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class PatientConditionHistoryResponse(ConditionFields):
    condition_id: UUID7
    patient_id: UUID7
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int


class ConditionQuery(PageQuery):
    clinical_status: ConditionClinicalStatus | None = None
    verification_status: ConditionVerificationStatus | None = None
    include_entered_in_error: bool = False


class ClinicalSectionReviewResponse(BaseModel):
    patient_id: UUID7
    section: Literal["conditions", "allergies"]
    information_status: Literal[
        "not_recorded", "not_asked", "unknown", "none_known", "has_entries"
    ]
    source_type: ClinicalSourceType | None
    reviewed_by_user_id: UUID7 | None
    reviewed_at: AwareDatetime | None
    active_count: int = Field(ge=0)
    version: int = Field(ge=0)
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class ClinicalSectionReviewHistoryResponse(BaseModel):
    patient_id: UUID7
    section: Literal["conditions", "allergies"]
    information_status: Literal["not_asked", "unknown", "none_known", "has_entries"]
    source_type: ClinicalSourceType
    action: Literal["set", "derived"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime
    version: int
