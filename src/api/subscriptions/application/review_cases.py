from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.evidence_cases import (
    EvidenceNotFound,
    ReportNotFound,
)
from src.api.subscriptions.application.operator_cases import authenticate_operator
from src.api.subscriptions.application.report_cases import report_view
from src.api.subscriptions.domain.money import BcvRate, Money
from src.api.subscriptions.domain.periods import compute_period
from src.api.subscriptions.domain.plans import price_for
from src.api.subscriptions.domain.reports import (
    GrantedPeriodView,
    OperatorPaymentReportDetail,
    OperatorPaymentReportPage,
    OperatorPaymentReportView,
    ReferenceWarning,
    ReviewOutcomeView,
)
from src.api.subscriptions.domain.reviews import (
    ApprovalRequest,
    ApprovalResultResponse,
    GrantedPeriodResult,
    PaymentMismatchError,
    RejectionRequest,
    RejectionResultResponse,
    SubscriptionReview,
    SubscriptionStateView,
    VerifiedPayment,
    ensure_full_payment,
)
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_bcv_rates,
    dao_payment_reports,
    dao_plan_versions,
    dao_report_evidence,
    dao_subscription_periods,
    dao_subscription_reviews,
)
from src.core import Err, Ok, Result
from src.core.constants import CORRELATION_ID
from src.core.db import transaction
from src.core.services import report_storage
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def operator_report_view(db: AsyncSession, row) -> OperatorPaymentReportView:
    base = await report_view(db, row)

    return OperatorPaymentReportView(
        report_id=base.report_id,
        account_id=row.account_id,
        plan_code=base.plan_code,
        periodicity=base.periodicity,
        status=base.status,
        declared=base.declared,
        evidence=base.evidence,
        previous_report_id=base.previous_report_id,
        submitted_by=row.submitted_by,
        created_at=base.created_at,
        version=base.version,
    )


async def list_reports_for_operator(
    db: AsyncSession,
    token: str | None,
    status: str | None,
    account_id: UUID | None,
    page: int,
    shows: int,
) -> Result[OperatorPaymentReportPage, InvalidCredential | AccessDenied]:
    operator = await authenticate_operator(db, token, "review")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    rows, total = await dao_payment_reports.page_for_operator(
        db, status, account_id, page, shows
    )
    items = [await operator_report_view(db, row) for row in rows]

    return Ok(OperatorPaymentReportPage(items=items, total=total))


async def report_detail_for_operator(
    db: AsyncSession, token: str | None, report_id: UUID
) -> Result[
    OperatorPaymentReportDetail, InvalidCredential | AccessDenied | ReportNotFound
]:
    operator = await authenticate_operator(db, token, "review")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    row = await dao_payment_reports.get(db, report_id)

    if row is Empty:
        return Err(ReportNotFound())

    base = await operator_report_view(db, row)
    review = await dao_subscription_reviews.by_report(db, report_id)
    outcome = None

    if review is not Empty:
        period = await dao_subscription_periods.period_by_origin(db, review.id)
        outcome = ReviewOutcomeView(
            decision=review.decision,
            decided_at=review.created_at,
            granted_period=None
            if period is Empty
            else GrantedPeriodView(
                starts_at=period.starts_at,
                ends_at=period.ends_at,
                periodicity=period.periodicity,
                sequence=period.sequence,
            ),
            reason=review.reason,
        )

    warnings = []
    if row.declared_reference_last4 is not None:
        matches = await dao_payment_reports.reference_matches(
            db, row.account_id, row.declared_reference_last4, row.id
        )
        warnings = [
            ReferenceWarning(
                report_id=match.id,
                account_id=match.account_id,
                status=match.status,
                declared_paid_on=match.declared_paid_on,
                declared_amount=Money(
                    amount=match.declared_amount, currency=match.declared_currency
                ),
            )
            for match in matches
        ]

    resubmissions = await dao_payment_reports.resubmissions_of(db, report_id)

    return Ok(
        OperatorPaymentReportDetail(
            **base.model_dump(),
            review=outcome,
            resubmissions=resubmissions,
            reference_warnings=warnings,
        )
    )


