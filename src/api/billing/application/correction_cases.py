from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ConfigDict

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.billing.application.direct_payment_cases import PaymentResponse
from src.api.billing.domain.charges import BalanceView
from src.api.billing.domain.money import charge_balance
from src.api.billing.repository.dao import dao_charges, dao_payments
from src.core import Err, Ok, Result
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PaymentAnnulmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_version: int
    # The reason never claims a refund; no money moves back (D27).
    reason: str


class PaymentAlreadyAnnulledError(Exception):
    pass


async def annul_payment(
    db: AsyncSession, context, payment_id: UUID, data: PaymentAnnulmentRequest
) -> Result[PaymentResponse, AccountObjectNotFound | PaymentAlreadyAnnulledError]:
    """Annulment excludes the payment from the active balance without deleting
    the report, evidence or receipt, and never affirms a refund (§13.5, D27).
    The charge row lock serializes the balance effect with approvals."""
    account_id = context.account.id
    payment = await dao_payments.by_id_in_account(db, payment_id, account_id)

    if payment is Empty:
        return Err(AccountObjectNotFound())

    charge = await dao_charges.by_id_for_update(db, payment.charge_id, account_id)

    if charge is Empty:
        return Err(AccountObjectNotFound())

    now = datetime_now()
    applied = await dao_payments.annul(
        db,
        payment_id,
        account_id,
        payment.version,
        now,
        context.actor.user_id,
        data.reason,
    )

    if not applied:
        return Err(PaymentAlreadyAnnulledError())

    await record_control(
        db,
        ControlAudit(
            account_id=account_id,
            actor_user_id=context.actor.user_id,
            actor_device_id=context.actor.device_id,
            action="AnnulPatientPayment",
            object_type="patient_payment",
            object_key=str(payment_id),
            outcome="accepted",
            correlation_id=data.operation_id,
            occurred_at=now,
        ),
    )
    row = await dao_payments.by_id_in_account(db, payment_id, account_id)
    amounts = await dao_payments.active_amounts_of(db, charge.id, account_id)
    balance = charge_balance(charge.amount, amounts)

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
                paid=balance.paid,
                outstanding=balance.outstanding,
                state=balance.state,
            ),
        )
    )
