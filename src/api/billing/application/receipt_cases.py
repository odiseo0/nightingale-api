import hashlib
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.billing.repository.dao import dao_charges, dao_payments, dao_receipts
from src.core import Err, Ok, Result
from src.core.services import report_storage
from src.core.services.billing_receipts import render_receipt_pdf
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def read_receipt(
    db: AsyncSession, account_id: UUID, payment_id: UUID
) -> Result[tuple[str, bytes], AccountObjectNotFound]:
    """Non-fiscal administrative receipt with its frozen snapshot (§11.3).

    Generated on first authorized download and stored privately; later changes
    (annulment, renames) never rewrite it — the payment row carries the current
    state. Knowing the storage key grants nothing: the route re-authorizes.
    """
    payment = await dao_payments.by_id_in_account(db, payment_id, account_id)

    if payment is Empty:
        return Err(AccountObjectNotFound())

    receipt = await dao_receipts.by_payment(db, payment_id)

    if receipt is not Empty:
        try:
            return Ok(("application/pdf", await report_storage.fetch(receipt.storage_key)))
        except report_storage.StorageError:
            return Err(AccountObjectNotFound())

    charge = await dao_charges.by_id_in_account(db, payment.charge_id, account_id)

    if charge is Empty:
        return Err(AccountObjectNotFound())

    lines = [
        "Nightingale - Constancia administrativa de pago",
        "Este documento no es una factura fiscal ni una constancia de devolucion.",
        "",
        f"Comprobante: {uuid7()}",
        f"Pago: {payment.id}",
        f"Cargo: {charge.id} - {charge.description}",
        f"Origen: {payment.origin}",
        f"Importe aplicado: {payment.amount} {payment.currency}",
    ]
    if payment.exchange_rate is not None:
        lines.append(
            f"Conversion BCV: tasa {payment.exchange_rate} del "
            f"{payment.exchange_rate_date} ({payment.exchange_rate_source})"
        )
    lines += [
        f"Fecha del pago: {payment.paid_on}",
        f"Metodo: {payment.method}",
        f"Referencia (parcial): {payment.reference_last4 or 'n/a'}",
        f"Estado al emitir: {payment.status}",
    ]
    content = render_receipt_pdf(lines)
    receipt_id = uuid7()
    storage_key = await report_storage.save(account_id, receipt_id, content)
    await dao_receipts.insert_receipt(
        db,
        {
            "id": receipt_id,
            "account_id": account_id,
            "payment_id": payment_id,
            "storage_key": storage_key,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )

    return Ok(("application/pdf", content))
