from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class CarePlan(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    condition_id: Mapped[UUID | None]
    title: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[str | None] = mapped_column(Text)
    expected_end_date: Mapped[str | None] = mapped_column(Text)
    plan_status: Mapped[str] = mapped_column(Text, server_default="active")
    status_reason: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class CarePlanHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    condition_id: Mapped[UUID | None]
    title: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[str | None] = mapped_column(Text)
    expected_end_date: Mapped[str | None] = mapped_column(Text)
    plan_status: Mapped[str] = mapped_column(Text)
    status_reason: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class CarePlanGoal(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    description: Mapped[str] = mapped_column(Text)
    goal_kind: Mapped[str] = mapped_column(Text)
    measurement_kind: Mapped[str | None] = mapped_column(Text)
    reference_description: Mapped[str | None] = mapped_column(Text)
    expected_result: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[str | None] = mapped_column(Text)
    evaluation_status: Mapped[str] = mapped_column(Text, server_default="pending")
    evaluated_at: Mapped[datetime | None]
    evaluated_by_user_id: Mapped[UUID | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class CarePlanGoalHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    description: Mapped[str] = mapped_column(Text)
    goal_kind: Mapped[str] = mapped_column(Text)
    measurement_kind: Mapped[str | None] = mapped_column(Text)
    reference_description: Mapped[str | None] = mapped_column(Text)
    expected_result: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[str | None] = mapped_column(Text)
    evaluation_status: Mapped[str] = mapped_column(Text)
    evaluated_at: Mapped[datetime | None]
    evaluated_by_user_id: Mapped[UUID | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class CarePlanAction(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    goal_id: Mapped[UUID | None]
    description: Mapped[str] = mapped_column(Text)
    responsible_user_id: Mapped[UUID | None]
    due_date: Mapped[str | None] = mapped_column(Text)
    completion_status: Mapped[str] = mapped_column(Text, server_default="not_completed")
    completed_at: Mapped[datetime | None]
    completion_note: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class CarePlanActionHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    goal_id: Mapped[UUID | None]
    description: Mapped[str] = mapped_column(Text)
    responsible_user_id: Mapped[UUID | None]
    due_date: Mapped[str | None] = mapped_column(Text)
    completion_status: Mapped[str] = mapped_column(Text)
    completed_at: Mapped[datetime | None]
    completion_note: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class CarePlanReview(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    reviewed_at: Mapped[datetime]
    summary: Mapped[str] = mapped_column(Text)
    findings: Mapped[str | None] = mapped_column(Text)
    next_review_date: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int] = mapped_column(server_default="1")


class CarePlanReviewHistory(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    reviewed_at: Mapped[datetime]
    summary: Mapped[str] = mapped_column(Text)
    findings: Mapped[str | None] = mapped_column(Text)
    next_review_date: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
