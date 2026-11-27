from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, field_validator

from src.core.schema import BaseModel

Currency = Literal["USD", "VES"]

# One rounding rule for every conversion (patient-billing.md §14.3, D25).
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
    # Zero is a valid free price; null (absence of a price) is modelled by None (D25).
    amount: Annotated[Decimal, Field(ge=0)]
    currency: Currency

    @field_validator("amount")
    @classmethod
    def _two_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 2)


class BcvRate(MoneyModel):
    # Billing keeps its own rate configuration and history, separate from subscriptions (D25).
    rate_ves_per_usd: Annotated[Decimal, Field(gt=0)]
    rate_date: date
    source: Annotated[str, Field(min_length=1)]

    @field_validator("rate_ves_per_usd")
    @classmethod
    def _six_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 6)


def _positive_finite(amount: Decimal) -> Decimal:
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be a positive finite decimal")
    return amount


def usd_to_ves(amount_usd: Decimal, rate: BcvRate) -> Decimal:
    """Equivalent VES of a USD amount; rounded once, half-up, two places (D25)."""
    _positive_finite(amount_usd)

    return (amount_usd * rate.rate_ves_per_usd).quantize(_CENTS, rounding=ROUNDING_RULE)


def ves_to_usd(amount_ves: Decimal, rate: BcvRate) -> Decimal:
    """USD applied to a USD charge paid in VES; conversion is explicit and prior (§14.2, D25)."""
    _positive_finite(amount_ves)

    return (amount_ves / rate.rate_ves_per_usd).quantize(_CENTS, rounding=ROUNDING_RULE)


BalanceState = Literal["unpaid", "partially_paid", "paid"]


class ChargeBalance(MoneyModel):
    total: Annotated[Decimal, Field(ge=0)]
    paid: Annotated[Decimal, Field(ge=0)]
    outstanding: Annotated[Decimal, Field(ge=0)]
    state: BalanceState


def charge_balance(total: Decimal, active_payments: Iterable[Decimal]) -> ChargeBalance:
    """Balance of one charge from its active payments, in the charge currency (§13.2).

    Annulled payments are excluded by the caller. An excess is rejected by policy
    (D26), so a sum above the total is an error, never a credit.
    """
    _exact_amount(total, 2)
    if total < 0:
        raise ValueError("total must not be negative")

    paid = Decimal("0.00")
    for payment in active_payments:
        _positive_finite(payment)
        _exact_amount(payment, 2)
        paid += payment

    if paid > total:
        raise ValueError("active payments exceed the charge total")

    outstanding = total - paid
    # A zero-total (free) charge has zero outstanding and counts as paid (§19.1).
    state: BalanceState = (
        "paid" if outstanding == 0 else ("unpaid" if paid == 0 else "partially_paid")
    )

    return ChargeBalance(total=total, paid=paid, outstanding=outstanding, state=state)
