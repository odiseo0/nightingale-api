from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID, uuid7

from pydantic import ConfigDict, Field

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.billing.application.review_cases import PaymentExceedsBalanceError
from src.api.billing.domain.charges import BalanceView
from src.api.billing.domain.money import BcvRate, charge_balance
from src.api.billing.domain.payments import (
    CurrencyMismatchError,
    VerifiedPayment,
    convert_verified,
)
from src.api.billing.repository.dao import dao_charges, dao_exchange_rates, dao_payments
from src.core import Err, Ok, Result
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DirectPaymentRequest(BaseModel):
    """Cash or other payment received directly by the practice (staff_entry);
    never a simulated patient report (D26)."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_version: int
    paid_on: date
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2, allow_inf_nan=False)]
    currency: Literal["USD", "VES"]
    method: Annotated[str, Field(min_length=1)]
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    evidence_note: Annotated[str, Field(min_length=1)]


class PaymentResponse(BaseModel):
    payment_id: UUID
    charge_id: UUID
    origin: Literal["patient_report", "staff_entry"]
    amount: Decimal
    currency: str
    exchange_rate: Decimal | None = None
    exchange_rate_date: date | None = None
    exchange_rate_source: str | None = None
    paid_on: date
    method: str
    reference_last4: str | None = None
    status: str
    registered_by: UUID
    created_at: datetime
    version: int
    balance: BalanceView | None = None


class ChargeNotIssuedError(Exception):
    pass


async def register_direct_payment(
    db: AsyncSession, context, charge_id: UUID, data: DirectPaymentRequest
) -> Result[
    PaymentResponse,
    AccountObjectNotFound
    | ChargeNotIssuedError
    | PaymentExceedsBalanceError
    | CurrencyMismatchError,
]:
    """Direct staff payment with its own origin and evidence note; same
    currency, balance and single-effect rules as an approval (D26)."""
    account_id = context.account.id
    charge = await dao_charges.by_id_for_update(db, charge_id, account_id)

    if charge is Empty:
        return Err(AccountObjectNotFound())

    if charge.status != "issued":
        return Err(ChargeNotIssuedError())

    verified = VerifiedPayment(
        paid_on=data.paid_on,
        amount=data.amount,
        currency=data.currency,
        method=data.method,
        reference_last4=data.reference_last4,
    )
    rate_row = None
    rate = None
    if verified.currency != charge.currency:
        rate_row = await dao_exchange_rates.applicable(db, account_id, verified.paid_on)

        if rate_row is Empty:
            return Err(CurrencyMismatchError())

        rate = BcvRate(
            rate_ves_per_usd=rate_row.rate_ves_per_usd,
            rate_date=rate_row.rate_date,
            source=rate_row.source,
        )

    applied, conversion = convert_verified(verified, charge.currency, rate)
    amounts = await dao_payments.active_amounts_of(db, charge.id, account_id)
    balance = charge_balance(charge.amount, amounts)

    if balance.paid + applied > charge.amount:
        return Err(PaymentExceedsBalanceError())

    payment_id = uuid7()
    await dao_payments.insert_payment(
        db,
        {
            "id": payment_id,
            "account_id": account_id,
            "charge_id": charge.id,
            "patient_id": charge.patient_id,
            "origin": "staff_entry",
            "origin_report_id": None,
            "amount": applied,
            "currency": charge.currency,
            "amount_usd": None if conversion is None else conversion.amount_usd,
            "exchange_rate": None if conversion is None else conversion.exchange_rate,
            "exchange_rate_date": None
            if conversion is None
            else conversion.exchange_rate_date,
            "exchange_rate_source": None
            if conversion is None
            else conversion.exchange_rate_source,
            "paid_on": data.paid_on,
            "method": data.method,
            "reference_last4": data.reference_last4,
            "registered_by": context.actor.user_id,
        },
    )
    await record_control(
        db,
        ControlAudit(
            account_id=account_id,
            actor_user_id=context.actor.user_id,
            actor_device_id=context.actor.device_id,
            action="RegisterDirectPatientPayment",
            object_type="patient_payment",
            object_key=str(payment_id),
            outcome="accepted",
            correlation_id=data.operation_id,
            occurred_at=datetime_now(),
        ),
    )
    row = await dao_payments.by_id_in_account(db, payment_id, account_id)
    new_balance = charge_balance(charge.amount, [*amounts, applied])

    return Ok(
        PaymentResponse(
            payment_id=row.id,
            charge_id=row.charge_id,
            origin=row.origin,
            amount=row.amount,
            currency=row.currency,
            exchange_rate=row.exchange_rate,
            exchange_rate_date=row.exchange_rate_date,
            exchange_rate_source=row.exchange_rate_source,
            paid_on=row.paid_on,
            method=row.method,
            reference_last4=row.reference_last4,
            status=row.status,
            registered_by=row.registered_by,
            created_at=row.created_at,
            version=row.version,
            balance=BalanceView(
                paid=new_balance.paid,
                outstanding=new_balance.outstanding,
                state=new_balance.state,
            ),
        )
    )
