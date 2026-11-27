from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from src.api.accounts.application.accounts_cases import get_account_context
from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.operator_cases import authenticate_operator
from src.api.subscriptions.domain.money import BcvRate, usd_to_ves
from src.api.subscriptions.domain.plans import price_for
from src.api.subscriptions.domain.quotes import (
    BcvRateCreateRequest,
    BcvRatePage,
    BcvRateResponse,
    QuoteRequest,
    QuoteResponse,
)
from src.api.subscriptions.repository.dao import (
    dao_bcv_rates,
    dao_plan_versions,
    dao_subscription_plans,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

CARACAS = ZoneInfo("America/Caracas")


@dataclass(frozen=True, slots=True)
class RateDateExists:
    pass


@dataclass(frozen=True, slots=True)
class RateUnavailable:
    pass


@dataclass(frozen=True, slots=True)
class PlanNotFound:
    pass


@dataclass(frozen=True, slots=True)
class PlanUnavailable:
    pass


RateError = InvalidCredential | AccessDenied | RateDateExists
QuoteError = (
    InvalidCredential
    | AccountNotFound
    | AccessDenied
    | PlanNotFound
    | PlanUnavailable
    | RateUnavailable
)


def rate_response(row) -> BcvRateResponse:
    return BcvRateResponse(
        rate_id=row.id,
        rate_date=row.rate_date,
        rate_ves_per_usd=row.rate_ves_per_usd,
        source=row.source,
        registered_at=row.created_at,
    )


async def register_rate(
    db: AsyncSession, token: str | None, payload: BcvRateCreateRequest
) -> Result[BcvRateResponse, RateError]:
    async with transaction(db):
        operator = await authenticate_operator(db, token, "rates")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(actor):
                pass

        existing = await dao_bcv_rates.by_date(db, payload.rate_date)

        if existing is not Empty:
            return Err(RateDateExists())

        rate_id = uuid7()
        await dao_bcv_rates.insert_rate(
            db,
            rate_id,
            payload.rate_date,
            payload.rate_ves_per_usd,
            payload.source,
            actor.id,
        )
        row = await dao_bcv_rates.by_date(db, payload.rate_date)

    return Ok(rate_response(row))


async def list_rates(
    db: AsyncSession, token: str | None, page: int, shows: int
) -> Result[BcvRatePage, InvalidCredential | AccessDenied]:
    operator = await authenticate_operator(db, token, "rates")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    rows, total = await dao_bcv_rates.page(db, page, shows)

    return Ok(BcvRatePage(items=[rate_response(row) for row in rows], total=total))


async def build_quote(
    db: AsyncSession, plan_code: str, periodicity: str, now: datetime
) -> Result[QuoteResponse, PlanNotFound | PlanUnavailable | RateUnavailable]:
    """Latest plan version priced with the most recent BCV rate published on or
    before today in America/Caracas (D22); nothing is persisted or activated."""
    plan = await dao_subscription_plans.by_code(db, plan_code)

    if plan is Empty:
        return Err(PlanNotFound())

    if plan.status == "retired":
        return Err(PlanUnavailable())

    version = await dao_plan_versions.latest_version(db, plan.id)
    today = now.astimezone(CARACAS).date()
    rate_row = await dao_bcv_rates.latest_on_or_before(db, today)

    if rate_row is Empty:
        return Err(RateUnavailable())

    amount_usd = price_for(version, periodicity)
    rate = BcvRate(
        rate_ves_per_usd=rate_row.rate_ves_per_usd,
        rate_date=rate_row.rate_date,
        source=rate_row.source,
    )

    return Ok(
        QuoteResponse(
            quote_id=uuid7(),
            plan_code=plan_code,
            plan_version=version.version,
            periodicity=periodicity,
            amount_usd=amount_usd,
            bcv_rate=rate.rate_ves_per_usd,
            bcv_rate_date=rate.rate_date,
            bcv_rate_source=rate.source,
            amount_ves=usd_to_ves(amount_usd, rate),
            quoted_at=now,
        )
    )


async def create_quote(
    db: AsyncSession, credential: str | None, account_id: UUID, payload: QuoteRequest
) -> Result[QuoteResponse, QuoteError]:
    context = await get_account_context(db, credential, account_id, require_device=True)

    match context:
        case Err(error):
            return Err(error)
        case Ok(account):
            pass

    if not account.owner:
        return Err(AccessDenied())

    return await build_quote(db, payload.plan_code, payload.periodicity, datetime_now())
