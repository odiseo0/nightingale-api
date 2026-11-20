from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.domain.errors import AccessDenied
from src.api.care_plans.domain.goals import (
    AddCarePlanActionPayload,
    AddCarePlanGoalPayload,
    AddCarePlanReviewPayload,
    CarePlanActionHistoryResponse,
    CarePlanActionResponse,
    CarePlanGoalHistoryResponse,
    CarePlanGoalResponse,
    CarePlanReviewHistoryResponse,
    CarePlanReviewResponse,
    CompleteCarePlanActionPayload,
    EvaluateCarePlanGoalPayload,
    InvalidateCarePlanActionPayload,
    InvalidateCarePlanGoalPayload,
    InvalidateCarePlanReviewPayload,
    UpdateCarePlanActionPayload,
    UpdateCarePlanGoalPayload,
)
from src.api.care_plans.domain.plans import (
    CarePlanHistoryResponse,
    CarePlanResponse,
    CreatePatientCarePlanPayload,
    InvalidatePatientCarePlanPayload,
    UpdatePatientCarePlanPayload,
)
from src.api.care_plans.repository.dao import (
    dao_care_plan_action_histories,
    dao_care_plan_actions,
    dao_care_plan_goal_histories,
    dao_care_plan_goals,
    dao_care_plan_histories,
    dao_care_plan_review_histories,
    dao_care_plan_reviews,
    dao_care_plans,
)
from src.api.care_plans.repository.models import (
    CarePlan,
    CarePlanAction,
    CarePlanActionHistory,
    CarePlanGoal,
    CarePlanGoalHistory,
    CarePlanHistory,
    CarePlanReview,
    CarePlanReviewHistory,
)
from src.api.encounters.application.encounters_cases import valid_encounter_for_record
from src.api.patients.application.patients_cases import (
    clinical_server_time,
    lock_clinical_patient,
)
from src.core import Err, Ok, Result
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

PLAN_ACTIONS = ("CreatePatientCarePlan",)
GOAL_ACTIONS = ("AddCarePlanGoal",)
ACTION_ACTIONS = ("AddCarePlanAction",)
REVIEW_ACTIONS = ("AddCarePlanReview",)


