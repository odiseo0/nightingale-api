from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.subscription_cases import (
    PlanUnavailable,
    SubscriptionNotFound,
    VersionConflict,
    cancel_for_owner,
    change_plan_for_owner,
    get_subscription,
)
from src.api.subscriptions.domain.subscriptions import (
    CancellationRequest,
    PlanChangeRequest,
    SubscriptionResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/accounts/{account_id}/subscription",
    tags=["subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422)},
)
bearer = HTTPBearer(auto_error=False)


def respond(result):
    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | SubscriptionNotFound()):
            raise HTTPException(404)
        case Err(PlanUnavailable()):
            raise HTTPException(409, detail="PLAN_UNAVAILABLE")
        case Err(VersionConflict()):
            raise HTTPException(409, detail="VERSION_CONFLICT")
        case unexpected:
            assert_never(unexpected)


@router.get("", operation_id="getAccountSubscription")
async def read_account_subscription(
    account_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SubscriptionResponse:
    return respond(
        await get_subscription(
            db, authorization.credentials if authorization else None, account_id
        )
    )


@router.post("/plan-changes", operation_id="changeAccountSubscriptionPlan")
async def change_account_subscription_plan(
    account_id: UUID7,
    payload: PlanChangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SubscriptionResponse:
    return respond(
        await change_plan_for_owner(
            db, authorization.credentials if authorization else None, account_id, payload
        )
    )


@router.post("/cancellation", operation_id="cancelAccountSubscription")
async def cancel_account_subscription(
    account_id: UUID7,
    payload: CancellationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SubscriptionResponse:
    return respond(
        await cancel_for_owner(
            db, authorization.credentials if authorization else None, account_id, payload
        )
    )
