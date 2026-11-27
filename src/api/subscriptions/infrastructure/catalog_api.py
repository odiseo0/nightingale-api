from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.catalog_cases import (
    PlanNotFound,
    PlanRetired,
    VersionConflict,
    create_plan_version,
    list_plans,
    retire_plan,
)
from src.api.subscriptions.domain.plans import (
    OperatorPlanPage,
    OperatorPlanResponse,
    PlanRetirementRequest,
    PlanVersionCreateRequest,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/operator/plans",
    tags=["operator-subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("", operation_id="listOperatorPlans")
async def list_operator_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorPlanPage:
    result = await list_plans(db, authorization.credentials if authorization else None)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case unexpected:
            assert_never(unexpected)


@router.post("/{code}/versions", operation_id="createOperatorPlanVersion", status_code=201)
async def create_operator_plan_version(
    code: str,
    payload: PlanVersionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorPlanResponse:
    result = await create_plan_version(
        db, authorization.credentials if authorization else None, code, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(PlanNotFound()):
            raise HTTPException(404)
        case Err(PlanRetired() | VersionConflict()):
            raise HTTPException(409)
        case unexpected:
            assert_never(unexpected)


@router.post("/{code}/retirement", operation_id="retireOperatorPlan")
async def retire_operator_plan(
    code: str,
    payload: PlanRetirementRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorPlanResponse:
    result = await retire_plan(
        db, authorization.credentials if authorization else None, code, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(PlanNotFound()):
            raise HTTPException(404)
        case Err(PlanRetired() | VersionConflict()):
            raise HTTPException(409)
        case unexpected:
            assert_never(unexpected)