def plan_response(row: CarePlan) -> CarePlanResponse:
    return CarePlanResponse(
        plan_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        condition_id=row.condition_id,
        title=row.title,
        purpose=row.purpose,
        start_date=row.start_date,
        expected_end_date=row.expected_end_date,
        plan_status=row.plan_status,
        status_reason=row.status_reason,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def goal_response(row: CarePlanGoal) -> CarePlanGoalResponse:
    return CarePlanGoalResponse(
        goal_id=row.id,
        plan_id=row.plan_id,
        patient_id=row.patient_id,
        description=row.description,
        goal_kind=row.goal_kind,
        measurement_kind=row.measurement_kind,
        reference_description=row.reference_description,
        expected_result=row.expected_result,
        target_value=row.target_value,
        unit=row.unit,
        due_date=row.due_date,
        evaluation_status=row.evaluation_status,
        evaluated_at=row.evaluated_at,
        evaluated_by_user_id=row.evaluated_by_user_id,
        evaluation_note=row.evaluation_note,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def action_response(row: CarePlanAction) -> CarePlanActionResponse:
    return CarePlanActionResponse(
        action_id=row.id,
        plan_id=row.plan_id,
        goal_id=row.goal_id,
        patient_id=row.patient_id,
        description=row.description,
        responsible_user_id=row.responsible_user_id,
        due_date=row.due_date,
        completion_status=row.completion_status,
        completed_at=row.completed_at,
        completion_note=row.completion_note,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def review_response(row: CarePlanReview) -> CarePlanReviewResponse:
    return CarePlanReviewResponse(
        review_id=row.id,
        plan_id=row.plan_id,
        patient_id=row.patient_id,
        reviewed_at=row.reviewed_at,
        summary=row.summary,
        findings=row.findings,
        next_review_date=row.next_review_date,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def plan_history_response(row: CarePlanHistory) -> CarePlanHistoryResponse:
    return CarePlanHistoryResponse(
        **plan_response(row).model_dump(),
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


def goal_history_response(row: CarePlanGoalHistory) -> CarePlanGoalHistoryResponse:
    return CarePlanGoalHistoryResponse(
        **goal_response(row).model_dump(),
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


def action_history_response(
    row: CarePlanActionHistory,
) -> CarePlanActionHistoryResponse:
    return CarePlanActionHistoryResponse(
        **action_response(row).model_dump(),
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


def review_history_response(
    row: CarePlanReviewHistory,
) -> CarePlanReviewHistoryResponse:
    return CarePlanReviewHistoryResponse(
        **review_response(row).model_dump(),
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


async def apply_care_plan_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.care_plans != "read_write":
        return Err(AccessDenied())

    if action in PLAN_ACTIONS or action in (
        "UpdatePatientCarePlan",
        "InvalidatePatientCarePlan",
    ):
        return await _apply_plan(
            db, context, action, entity_key, expected_version, payload, operation_id
        )

    if action in GOAL_ACTIONS or action in (
        "UpdateCarePlanGoal",
        "EvaluateCarePlanGoal",
        "InvalidateCarePlanGoal",
    ):
        return await _apply_goal(
            db, context, action, entity_key, expected_version, payload, operation_id
        )

    if action in ACTION_ACTIONS or action in (
        "UpdateCarePlanAction",
        "CompleteCarePlanAction",
        "InvalidateCarePlanAction",
    ):
        return await _apply_action(
            db, context, action, entity_key, expected_version, payload, operation_id
        )

    if action in REVIEW_ACTIONS or action == "InvalidateCarePlanReview":
        return await _apply_review(
            db, context, action, entity_key, expected_version, payload, operation_id
        )

    return Err(AccountRuleError("UNSUPPORTED_OPERATION"))


async def _plan_for_write(
    db: AsyncSession, context: AccountContext, plan_id: UUID, patient_id: UUID
) -> CarePlan | EmptyType:
    plan = await dao_care_plans.get_by(db, where={"account_id": context.account.id, "id": plan_id}, execution_options={"populate_existing": True})

    if plan is Empty or plan.patient_id != patient_id:
        return Empty

    return plan


async def _apply_plan(
    db, context, action, entity_key, expected_version, payload, operation_id
):
    if action == "CreatePatientCarePlan":
        if not isinstance(payload, CreatePatientCarePlanPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if await dao_care_plans.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await lock_clinical_patient(db, context.account.id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = CarePlan(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            condition_id=payload.condition_id,
            **payload.model_dump(
                exclude={"patient_id", "encounter_id", "condition_id"}
            ),
            plan_status="active",
            status_reason=None,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_care_plans.add(db, row)
        event = "created"
    else:
        row = await dao_care_plans.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidatePatientCarePlan":
            if not isinstance(payload, InvalidatePatientCarePlanPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdatePatientCarePlan":
            if not isinstance(payload, UpdatePatientCarePlanPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)

            if (
                row.plan_status in ("closed", "cancelled")
                and changes.get("plan_status", row.plan_status) != row.plan_status
            ):
                return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))

            for name, value in changes.items():
                setattr(row, name, value)

            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_care_plans.flush(db)

    await dao_care_plan_histories.add(
        db,
        CarePlanHistory(
            account_id=row.account_id,
            id=row.id,
            **plan_response(row).model_dump(
                exclude={"plan_id", "version", "created_at", "updated_at"}
            ),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = plan_response(row)
    from src.api.clinical_records.application.timeline_cases import (
        _date_precision,
        project_stage3_entry,
    )

    occurrence_date, date_precision = _date_precision(row.start_date)
    await project_stage3_entry(
        db,
        row.account_id,
        patient_id=row.patient_id,
        entry_type="care_plan",
        entry_id=row.id,
        source_section="care_plans",
        occurrence_date=occurrence_date,
        occurred_at=row.date_updated,
        date_precision=date_precision,
        accepted_at=row.date_updated,
        entity_version=row.version,
        record_status=row.record_status,
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "care_plan",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_care_plans",
                )
            ],
            False,
        )
    )


async def _apply_goal(
    db, context, action, entity_key, expected_version, payload, operation_id
):
    if action == "AddCarePlanGoal":
        if not isinstance(payload, AddCarePlanGoalPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_care_plan_goals.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True})
            is not Empty
        ):
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await _plan_for_write(db, context, payload.plan_id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = CarePlanGoal(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            plan_id=payload.plan_id,
            **payload.model_dump(exclude={"plan_id", "patient_id"}),
            evaluation_status="pending",
            evaluated_at=None,
            evaluated_by_user_id=None,
            evaluation_note=None,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_care_plan_goals.add(db, row)
        event = "created"
    else:
        row = await dao_care_plan_goals.get_by(
            db, where={"account_id": context.account.id, "id": entity_key},
            for_update=True, execution_options={"populate_existing": True}
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateCarePlanGoal":
            if not isinstance(payload, InvalidateCarePlanGoalPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "EvaluateCarePlanGoal":
            if not isinstance(payload, EvaluateCarePlanGoalPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if row.evaluation_status == payload.evaluation_status:
                return Err(AccountRuleError("NO_CHANGES", row.version))

            evaluated_at = await clinical_server_time(db)
            row.evaluation_status = payload.evaluation_status
            row.evaluated_at = evaluated_at
            row.evaluated_by_user_id = context.actor.user_id
            row.evaluation_note = payload.note
            event = "updated"
        elif action == "UpdateCarePlanGoal":
            if not isinstance(payload, UpdateCarePlanGoalPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)

            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))

            for name, value in changes.items():
                setattr(row, name, value)

            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_care_plan_goals.flush(db)

    await dao_care_plan_goal_histories.add(
        db,
        CarePlanGoalHistory(
            account_id=row.account_id,
            id=row.id,
            **goal_response(row).model_dump(
                exclude={"goal_id", "version", "created_at", "updated_at"}
            ),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = goal_response(row)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "care_plan_goal",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_care_plans",
                )
            ],
            False,
        )
    )


async def _apply_action(
    db, context, action, entity_key, expected_version, payload, operation_id
):
    if action == "AddCarePlanAction":
        if not isinstance(payload, AddCarePlanActionPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_care_plan_actions.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True})
            is not Empty
        ):
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await _plan_for_write(db, context, payload.plan_id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        if payload.goal_id is not None:
            goal = await dao_care_plan_goals.get_by(
                db, where={"account_id": context.account.id, "id": payload.goal_id},
                execution_options={"populate_existing": True}
            )
            if goal is Empty or goal.plan_id != payload.plan_id:
                return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = CarePlanAction(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            plan_id=payload.plan_id,
            goal_id=payload.goal_id,
            **payload.model_dump(exclude={"plan_id", "patient_id", "goal_id"}),
            completion_status="not_completed",
            completed_at=None,
            completion_note=None,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_care_plan_actions.add(db, row)
        event = "created"
    else:
        row = await dao_care_plan_actions.get_by(
            db, where={"account_id": context.account.id, "id": entity_key},
            for_update=True, execution_options={"populate_existing": True}
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateCarePlanAction":
            if not isinstance(payload, InvalidateCarePlanActionPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "CompleteCarePlanAction":
            if not isinstance(payload, CompleteCarePlanActionPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if row.completion_status == "completed":
                return Err(AccountRuleError("NO_CHANGES", row.version))

            completed_at = payload.completed_at or await clinical_server_time(db)
            row.completion_status = "completed"
            row.completed_at = completed_at
            row.completion_note = payload.completion_note
            event = "updated"
        elif action == "UpdateCarePlanAction":
            if not isinstance(payload, UpdateCarePlanActionPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)

            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))

            for name, value in changes.items():
                setattr(row, name, value)

            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_care_plan_actions.flush(db)

    await dao_care_plan_action_histories.add(
        db,
        CarePlanActionHistory(
            account_id=row.account_id,
            id=row.id,
            **action_response(row).model_dump(
                exclude={"action_id", "version", "created_at", "updated_at"}
            ),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = action_response(row)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "care_plan_action",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_care_plans",
                )
            ],
            False,
        )
    )


async def _apply_review(
    db, context, action, entity_key, expected_version, payload, operation_id
):
    if action == "AddCarePlanReview":
        if not isinstance(payload, AddCarePlanReviewPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_care_plan_reviews.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True})
            is not Empty
        ):
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await _plan_for_write(db, context, payload.plan_id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = CarePlanReview(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            plan_id=payload.plan_id,
            reviewed_at=payload.reviewed_at or now,
            summary=payload.summary,
            findings=payload.findings,
            next_review_date=payload.next_review_date,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_care_plan_reviews.add(db, row)
        event = "created"
    elif action == "InvalidateCarePlanReview":
        row = await dao_care_plan_reviews.get_by(
            db, where={"account_id": context.account.id, "id": entity_key},
            for_update=True, execution_options={"populate_existing": True}
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if not isinstance(payload, InvalidateCarePlanReviewPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        row.record_status = "entered-in-error"
        row.correction_reason = payload.correction_reason
        row.updated_by_user_id = context.actor.user_id
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_care_plan_reviews.flush(db)
        event = "invalidated"
    else:
        return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

    await dao_care_plan_review_histories.add(
        db,
        CarePlanReviewHistory(
            account_id=row.account_id,
            id=row.id,
            **review_response(row).model_dump(
                exclude={"review_id", "version", "created_at", "updated_at"}
            ),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = review_response(row)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "care_plan_review",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_care_plans",
                )
            ],
            False,
        )
    )
