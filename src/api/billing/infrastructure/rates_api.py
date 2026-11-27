from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, assert_never
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.application.charge_cases import billing_scope
from src.api.billing.domain.payments import PaymentModel
from src.api.billing.repository.dao import dao_exchange_rates
from src.api.services.application.services_cases import resolve_service_price
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError, BaseModel, PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

router = APIRouter(
    tags=["billing"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


class BillingRateCreateRequest(PaymentModel):
    operation_id: UUID
    rate_date: date
    rate_ves_per_usd: Annotated[
        Decimal, Field(gt=0, decimal_places=6, allow_inf_nan=False)
    ]
    source: Annotated[str, Field(min_length=1)]


class BillingRateResponse(BaseModel):
    rate_id: UUID
    rate_date: date
    rate_ves_per_usd: Decimal
    source: str
    registered_at: datetime


class PriceResolutionResponse(BaseModel):
    service_id: UUID
    source: str
    amount: Decimal
    currency: str
    resolved_at: datetime


def _rate_response(row) -> BillingRateResponse:
    return BillingRateResponse(
        rate_id=row.id,
        rate_date=row.rate_date,
        rate_ves_per_usd=row.rate_ves_per_usd,
        source=row.source,
        registered_at=row.created_at,
    )


@router.get(
    "/v1/accounts/{account_id}/billing/price-resolution",
    operation_id="resolveBillingPrice",
    response_model=PriceResolutionResponse,
)
async def resolve_billing_price(
    account_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service_id: Annotated[UUID7, Query(alias="serviceId")],
    professional_id: Annotated[UUID7, Query(alias="professionalId")],
) -> PriceResolutionResponse:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None, account_id
        )

        if isinstance(scope, Err):
            result = scope
        else:
            resolved = await resolve_service_price(
                db, account_id, professional_id, service_id
            )
            result = (
                # PRICE_NOT_DEFINED is a uniform absence, distinct from zero (D25).
                Err(AccountObjectNotFound())
                if resolved is None
                else Ok(
                    PriceResolutionResponse(
                        service_id=service_id,
                        source=resolved.source,
                        amount=resolved.amount,
                        currency=resolved.currency,
                        resolved_at=datetime.now(UTC),
                    )
                )
            )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404, detail="PRICE_NOT_DEFINED")
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/billing/exchange-rates",
    operation_id="listBillingExchangeRates",
    response_model=PaginatedResponse[BillingRateResponse],
)
async def list_billing_exchange_rates(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    async with transaction(db):
        scope = await billing_scope(
            db,
            authorization.credentials if authorization else None,
            account_id,
            "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            rows, total = await dao_exchange_rates.page_rates(
                db, account_id, query.page, query.shows
            )
            result = Ok(
                {
                    "items": [_rate_response(row) for row in rows],
                    "total": total,
                }
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


@router.post(
    "/v1/accounts/{account_id}/billing/exchange-rates",
    operation_id="registerBillingExchangeRate",
    response_model=BillingRateResponse,
    status_code=201,
)
async def register_billing_exchange_rate(
    account_id: UUID7,
    payload: BillingRateCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> BillingRateResponse:
    async with transaction(db):
        scope = await billing_scope(
            db,
            authorization.credentials if authorization else None,
            account_id,
            "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        elif (
            await dao_exchange_rates.by_date(db, account_id, payload.rate_date)
            is not Empty
        ):
            result = Err("RATE_DATE_EXISTS")
        else:
            rate_id = payload.operation_id
            await dao_exchange_rates.insert_rate(
                db,
                rate_id,
                account_id,
                payload.rate_date,
                payload.rate_ves_per_usd,
                payload.source,
                scope.value.actor.user_id,
            )
            row = await dao_exchange_rates.by_date(db, account_id, payload.rate_date)
            result = Ok(_rate_response(row))

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case Err("RATE_DATE_EXISTS"):
            raise HTTPException(409, detail="RATE_DATE_EXISTS")
        case unexpected:
            assert_never(unexpected)
