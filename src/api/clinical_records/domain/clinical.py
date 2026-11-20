from datetime import date
from typing import Literal

from pydantic import UUID7, AwareDatetime, ConfigDict, Field

from src.api.patients.domain.patients import PatientBirthDateChangeResponse
from src.core.schema import BaseModel, PageQuery

type ClinicalSourceType = Literal[
    "patient", "related_person", "professional", "external_document", "unknown"
]
type SexAtBirth = Literal["male", "female", "other", "unknown"]


class SetPatientSexAtBirthPayload(BaseModel):
    sex_at_birth: SexAtBirth | None
    source_type: ClinicalSourceType = "unknown"

    model_config = ConfigDict(extra="forbid", validate_default=True)


class ClinicalProfileResponse(BaseModel):
    patient_id: UUID7
    sex_at_birth: SexAtBirth | None
    source_type: ClinicalSourceType | None
    version: int = Field(ge=0)
    birth_date: date | None = None
    patient_version: int = Field(ge=1)
    age_years: int | None = Field(default=None, ge=0)
    age_as_of: date
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class ClinicalProfileHistoryResponse(BaseModel):
    patient_id: UUID7
    sex_at_birth: SexAtBirth | None
    source_type: ClinicalSourceType
    version: int = Field(ge=1)
    action: Literal["set"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class ClinicalHistoryQuery(PageQuery):
    after_version: int | None = Field(default=None, ge=0)


__all__ = [
    "ClinicalHistoryQuery",
    "ClinicalProfileHistoryResponse",
    "ClinicalProfileResponse",
    "ClinicalSourceType",
    "PatientBirthDateChangeResponse",
    "SetPatientSexAtBirthPayload",
    "SexAtBirth",
]