async def read_evidence_for_operator(
    db: AsyncSession, token: str | None, report_id: UUID
) -> Result[
    tuple[str, bytes],
    InvalidCredential | AccessDenied | ReportNotFound | EvidenceNotFound,
]:
    """The operator downloads only with the review action, re-authorized on every
    request; the storage key never leaves the server (§13.2)."""
    operator = await authenticate_operator(db, token, "review")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    if (await dao_payment_reports.get(db, report_id)) is Empty:
        return Err(ReportNotFound())

    evidence = await dao_report_evidence.by_report(db, report_id)

    if evidence is Empty:
        return Err(EvidenceNotFound())

    try:
        content = await report_storage.fetch(evidence.storage_key)
    except report_storage.StorageError:
        return Err(EvidenceNotFound())

    return Ok((evidence.content_type, content))


@dataclass(frozen=True, slots=True)
class ReportNotPending:
    pass


@dataclass(frozen=True, slots=True)
class VersionConflict:
    pass


@dataclass(frozen=True, slots=True)
class PaymentMismatch:
    pass


@dataclass(frozen=True, slots=True)
class RateMismatch:
    pass


ApproveError = (
    InvalidCredential
    | AccessDenied
    | ReportNotFound
    | ReportNotPending
    | VersionConflict
    | PaymentMismatch
    | RateMismatch
)


async def _approval_result(
    db: AsyncSession, report_id, review, duplicate: bool
) -> ApprovalResultResponse:
    period = await dao_subscription_periods.period_by_origin(db, review.id)
    subscription = await dao_account_subscriptions.by_account_for_update(
        db, (await dao_payment_reports.get(db, report_id)).account_id
    )

    return ApprovalResultResponse(
        report_id=report_id,
        granted_period=GrantedPeriodResult(
            starts_at=period.starts_at,
            ends_at=period.ends_at,
            periodicity=period.periodicity,
            sequence=period.sequence,
        ),
        subscription=SubscriptionStateView(
            status=subscription.status, subscription_version=subscription.version
        ),
        duplicate=duplicate,
    )


