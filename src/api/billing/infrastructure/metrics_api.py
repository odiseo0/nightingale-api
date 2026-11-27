from datetime import UTC, datetime, timedelta
from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.application.charge_cases import billing_scope
from src.api.billing.application.metrics_cases import (
    BillingMetricsResponse,
    billing_metrics,
)
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError

router = APIRouter(
    tags=["billing"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/v1/accounts/{account_id}/billing/metrics",
    operation_id="getBillingMetrics",
    response_model=BillingMetricsResponse,
)
async def get_billing_metrics(
    account_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    until: Annotated[datetime | None, Query()] = None,
) -> BillingMetricsResponse:
    window_until = until or datetime.now(UTC)
    window_from = from_ or window_until - timedelta(days=30)

    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None, account_id
        )

        if isinstance(scope, Err):
            result = scope
        elif window_from >= window_until:
            raise HTTPException(422)
        else:
            result = Ok(
                await billing_metrics(db, account_id, window_from, window_until)
            )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
