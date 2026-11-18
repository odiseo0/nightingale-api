from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery

PlanStatus = Literal["active", "suspended", "closed", "cancelled"]
MeasurementKind = Literal[
    "weight", "temperature", "oxygen_saturation", "heart_rate", "blood_pressure"
]


class CarePlanFields(BaseModel):
    title: str = Field(min_length=1)
    purpose: str | None = Field(default=None, min_length=1)
    start_date: ClinicalDate | None = None
    expected_end_date: ClinicalDate | None = None
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def period_order(self) -> Self:
        if self.start_date is None or self.expected_end_date is None:
            return self
        if self.expected_end_date < self.start_date:
            raise ValueError("El fin previsto no puede preceder al inicio")
        return self


class CreatePatientCarePlanPayload(CarePlanFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None
    condition_id: UUID7 | None = None


class UpdatePatientCarePlanPayload(CarePlanFields):
    title: str | None = Field(default=None, min_length=1)
    purpose: str | None = Field(default=None, min_length=1)
    start_date: ClinicalDate | None = None
    expected_end_date: ClinicalDate | None = None
    plan_status: PlanStatus | None = None
    status_reason: str | None = Field(default=None, min_length=1)
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("title", "plan_status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        if (
            self.plan_status is not None
            and self.plan_status != "active"
            and "status_reason" not in self.model_fields_set
        ):
            raise ValueError("El cambio de estado requiere motivo")

        return self


class InvalidatePatientCarePlanPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class CarePlanResponse(CarePlanFields):
    plan_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    condition_id: UUID7 | None
    plan_status: PlanStatus
    status_reason: str | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class CarePlanHistoryResponse(CarePlanResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class CarePlanQuery(PageQuery):
    plan_status: PlanStatus | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None


__all__ = [
    "CarePlanFields",
    "CarePlanHistoryResponse",
    "CarePlanQuery",
    "CarePlanResponse",
    "CreatePatientCarePlanPayload",
    "InvalidatePatientCarePlanPayload",
    "MeasurementKind",
    "PlanStatus",
    "UpdatePatientCarePlanPayload",
]
