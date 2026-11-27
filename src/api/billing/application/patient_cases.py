import hashlib
from typing import TYPE_CHECKING

from src.api.billing.domain.money import charge_balance
from src.api.billing.domain.payments import (
    GrantAction,
    PatientBillingGrant,
    PatientChargeView,
)
from src.api.billing.repository.dao import (
    dao_charges,
    dao_grants,
    dao_payments,
    dao_reports,
)
from src.core import Err, Ok, Result
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GrantNotUsable(Exception):
    """Expired, revoked, foreign or action-less links are a uniform absence (D28)."""


async def usable_grant(
    db: AsyncSession, secret: str | None, action: GrantAction
) -> Result[PatientBillingGrant, GrantNotUsable]:
    """The UUID alone authorizes nothing: hash match, validity window and the
    granted action are all required (D28)."""
    if not secret:
        return Err(GrantNotUsable())

    row = await dao_grants.by_token_hash(
        db, hashlib.sha256(secret.encode()).hexdigest()
    )

    if row is Empty:
        return Err(GrantNotUsable())

    grant = PatientBillingGrant(
        grant_id=row.id,
        account_id=row.account_id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        charge_id=row.charge_id,
        actions=row.actions,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
    )

    if not grant.usable(action, datetime_now()):
        return Err(GrantNotUsable())

    return Ok(grant)


async def read_patient_charges(
    db: AsyncSession, secret: str | None
) -> Result[dict[str, object], GrantNotUsable]:
    """Minimal projection of the granted charge(s) only; drafts never appear
    (§9.3, §8.2). Presenting or reading never changes the balance."""
    grant = await usable_grant(db, secret, "read_charge")

    if isinstance(grant, Err):
        return grant

    scope = grant.value
    if scope.charge_id is not None:
        row = await dao_charges.by_id_in_account(db, scope.charge_id, scope.account_id)
        rows = [] if row is Empty or row.status == "draft" else [row]
    else:
        rows, _ = await dao_charges.page_list(
            db, scope.account_id, 1, 100, patient_id=scope.patient_id
        )
        rows = [
            row
            for row in rows
            if row.appointment_id == scope.appointment_id and row.status != "draft"
        ]

    items = []

    for row in rows:
        amounts = await dao_payments.active_amounts_of(db, row.id, scope.account_id)
        balance = charge_balance(row.amount, amounts)
        latest, _ = await dao_reports.page_inbox(
            db, scope.account_id, 1, 1, charge_id=row.id
        )
        items.append(
            PatientChargeView(
                charge_id=row.id,
                description=row.description,
                amount=row.amount,
                currency=row.currency,
                outstanding=balance.outstanding,
                balance_state=balance.state,
                issued_at=row.issued_at,
                review_state=None if not latest else latest[0].status,
            )
        )

    return Ok({"items": items, "total": len(items)})


async def read_patient_receipt(
    db: AsyncSession, secret: str | None, payment_id
) -> Result[tuple[str, bytes], GrantNotUsable]:
    """Receipt download with the read_receipt action over the granted charge."""
    from src.api.billing.application.receipt_cases import read_receipt
    from src.api.billing.repository.dao import dao_payments

    grant = await usable_grant(db, secret, "read_receipt")

    if isinstance(grant, Err):
        return grant

    scope = grant.value
    payment = await dao_payments.by_id_in_account(db, payment_id, scope.account_id)

    if payment is Empty:
        return Err(GrantNotUsable())

    if scope.charge_id is not None and payment.charge_id != scope.charge_id:
        return Err(GrantNotUsable())

    if scope.charge_id is None:
        charge = await dao_charges.by_id_in_account(
            db, payment.charge_id, scope.account_id
        )
        if charge is Empty or charge.appointment_id != scope.appointment_id:
            return Err(GrantNotUsable())

    result = await read_receipt(db, scope.account_id, payment_id)

    if isinstance(result, Err):
        return Err(GrantNotUsable())

    return result
