from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from uuid import uuid7 as new_id

from pydantic import ConfigDict, Field

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.billing.application.evidence_cases import read_report_evidence
from src.api.billing.domain.charges import BalanceView
from src.api.billing.domain.money import BcvRate, charge_balance
from src.api.billing.domain.payments import (
    CurrencyMismatchError,
    DeclaredPayment,
    VerifiedPayment,
    convert_verified,
)
from src.api.billing.repository.dao import (
    dao_charges,
    dao_evidence,
    dao_exchange_rates,
    dao_payments,
    dao_reports,
    dao_reviews,
)
from src.core import Err, Ok, Result
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceView(ReviewModel):
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime


class ReviewItem(ReviewModel):
    report_id: UUID
    charge_id: UUID
    patient_id: UUID
    status: str
    declared: DeclaredPayment
    evidence: EvidenceView | None = None
    previous_report_id: UUID | None = None
    created_at: datetime
    version: int


class ReferenceWarning(ReviewModel):
    """A partial-reference coincidence only warns the reviewer; it never
    rejects or deletes anything by itself (§10.5)."""

    report_id: UUID
    status: str
    declared_paid_on: date
    declared_amount: Decimal


class ReviewOutcome(ReviewModel):
    decision: str
    reviewer_id: UUID
    decided_at: datetime
    verified_paid_on: date | None = None
    verified_amount: Decimal | None = None
    verified_currency: str | None = None
    internal_note: str | None = None
    reason: str | None = None


class ReviewDetail(ReviewItem):
    review: ReviewOutcome | None = None
    resubmissions: list[UUID] = Field(default_factory=list)
    reference_warnings: list[ReferenceWarning] = Field(default_factory=list)


async def _item(db: AsyncSession, row) -> ReviewItem:
    evidence = await dao_evidence.by_report(db, row.id)

    return ReviewItem(
        report_id=row.id,
        charge_id=row.charge_id,
        patient_id=row.patient_id,
        status=row.status,
        declared=DeclaredPayment(
            paid_on=row.declared_paid_on,
            amount=row.declared_amount,
            currency=row.declared_currency,
            method=row.declared_method,
            reference_last4=row.declared_reference_last4,
            note=row.declared_note,
        ),
        evidence=None
        if evidence is Empty
        else EvidenceView(
            content_type=evidence.content_type,
            size_bytes=evidence.size_bytes,
            sha256=evidence.sha256,
            uploaded_at=evidence.created_at,
        ),
        previous_report_id=row.previous_report_id,
        created_at=row.created_at,
        version=row.version,
    )


async def review_inbox(
    db: AsyncSession,
    account_id: UUID,
    page: int,
    shows: int,
    status: str | None = "pending",
    charge_id: UUID | None = None,
    patient_id: UUID | None = None,
) -> dict[str, object]:
    """Review tray; authorization happened before counting and paging (§12.1)."""
    rows, total = await dao_reports.page_inbox(
        db,
        account_id,
        page,
        shows,
        status=status,
        charge_id=charge_id,
        patient_id=patient_id,
    )

    return {"items": [await _item(db, row) for row in rows], "total": total}


async def review_detail(
    db: AsyncSession, account_id: UUID, report_id: UUID
) -> Result[ReviewDetail, AccountObjectNotFound]:
    row = await dao_reports.by_id_in_account(db, report_id, account_id)

    if row is Empty:
        return Err(AccountObjectNotFound())

    item = await _item(db, row)
    review = await dao_reviews.by_report(db, row.id)
    chain = await dao_reports.chain_of(db, row.id, account_id)
    warnings = []

    if row.declared_reference_last4 is not None:
        candidates, _ = await dao_reports.page_inbox(
            db, account_id, 1, 100, charge_id=row.charge_id
        )
        warnings = [
            ReferenceWarning(
                report_id=other.id,
                status=other.status,
                declared_paid_on=other.declared_paid_on,
                declared_amount=other.declared_amount,
            )
            for other in candidates
            if other.id != row.id
            and other.declared_reference_last4 == row.declared_reference_last4
        ]

    return Ok(
        ReviewDetail(
            **item.model_dump(),
            review=None
            if review is Empty
            else ReviewOutcome(
                decision=review.decision,
                reviewer_id=review.reviewer_id,
                decided_at=review.created_at,
                verified_paid_on=review.verified_paid_on,
                verified_amount=review.verified_amount,
                verified_currency=review.verified_currency,
                internal_note=review.internal_note,
                reason=review.reason,
            ),
            resubmissions=[entry.id for entry in chain],
            reference_warnings=warnings,
        )
    )


async def review_evidence(
    db: AsyncSession, account_id: UUID, report_id: UUID
) -> Result[tuple[str, bytes], AccountObjectNotFound]:
    """Evidence download; the route re-authorizes on every request and knowing
    the storage key grants nothing (§11.2)."""
    row = await dao_reports.by_id_in_account(db, report_id, account_id)

    if row is Empty:
        return Err(AccountObjectNotFound())

    content = await read_report_evidence(db, account_id, report_id)

    if isinstance(content, Err):
        return Err(AccountObjectNotFound())

    return content


