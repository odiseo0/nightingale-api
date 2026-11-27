from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.quote_cases import (
    PlanNotFound,
    PlanUnavailable,
    RateDateExists,
    RateUnavailable,
    create_quote,
    list_rates,
    register_rate,
)
from src.api.subscriptions.domain.quotes import (
    BcvRateCreateRequest,
    BcvRatePage,
    BcvRateResponse,
    QuoteRequest,
    QuoteResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery

operator_rates_router = APIRouter(
    prefix="/v1/operator/bcv-rates",
    tags=["operator-subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 409, 422)},
)
quotes_router = APIRouter(
    prefix="/v1/accounts/{account_id}/subscription",
    tags=["subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@operator_rates_router.get("", operation_id="listOperatorBcvRates")
async def list_operator_bcv_rates(
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> BcvRatePage:
    result = await list_rates(
        db, authorization.credentials if authorization else None, query.page, query.shows
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


@operator_rates_router.post("", operation_id="registerOperatorBcvRate", status_code=201)
async def register_operator_bcv_rate(
    payload: BcvRateCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> BcvRateResponse:
    result = await register_rate(
        db, authorization.credentials if authorization else None, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(RateDateExists()):
            raise HTTPException(409)
        case unexpected:
            assert_never(unexpected)


@quotes_router.post("/quotes", operation_id="createSubscriptionQuote", status_code=201)
async def create_subscription_quote(
    account_id: UUID7,
    payload: QuoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> QuoteResponse:
    result = await create_quote(
        db, authorization.credentials if authorization else None, account_id, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | PlanNotFound()):
            raise HTTPException(404)
        case Err(PlanUnavailable()):
            raise HTTPException(409)
        case Err(RateUnavailable()):
            raise HTTPException(503)
        case unexpected:
            assert_never(unexpected)
