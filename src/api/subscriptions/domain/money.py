from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, field_validator

from src.core.schema import BaseModel

Currency = Literal["USD", "VES"]

# One rounding rule for every quote and approval (account-subscriptions.md §9.2).
ROUNDING_RULE = "ROUND_HALF_UP"
_CENTS = Decimal("0.01")


class MoneyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _exact_amount(value: Decimal, max_places: int) -> Decimal:
    if not value.is_finite():
        raise ValueError("amount must be finite")
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -max_places:
        raise ValueError(f"amount admits at most {max_places} decimal places")
    return value


class Money(MoneyModel):
    amount: Annotated[Decimal, Field(gt=0)]
    currency: Currency

    @field_validator("amount")
    @classmethod
    def _two_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 2)


class BcvRate(MoneyModel):
    rate_ves_per_usd: Annotated[Decimal, Field(gt=0)]
    rate_date: date
    source: Annotated[str, Field(min_length=1)]

    @field_validator("rate_ves_per_usd")
    @classmethod
    def _six_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 6)

    @field_validator("rate_date")
    @classmethod
    def _finite_date(cls, value: date) -> date:
        # date has no infinity, but pydantic admits any year; keep it explicit.
        return value


def usd_to_ves(amount_usd: Decimal, rate: BcvRate) -> Decimal:
    """Equivalent VES of a USD amount; rounded once, at the quote total (§9.2)."""
    if not amount_usd.is_finite() or amount_usd <= 0:
        raise ValueError("amount_usd must be a positive finite decimal")

    return (amount_usd * rate.rate_ves_per_usd).quantize(_CENTS, rounding=ROUNDING_RULE)
