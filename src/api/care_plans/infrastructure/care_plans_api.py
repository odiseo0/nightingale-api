from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.care_plans.application.read_cases import (
    read_care_plan_child_history,
    read_care_plan_children,
    read_care_plan_history,
    read_care_plans,
)
from src.api.care_plans.domain.goals import (
    CarePlanActionHistoryResponse,
    CarePlanActionQuery,
    CarePlanActionResponse,
    CarePlanGoalHistoryResponse,
    CarePlanGoalQuery,
    CarePlanGoalResponse,
    CarePlanReviewHistoryResponse,
    CarePlanReviewResponse,
)
from src.api.care_plans.domain.plans import (
    CarePlanHistoryResponse,
    CarePlanQuery,
    CarePlanResponse,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-care-plans"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


def _raise(result):
    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get("/care-plans", operation_id="listPatientCarePlans")
async def list_care_plans(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[CarePlanQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanResponse]:
    return _raise(
        await read_care_plans(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            query,
        )
    )


@router.get(
    "/care-plans/{plan_id}",
    operation_id="getPatientCarePlan",
    dependencies=[Depends(no_query_parameters)],
)
async def get_care_plan(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CarePlanResponse:
    return _raise(
        await read_care_plans(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            PageQuery(),
            plan_id,
        )
    )


@router.get("/care-plans/{plan_id}/history", operation_id="listPatientCarePlanHistory")
async def list_care_plan_history(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanHistoryResponse]:
    return _raise(
        await read_care_plan_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            query,
        )
    )


@router.get("/care-plans/{plan_id}/goals", operation_id="listPatientCarePlanGoals")
async def list_care_plan_goals(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    query: Annotated[CarePlanGoalQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanGoalResponse]:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "goals",
            query,
        )
    )


@router.get(
    "/care-plans/{plan_id}/goals/{goal_id}",
    operation_id="getPatientCarePlanGoal",
    dependencies=[Depends(no_query_parameters)],
)
async def get_care_plan_goal(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    goal_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CarePlanGoalResponse:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "goals",
            PageQuery(),
            goal_id,
        )
    )


@router.get(
    "/care-plans/{plan_id}/goals/{goal_id}/history",
    operation_id="listPatientCarePlanGoalHistory",
)
async def list_care_plan_goal_history(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    goal_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanGoalHistoryResponse]:
    return _raise(
        await read_care_plan_child_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "goals",
            goal_id,
            query,
        )
    )


@router.get("/care-plans/{plan_id}/actions", operation_id="listPatientCarePlanActions")
async def list_care_plan_actions(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    query: Annotated[CarePlanActionQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanActionResponse]:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "actions",
            query,
        )
    )


@router.get(
    "/care-plans/{plan_id}/actions/{action_id}",
    operation_id="getPatientCarePlanAction",
    dependencies=[Depends(no_query_parameters)],
)
async def get_care_plan_action(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    action_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CarePlanActionResponse:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "actions",
            PageQuery(),
            action_id,
        )
    )


@router.get(
    "/care-plans/{plan_id}/actions/{action_id}/history",
    operation_id="listPatientCarePlanActionHistory",
)
async def list_care_plan_action_history(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    action_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanActionHistoryResponse]:
    return _raise(
        await read_care_plan_child_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "actions",
            action_id,
            query,
        )
    )


@router.get("/care-plans/{plan_id}/reviews", operation_id="listPatientCarePlanReviews")
async def list_care_plan_reviews(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanReviewResponse]:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "reviews",
            query,
        )
    )


@router.get(
    "/care-plans/{plan_id}/reviews/{review_id}",
    operation_id="getPatientCarePlanReview",
    dependencies=[Depends(no_query_parameters)],
)
async def get_care_plan_review(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    review_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CarePlanReviewResponse:
    return _raise(
        await read_care_plan_children(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "reviews",
            PageQuery(),
            review_id,
        )
    )


@router.get(
    "/care-plans/{plan_id}/reviews/{review_id}/history",
    operation_id="listPatientCarePlanReviewHistory",
)
async def list_care_plan_review_history(
    account_id: UUID7,
    patient_id: UUID7,
    plan_id: UUID7,
    review_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[CarePlanReviewHistoryResponse]:
    return _raise(
        await read_care_plan_child_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            plan_id,
            "reviews",
            review_id,
            query,
        )
    )
