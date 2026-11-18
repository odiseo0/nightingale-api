from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.care_plans.application.plan_cases import (
    action_history_response,
    action_response,
    goal_history_response,
    goal_response,
    plan_history_response,
    plan_response,
    review_history_response,
    review_response,
)
from src.api.care_plans.domain.goals import (
    CarePlanActionQuery,
    CarePlanGoalQuery,
)
from src.api.care_plans.domain.plans import CarePlanQuery
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
from src.api.clinical_records.application.access_cases import (
    clinical_page,
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.patients.application.patients_cases import clinical_patient
from src.core import Err, Ok
from src.core.db import transaction
from src.core.schema import PageQuery
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def read_care_plans(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: CarePlanQuery | PageQuery,
    plan_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "care_plans")
        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if plan_id is None:
            if not isinstance(query, CarePlanQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            rows, total = await dao_care_plans.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, plan_response)
            action = "ReadPatientCarePlans"
        else:
            row = await dao_care_plans.scoped(db, account_id, plan_id)
            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            response = plan_response(row)
            action = "ReadPatientCarePlan"

        await record_clinical_read(
            db, scope.value, action, "care_plan", str(plan_id or patient_id)
        )

    return Ok(response)


async def read_care_plan_history(
    db, credential, account_id, patient_id, plan_id, query: ClinicalHistoryQuery
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "care_plans")
        if isinstance(scope, Err):
            return scope

        row = await dao_care_plans.scoped(db, account_id, plan_id)

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_care_plan_histories.page(
            db,
            account_id,
            plan_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(rows, total, plan_history_response)
        await record_clinical_read(
            db, scope.value, "ReadPatientCarePlanHistory", "care_plan", str(plan_id)
        )

    return Ok(response)


_KINDS = {
    "goals": (
        dao_care_plan_goals,
        dao_care_plan_goal_histories,
        goal_response,
        goal_history_response,
        CarePlanGoalQuery,
        "care_plan_goal",
        "ReadPatientCarePlanGoals",
    ),
    "actions": (
        dao_care_plan_actions,
        dao_care_plan_action_histories,
        action_response,
        action_history_response,
        CarePlanActionQuery,
        "care_plan_action",
        "ReadPatientCarePlanActions",
    ),
    "reviews": (
        dao_care_plan_reviews,
        dao_care_plan_review_histories,
        review_response,
        review_history_response,
        PageQuery,
        "care_plan_review",
        "ReadPatientCarePlanReviews",
    ),
}


async def read_care_plan_children(
    db, credential, account_id, patient_id, plan_id, kind, query, child_id=None
):
    dao, history_dao, to_response, to_history, query_type, entity, action_name = _KINDS[
        kind
    ]

    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "care_plans")
        if isinstance(scope, Err):
            return scope

        plan = await dao_care_plans.scoped(db, account_id, plan_id)
        if plan is Empty or plan.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        if child_id is None:

            def extra_where(statement):
                if query_type is not PageQuery and query.record_status is not None:
                    return statement.where(
                        dao.model.record_status == query.record_status
                    )
                return statement.where(dao.model.record_status == "valid")

            rows, total = await dao.page(
                db,
                account_id,
                plan_id,
                (query.page - 1) * query.shows,
                query.shows,
                extra_where=extra_where,
            )
            response = clinical_page(rows, total, to_response)
        else:
            row = await dao.scoped(db, account_id, child_id)
            if row is Empty or row.plan_id != plan_id:
                return Err(AccountObjectNotFound())
            response = to_response(row)

        await record_clinical_read(
            db, scope.value, action_name, entity, str(child_id or plan_id)
        )

    return Ok(response)


async def read_care_plan_child_history(
    db,
    credential,
    account_id,
    patient_id,
    plan_id,
    kind,
    child_id,
    query: ClinicalHistoryQuery,
):
    dao, history_dao, to_response, to_history, query_type, entity, _ = _KINDS[kind]

    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "care_plans")
        if isinstance(scope, Err):
            return scope

        plan = await dao_care_plans.scoped(db, account_id, plan_id)
        if plan is Empty or plan.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        row = await dao.scoped(db, account_id, child_id)
        if row is Empty or row.plan_id != plan_id:
            return Err(AccountObjectNotFound())

        rows, total = await history_dao.page(
            db,
            account_id,
            child_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(rows, total, to_history)
        await record_clinical_read(
            db,
            scope.value,
            f"ReadPatientCarePlan{kind.title().rstrip('s')}History",
            entity,
            str(child_id),
        )

    return Ok(response)
