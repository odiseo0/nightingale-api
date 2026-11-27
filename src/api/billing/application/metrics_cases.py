from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from src.core.schema import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.api.billing.repository.dao import dao_metrics


class CurrencyAmount(BaseModel):
    currency: str
    amount: Decimal


class BillingMetricsResponse(BaseModel):
    """D28 panel: charged/outstanding by issue date, collected by approval
    (registration) date; totals always per currency, never revalued."""

    charged: list[CurrencyAmount]
    collected: list[CurrencyAmount]
    outstanding: list[CurrencyAmount]
    pending_review: int
    partially_paid: int
    paid_charges: int
    annulments: list[CurrencyAmount]
    basis_charged_by: str = "issueDate"
    basis_collected_by: str = "approvalDate"
    from_: datetime
    until: datetime


def _amounts(values: dict) -> list[CurrencyAmount]:
    return [
        CurrencyAmount(currency=currency, amount=amount)
        for currency, amount in sorted(values.items())
    ]


async def billing_metrics(
    db: AsyncSession, account_id: UUID, since: datetime, until: datetime
) -> BillingMetricsResponse:
    panel = await dao_metrics.panel(db, account_id, since, until)

    return BillingMetricsResponse(
        charged=_amounts(panel["charged"]),
        collected=_amounts(panel["collected"]),
        outstanding=_amounts(panel["outstanding"]),
        pending_review=panel["pending_review"],
        partially_paid=panel["partially_paid"],
        paid_charges=panel["paid_charges"],
        annulments=_amounts(panel["annulments"]),
        from_=since,
        until=until,
    )
