from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.billing.domain.charges import BalanceView, ChargeResponse
from src.api.billing.domain.money import charge_balance
from src.api.billing.domain.payments import BillingPaymentProjection
from src.api.billing.repository.dao import dao_charges, dao_payments
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_billing(db: AsyncSession, context: AccountContext) -> list[SyncItem]:
    """Financial snapshot for the closed billing audience (§16.1): issued or
    cancelled charges with their balance and all payments by reference. Drafts,
    captures, receipts, rates and grant secrets never travel here."""
    if not (context.owner or context.billing_permissions.granted("billing_read")):
        return []

    account_id = context.account.id
    items: list[SyncItem] = []
    charges, _ = await dao_charges.page_list(db, account_id, 1, 500)
    payments_by_charge: dict = {}

    rows = await dao_payments.page_account(db, account_id)
    for row in rows:
        payments_by_charge.setdefault(row.charge_id, []).append(row)
        items.append(
            SyncItem(
                entity_type="billing_payment",
                entity_key=row.id,
                entity_version=row.version,
                state=BillingPaymentProjection(
                    payment_id=row.id,
                    charge_id=row.charge_id,
                    patient_id=row.patient_id,
                    origin=row.origin,
                    amount=row.amount,
                    currency=row.currency,
                    status=row.status,
                    paid_on=row.paid_on,
                    registered_by=row.registered_by,
                    updated_at=row.updated_at,
                ),
            )
        )

    for charge in charges:
        if charge.status == "draft":
            continue

        amounts = [
            row.amount
            for row in payments_by_charge.get(charge.id, [])
            if row.status == "active"
        ]
        balance = charge_balance(charge.amount, amounts)
        items.append(
            SyncItem(
                entity_type="billing_charge",
                entity_key=charge.id,
                entity_version=charge.version,
                state=ChargeResponse(
                    charge_id=charge.id,
                    patient_id=charge.patient_id,
                    appointment_id=charge.appointment_id,
                    encounter_id=charge.encounter_id,
                    service_id=charge.service_id,
                    description=charge.description,
                    amount=charge.amount,
                    currency=charge.currency,
                    price_source=charge.price_source,
                    status=charge.status,
                    balance=BalanceView(
                        paid=balance.paid,
                        outstanding=balance.outstanding,
                        state=balance.state,
                    ),
                    issued_at=charge.issued_at,
                    cancelled_at=charge.cancelled_at,
                    created_at=charge.created_at,
                    version=charge.version,
                ),
            )
        )

    return items
