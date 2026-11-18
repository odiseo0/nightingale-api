from typing import Annotated, Literal, Self

from pydantic import UUID7, AfterValidator, AwareDatetime, ConfigDict, Field, field_validator, model_validator

from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery

Surface = Literal[
    "vestibular", "palatina", "lingual", "mesial", "distal",
    "oclusal", "incisal", "cervical",
]
FindingKind = Literal[
    "healthy", "caries", "missing", "filling", "crown", "fracture", "other",
]
TreatmentKind = Literal["cleaning", "filling", "crown", "extraction", "other"]
FindingStatus = Literal["active", "resolved"]
TreatmentStatus = Literal["planned", "performed"]


def _valid_fdi(value: int) -> bool:
    tooth = value % 10
    quadrant = value // 10
    if 1 <= quadrant <= 4:
        return 1 <= tooth <= 8
    if 5 <= quadrant <= 8:
        return 1 <= tooth <= 5
    return False


def _validate_fdi(value: int) -> int:
    if not _valid_fdi(value):
        raise ValueError("La pieza debe usar numeración FDI válida")
    return value


ToothFdi = Annotated[int, AfterValidator(_validate_fdi)]


class DentalFindingFields(BaseModel):
    tooth_fdi: ToothFdi
    surface: Surface | None = None
    finding_kind: FindingKind
    note: str | None = Field(default=None, min_length=1)
    recorded_date: ClinicalDate | None = None
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)


class RecordDentalFindingPayload(DentalFindingFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class UpdateDentalFindingPayload(DentalFindingFields):
    finding_kind: FindingKind | None = None
    note: str | None = Field(default=None, min_length=1)
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("tooth_fdi", "finding_kind"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class ResolveDentalFindingPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class InvalidateDentalFindingPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class DentalFindingResponse(DentalFindingFields):
    finding_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    finding_status: FindingStatus
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class DentalFindingHistoryResponse(DentalFindingResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class DentalTreatmentFields(BaseModel):
    treatment_kind: TreatmentKind
    note: str | None = Field(default=None, min_length=1)
    performed_date: ClinicalDate | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)


class AddDentalTreatmentPayload(DentalTreatmentFields):
    finding_id: UUID7
    patient_id: UUID7


class UpdateDentalTreatmentPayload(DentalTreatmentFields):
    treatment_kind: TreatmentKind | None = None
    note: str | None = Field(default=None, min_length=1)
    performed_date: ClinicalDate | None = None
    treatment_status: TreatmentStatus | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def performed_needs_date(self) -> Self:
        if self.treatment_status == "performed" and self.performed_date is None:
            raise ValueError("La actuación realizada requiere fecha")
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")
        return self


class InvalidateDentalTreatmentPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class DentalTreatmentResponse(DentalTreatmentFields):
    treatment_id: UUID7
    finding_id: UUID7
    patient_id: UUID7
    treatment_status: TreatmentStatus
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class DentalTreatmentHistoryResponse(DentalTreatmentResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class DentalFindingQuery(PageQuery):
    tooth_fdi: int | None = None
    finding_kind: FindingKind | None = None
    finding_status: FindingStatus | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None

    @field_validator("tooth_fdi")
    @classmethod
    def fdi_valid(cls, value: int | None) -> int | None:
        if value is not None and not _valid_fdi(value):
            raise ValueError("La pieza debe usar numeración FDI válida")
        return value


__all__ = [
    "AddDentalTreatmentPayload",
    "DentalFindingFields",
    "DentalFindingHistoryResponse",
    "DentalFindingQuery",
    "DentalFindingResponse",
    "DentalTreatmentFields",
    "DentalTreatmentHistoryResponse",
    "DentalTreatmentResponse",
    "FindingKind",
    "FindingStatus",
    "InvalidateDentalFindingPayload",
    "InvalidateDentalTreatmentPayload",
    "RecordDentalFindingPayload",
    "ResolveDentalFindingPayload",
    "Surface",
    "ToothFdi",
    "TreatmentKind",
    "TreatmentStatus",
    "UpdateDentalFindingPayload",
    "UpdateDentalTreatmentPayload",
]
