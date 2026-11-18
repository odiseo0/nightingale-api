from decimal import Decimal
from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.api.care_plans.domain.plans import MeasurementKind
from src.api.clinical_records.domain.conditions import ClinicalDate
from src.core.schema import BaseModel, PageQuery

GoalKind = Literal["narrative", "measurable"]
EvaluationStatus = Literal["pending", "achieved", "not_achieved"]
CompletionStatus = Literal["not_completed", "completed"]


class CarePlanGoalFields(BaseModel):
    description: str = Field(min_length=1)
    goal_kind: GoalKind
    measurement_kind: MeasurementKind | None = None
    reference_description: str | None = Field(default=None, min_length=1)
    expected_result: str | None = Field(default=None, min_length=1)
    target_value: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1)
    due_date: ClinicalDate | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def measurable_needs_reference(self) -> Self:
        if self.goal_kind == "measurable" and (
            self.target_value is None
            and self.unit is None
            and self.measurement_kind is None
        ):
            raise ValueError(
                "El objetivo medible requiere meta, unidad o medición"
            )
        return self


class AddCarePlanGoalPayload(CarePlanGoalFields):
    plan_id: UUID7
    patient_id: UUID7


class UpdateCarePlanGoalPayload(CarePlanGoalFields):
    description: str | None = Field(default=None, min_length=1)
    goal_kind: GoalKind | None = None
    measurement_kind: MeasurementKind | None = None
    reference_description: str | None = Field(default=None, min_length=1)
    expected_result: str | None = Field(default=None, min_length=1)
    target_value: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1)
    due_date: ClinicalDate | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("description", "goal_kind"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class EvaluateCarePlanGoalPayload(BaseModel):
    evaluation_status: Literal["achieved", "not_achieved"]
    note: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class InvalidateCarePlanGoalPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class CarePlanGoalResponse(CarePlanGoalFields):
    goal_id: UUID7
    plan_id: UUID7
    patient_id: UUID7
    evaluation_status: EvaluationStatus
    evaluated_at: AwareDatetime | None
    evaluated_by_user_id: UUID7 | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class CarePlanGoalHistoryResponse(CarePlanGoalResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class CarePlanActionFields(BaseModel):
    description: str = Field(min_length=1)
    responsible_user_id: UUID7 | None = None
    due_date: ClinicalDate | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)


class AddCarePlanActionPayload(CarePlanActionFields):
    plan_id: UUID7
    patient_id: UUID7
    goal_id: UUID7 | None = None


class UpdateCarePlanActionPayload(CarePlanActionFields):
    description: str | None = Field(default=None, min_length=1)
    responsible_user_id: UUID7 | None = None
    due_date: ClinicalDate | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        if "description" in self.model_fields_set and self.description is None:
            raise ValueError("Un campo presente no puede ser nulo")

        return self


class CompleteCarePlanActionPayload(BaseModel):
    completed_at: AwareDatetime | None = None
    completion_note: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class InvalidateCarePlanActionPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class CarePlanActionResponse(CarePlanActionFields):
    action_id: UUID7
    plan_id: UUID7
    goal_id: UUID7 | None
    patient_id: UUID7
    completion_status: CompletionStatus
    completed_at: AwareDatetime | None
    completion_note: str | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class CarePlanActionHistoryResponse(CarePlanActionResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class AddCarePlanReviewPayload(BaseModel):
    plan_id: UUID7
    patient_id: UUID7
    reviewed_at: AwareDatetime | None = None
    summary: str = Field(min_length=1)
    findings: str | None = Field(default=None, min_length=1)
    next_review_date: ClinicalDate | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)


class InvalidateCarePlanReviewPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class CarePlanReviewResponse(BaseModel):
    review_id: UUID7
    plan_id: UUID7
    patient_id: UUID7
    reviewed_at: AwareDatetime
    summary: str
    findings: str | None
    next_review_date: ClinicalDate | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CarePlanReviewHistoryResponse(CarePlanReviewResponse):
    action: Literal["created", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class CarePlanGoalQuery(PageQuery):
    goal_kind: GoalKind | None = None
    evaluation_status: EvaluationStatus | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None


class CarePlanActionQuery(PageQuery):
    completion_status: CompletionStatus | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None


__all__ = [
    "AddCarePlanActionPayload",
    "AddCarePlanGoalPayload",
    "AddCarePlanReviewPayload",
    "CarePlanActionFields",
    "CarePlanActionHistoryResponse",
    "CarePlanActionQuery",
    "CarePlanActionResponse",
    "CarePlanGoalFields",
    "CarePlanGoalHistoryResponse",
    "CarePlanGoalQuery",
    "CarePlanGoalResponse",
    "CarePlanReviewHistoryResponse",
    "CarePlanReviewResponse",
    "CompleteCarePlanActionPayload",
    "CompletionStatus",
    "EvaluationStatus",
    "EvaluateCarePlanGoalPayload",
    "GoalKind",
    "InvalidateCarePlanActionPayload",
    "InvalidateCarePlanGoalPayload",
    "InvalidateCarePlanReviewPayload",
    "UpdateCarePlanActionPayload",
    "UpdateCarePlanGoalPayload",
]
