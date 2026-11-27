from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field

from src.api.billing.domain.money import Currency, Money, MoneyModel

PriceSource = Literal["offer", "base", "manual"]


class ResolvedPrice(MoneyModel):
    """Effective price of a service in one account; never reserves the price (D25)."""

    amount: Annotated[Decimal, Field(ge=0)]
    currency: Currency
    source: Literal["offer", "base"]


def resolve_price(offer: Money | None, base: Money | None) -> ResolvedPrice | None:
    """Offer price replaces the professional base when present; None = no price (D25).

    The patient estimate uses this same resolution and is non-binding.
    """
    if offer is not None:
        return ResolvedPrice(
            amount=offer.amount, currency=offer.currency, source="offer"
        )
    if base is not None:
        return ResolvedPrice(amount=base.amount, currency=base.currency, source="base")

    return None