async def approve_report(
    db: AsyncSession, token: str | None, report_id: UUID, payload: ApprovalRequest
) -> Result[ApprovalResultResponse, ApproveError]:
    """One transaction confirms review, report state, frozen rate/price, the
    unique period, the subscription and the audit evidence (§14.1)."""
    async with transaction(db):
        operator = await authenticate_operator(db, token, "review")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(actor):
                pass

        report = await dao_payment_reports.by_id_for_update(db, report_id)

        if report is Empty:
            return Err(ReportNotFound())

        existing = await dao_subscription_reviews.by_report(db, report_id)

        if existing is not Empty:
            # A lost response recovers the same approval; another decision conflicts.
            if existing.id == payload.operation_id:
                return Ok(
                    await _approval_result(db, report_id, existing, duplicate=True)
                )

            return Err(ReportNotPending())

        if report.version != payload.expected_version:
            return Err(VersionConflict())

        subscription = await dao_account_subscriptions.by_account_for_update(
            db, report.account_id
        )
        version = await dao_plan_versions.get(db, report.plan_version_id)
        due = Money(amount=price_for(version, report.periodicity), currency="USD")

        rate_row = Empty
        rate_domain = None

        if payload.verified_currency == "VES":
            if payload.bcv_rate_id is None:
                return Err(RateMismatch())

            rate_row = await dao_bcv_rates.get(db, payload.bcv_rate_id)

            if rate_row is Empty:
                return Err(RateMismatch())

            # D22: the applicable rate is the one published on the verified payment
            # date or, without publication, the most recent previous one. The
            # operator cannot pick another rate.
            applicable = await dao_bcv_rates.latest_on_or_before(
                db, payload.verified_paid_on
            )

            if applicable is Empty or applicable.id != rate_row.id:
                return Err(RateMismatch())

            rate_domain = BcvRate(
                rate_ves_per_usd=rate_row.rate_ves_per_usd,
                rate_date=rate_row.rate_date,
                source=rate_row.source,
            )

        review = SubscriptionReview(
            report_id=report_id,
            operator_id=actor.id,
            decision="approved",
            verified=VerifiedPayment(
                paid_on=payload.verified_paid_on,
                amount=payload.verified_amount,
                currency=payload.verified_currency,
            ),
            bcv_rate=rate_domain,
        )

        try:
            ensure_full_payment(review, due)
        except PaymentMismatchError:
            return Err(PaymentMismatch())

        now = datetime_now()
        last = await dao_subscription_periods.latest_period(db, subscription.id)
        period = compute_period(
            None if last is Empty else last.ends_at, now, report.periodicity
        )
        sequence = 1 if last is Empty else last.sequence + 1

        await dao_subscription_reviews.insert_review(
            db,
            {
                "id": payload.operation_id,
                "report_id": report_id,
                "operator_id": actor.id,
                "decision": "approved",
                "verified_paid_on": payload.verified_paid_on,
                "verified_amount": payload.verified_amount,
                "verified_currency": payload.verified_currency,
                "bcv_rate_id": None if rate_domain is None else payload.bcv_rate_id,
                "reason": None,
            },
        )
        await dao_payment_reports.mark_decided(
            db, report_id, "approved", payload.expected_version
        )
        await dao_subscription_periods.insert_period(
            db,
            uuid7(),
            subscription.id,
            report.plan_version_id,
            report.periodicity,
            period.starts_at,
            period.ends_at,
            sequence,
            payload.operation_id,
        )
        subscription_version = await dao_account_subscriptions.apply_approval(
            db, subscription.id, report.plan_version_id
        )
        await record_control(
            db,
            ControlAudit(
                account_id=report.account_id,
                operator_ref=str(actor.id),
                action="ApprovePaymentReport",
                object_type="payment_report",
                object_key=str(report_id),
                outcome="accepted",
                correlation_id=CORRELATION_ID.get() or uuid7(),
                occurred_at=now,
            ),
        )

        return Ok(
            ApprovalResultResponse(
                report_id=report_id,
                granted_period=GrantedPeriodResult(
                    starts_at=period.starts_at,
                    ends_at=period.ends_at,
                    periodicity=period.periodicity,
                    sequence=sequence,
                ),
                subscription=SubscriptionStateView(
                    status="active", subscription_version=subscription_version
                ),
            )
        )


async def reject_report(
    db: AsyncSession, token: str | None, report_id: UUID, payload: RejectionRequest
) -> Result[RejectionResultResponse, ApproveError]:
    """Rejection keeps the previous commercial state and never creates a
    payment or period; the declaration and evidence stay untouched (§15)."""
    async with transaction(db):
        operator = await authenticate_operator(db, token, "review")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(actor):
                pass

        report = await dao_payment_reports.by_id_for_update(db, report_id)

        if report is Empty:
            return Err(ReportNotFound())

        existing = await dao_subscription_reviews.by_report(db, report_id)

        if existing is not Empty:
            if existing.id == payload.operation_id and existing.decision == "rejected":
                return Ok(
                    RejectionResultResponse(
                        report_id=report_id, reason=existing.reason, duplicate=True
                    )
                )

            return Err(ReportNotPending())

        if report.version != payload.expected_version:
            return Err(VersionConflict())

        await dao_subscription_reviews.insert_review(
            db,
            {
                "id": payload.operation_id,
                "report_id": report_id,
                "operator_id": actor.id,
                "decision": "rejected",
                "verified_paid_on": None,
                "verified_amount": None,
                "verified_currency": None,
                "bcv_rate_id": None,
                "reason": payload.reason,
            },
        )
        await dao_payment_reports.mark_decided(
            db, report_id, "rejected", payload.expected_version
        )
        await record_control(
            db,
            ControlAudit(
                account_id=report.account_id,
                operator_ref=str(actor.id),
                action="RejectPaymentReport",
                object_type="payment_report",
                object_key=str(report_id),
                outcome="accepted",
                correlation_id=CORRELATION_ID.get() or uuid7(),
                occurred_at=datetime_now(),
            ),
        )

        return Ok(RejectionResultResponse(report_id=report_id, reason=payload.reason))