class BillingApprovalRequest(ReviewModel):
    operation_id: UUID
    expected_version: int
    verified_paid_on: date
    verified_amount: Decimal
    verified_currency: str
    method: str
    reference_last4: str | None = None
    internal_note: str | None = None


class ApprovalResult(ReviewModel):
    report_id: UUID
    decision: str
    payment_id: UUID
    amount: Decimal
    currency: str
    balance: object
    duplicate: bool = False


class ReportNotPendingError(Exception):
    pass


class PaymentExceedsBalanceError(Exception):
    pass


async def approve_report(
    db: AsyncSession, context, report_id: UUID, data: BillingApprovalRequest
) -> Result[
    ApprovalResult,
    AccountObjectNotFound
    | ReportNotPendingError
    | PaymentExceedsBalanceError
    | CurrencyMismatchError,
]:
    """Atomic approval (§12.1, §13): review, report state, single payment and
    balance are confirmed in one transaction under the report and charge row
    locks; two reviewers or a retry never duplicate the payment nor exceed the
    charge (UQ of origin_report_id is the last line of defense)."""
    account_id = context.account.id
    report = await dao_reports.by_id_for_update(db, report_id, account_id)

    if report is Empty:
        return Err(AccountObjectNotFound())

    if report.status != "pending":
        return Err(ReportNotPendingError())

    charge = await dao_charges.by_id_for_update(db, report.charge_id, account_id)

    if charge is Empty:
        return Err(AccountObjectNotFound())

    verified = VerifiedPayment(
        paid_on=data.verified_paid_on,
        amount=data.verified_amount,
        currency=data.verified_currency,
        method=data.method,
        reference_last4=data.reference_last4,
        internal_note=data.internal_note,
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
        # An excess is rejected; the patient submits a corrected report (D26).
        return Err(PaymentExceedsBalanceError())

    now = datetime_now()
    review_id = new_id()
    await dao_reviews.insert_review(
        db,
        {
            "id": review_id,
            "report_id": report.id,
            "account_id": account_id,
            "reviewer_id": context.actor.user_id,
            "decision": "approved",
            "verified_paid_on": data.verified_paid_on,
            "verified_amount": data.verified_amount,
            "verified_currency": data.verified_currency,
            "billing_exchange_rate_id": None if rate_row is None else rate_row.id,
            "internal_note": data.internal_note,
        },
    )
    applied_status = await dao_reports.apply_status(
        db, report.id, account_id, report.version, "approved"
    )

    if not applied_status:
        return Err(ReportNotPendingError())

    payment_id = new_id()
    await dao_payments.insert_payment(
        db,
        {
            "id": payment_id,
            "account_id": account_id,
            "charge_id": charge.id,
            "patient_id": report.patient_id,
            "origin": "patient_report",
            "origin_report_id": report.id,
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
            "paid_on": data.verified_paid_on,
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
            action="ApprovePatientPaymentReport",
            object_type="patient_payment_report",
            object_key=str(report.id),
            outcome="accepted",
            correlation_id=data.operation_id,
            occurred_at=now,
        ),
    )
    new_balance = charge_balance(charge.amount, [*amounts, applied])

    return Ok(
        ApprovalResult(
            report_id=report.id,
            decision="approved",
            payment_id=payment_id,
            amount=applied,
            currency=charge.currency,
            balance=BalanceView(
                paid=new_balance.paid,
                outstanding=new_balance.outstanding,
                state=new_balance.state,
            ),
        )
    )


class BillingRejectionRequest(ReviewModel):
    operation_id: UUID
    expected_version: int
    # Safe reason without full bank data; the declaration and capture remain.
    reason: str
    internal_note: str | None = None


async def reject_report(
    db: AsyncSession, context, report_id: UUID, data: BillingRejectionRequest
) -> Result[ReviewItem, AccountObjectNotFound | ReportNotPendingError]:
    """Rejection never creates a payment nor changes balance or the appointment;
    the evidence and reason remain and a new presentation is allowed (§12.4)."""
    account_id = context.account.id
    report = await dao_reports.by_id_for_update(db, report_id, account_id)

    if report is Empty:
        return Err(AccountObjectNotFound())

    if report.status != "pending":
        return Err(ReportNotPendingError())

    await dao_reviews.insert_review(
        db,
        {
            "id": new_id(),
            "report_id": report.id,
            "account_id": account_id,
            "reviewer_id": context.actor.user_id,
            "decision": "rejected",
            "internal_note": data.internal_note,
            "reason": data.reason,
        },
    )
    applied = await dao_reports.apply_status(
        db, report.id, account_id, report.version, "rejected"
    )

    if not applied:
        return Err(ReportNotPendingError())

    await record_control(
        db,
        ControlAudit(
            account_id=account_id,
            actor_user_id=context.actor.user_id,
            actor_device_id=context.actor.device_id,
            action="RejectPatientPaymentReport",
            object_type="patient_payment_report",
            object_key=str(report.id),
            outcome="accepted",
            correlation_id=data.operation_id,
            occurred_at=datetime_now(),
        ),
    )
    rejected = await dao_reports.by_id_in_account(db, report.id, account_id)

    return Ok(await _item(db, rejected))
