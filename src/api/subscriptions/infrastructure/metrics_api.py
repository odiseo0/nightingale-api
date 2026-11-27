from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.metrics_cases import subscription_metrics
from src.api.subscriptions.domain.metrics import SubscriptionMetricsResponse
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/operator/metrics",
    tags=["operator-subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/subscriptions", operation_id="getOperatorSubscriptionMetrics")
async def get_operator_subscription_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SubscriptionMetricsResponse:
    result = await subscription_metrics(
        db, authorization.credentials if authorization else None
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case unexpected:
            assert_never(unexpected)
