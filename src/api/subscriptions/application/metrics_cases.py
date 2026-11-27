from datetime import timedelta
from typing import TYPE_CHECKING

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.operator_cases import authenticate_operator
from src.api.subscriptions.domain.metrics import (
    ExpiringSubscription,
    PendingReportsSummary,
    PlanPeriodicityCount,
    PlanStatusCount,
    SeatOverrun,
    SubscriptionMetricsResponse,
    VerifiedAmount,
)
from src.api.subscriptions.repository.dao import dao_metrics
from src.core import Err, Ok, Result
from src.core.utils.utils import datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def subscription_metrics(
    db: AsyncSession, token: str | None
) -> Result[SubscriptionMetricsResponse, InvalidCredential | AccessDenied]:
    """Administrative indicators behind their own platform action; pending
    reports never count as verified income and currencies are never mixed (§22)."""
    operator = await authenticate_operator(db, token, "metrics")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    now = datetime_now()
    pending_count, oldest = await dao_metrics.pending_reports(db)

    return Ok(
        SubscriptionMetricsResponse(
            accounts_by_plan=[
                PlanStatusCount(plan_code=code, status=status, count=count)
                for code, status, count in await dao_metrics.accounts_by_plan(db)
            ],
            expiring_soon=[
                ExpiringSubscription(account_id=account_id, ends_at=ends_at)
                for account_id, ends_at in await dao_metrics.expiring_soon(
                    db, now + timedelta(days=7)
                )
            ],
            pending_reports=PendingReportsSummary(
                count=pending_count, oldest_created_at=oldest
            ),
            periods_by_plan=[
                PlanPeriodicityCount(
                    plan_code=code, periodicity=periodicity, count=count
                )
                for code, periodicity, count in await dao_metrics.periods_by_plan(db)
            ],
            verified_amounts=[
                VerifiedAmount(currency=currency, total=total)
                for currency, total in await dao_metrics.verified_amounts(db)
            ],
            seats_over_limit=[
                SeatOverrun(account_id=account_id, used=used, limit=limit)
                for account_id, used, limit in await dao_metrics.seats_over_limit(db)
            ],
            generated_at=now,
        )
    )
