import hashlib
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import get_account_context
from src.api.accounts.domain.errors import AccountNotFound
from src.api.audit.application.audit_cases import record_operation
from src.api.audit.domain.audit import OperationAudit
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.projection_cases import (
    publish_subscription_change,
)
from src.api.subscriptions.domain.money import Money
from src.api.subscriptions.domain.reports import (
    DeclaredPayment,
    EvidenceView,
    GrantedPeriodView,
    PaymentReportCreateRequest,
    PaymentReportDetailResponse,
    PaymentReportResponse,
    ReviewOutcomeView,
)
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_payment_reports,
    dao_plan_versions,
    dao_report_evidence,
    dao_subscription_periods,
    dao_subscription_plans,
    dao_subscription_reviews,
)
from src.api.sync.repository.dao import dao_receipts
from src.core import Err, Ok, Result
from src.core.constants import CORRELATION_ID
from src.core.db import transaction
from src.core.schema import PaginatedResponse
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class ReportNotFound:
    pass


@dataclass(frozen=True, slots=True)
class PlanUnavailable:
    pass


@dataclass(frozen=True, slots=True)
class IdempotencyConflict:
    pass


@dataclass(frozen=True, slots=True)
class EvidenceNotFound:
    pass


SubmitError = (
    InvalidCredential
    | AccountNotFound
    | AccessDenied
    | PlanUnavailable
    | IdempotencyConflict
)


async def report_view(db: AsyncSession, row) -> PaymentReportResponse:
    version = await dao_plan_versions.get(db, row.plan_version_id)
    plan = await dao_subscription_plans.get(db, version.plan_id)
    evidence = await dao_report_evidence.by_report(db, row.id)

    return PaymentReportResponse(
        report_id=row.id,
        plan_code=plan.code,
        periodicity=row.periodicity,
        status=row.status,
        declared=DeclaredPayment(
            paid_on=row.declared_paid_on,
            amount=Money(amount=row.declared_amount, currency=row.declared_currency),
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


def same_intent(
    row, account_id: UUID, payload: PaymentReportCreateRequest, plan_version_id
) -> bool:
    return (
        row.account_id == account_id
        and row.plan_version_id == plan_version_id
        and row.periodicity == payload.periodicity
        and row.declared_paid_on == payload.declared_paid_on
        and row.declared_amount == payload.declared_amount.amount
        and row.declared_currency == payload.declared_amount.currency
        and row.declared_method == payload.declared_method
        and row.declared_reference_last4 == payload.declared_reference_last4
        and row.declared_note == payload.declared_note
        and row.previous_report_id == payload.previous_report_id
    )


async def submit_report(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    payload: PaymentReportCreateRequest,
) -> Result[PaymentReportResponse, SubmitError]:
    """Submitting a payment report never activates or extends anything (§12).

    Authentication reads and the write share one transaction: the session
    autobegins on the first SELECT, so a second begin would be rejected."""
    async with transaction(db):
        context = await get_account_context(
            db, credential, account_id, require_device=True
        )

        match context:
            case Err(error):
                return Err(error)
            case Ok(account):
                pass

        if not account.owner:
            return Err(AccessDenied())

        return await _persist_report(
            db,
            account_id,
            account.actor.user_id,
            payload,
            device_id=account.actor.device_id,
        )


async def store_report(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    payload: PaymentReportCreateRequest,
    device_id: UUID | None = None,
) -> Result[PaymentReportResponse, PlanUnavailable | IdempotencyConflict]:
    async with transaction(db):
        return await _persist_report(
            db, account_id, user_id, payload, device_id=device_id
        )


async def _persist_report(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    payload: PaymentReportCreateRequest,
    device_id: UUID | None = None,
) -> Result[PaymentReportResponse, PlanUnavailable | IdempotencyConflict]:
    plan = await dao_subscription_plans.by_code(db, payload.plan_code)

    if plan is Empty or plan.status == "retired":
        return Err(PlanUnavailable())

    version = await dao_plan_versions.latest_version(db, plan.id)
    existing = await dao_payment_reports.get(db, payload.operation_id)

    if existing is not Empty:
        # A lost response recovers the same report; different content conflicts.
        if not same_intent(existing, account_id, payload, version.id):
            return Err(IdempotencyConflict())

        return Ok(await report_view(db, existing))

    subscription = await dao_account_subscriptions.by_account_for_update(db, account_id)

    subscription_created = subscription is Empty

    if subscription_created:
        # First commercial relation: pending_activation until a period is approved (§10.2).
        subscription_id = uuid7()
        await dao_account_subscriptions.insert_subscription(
            db, subscription_id, account_id, version.id
        )
    else:
        subscription_id = subscription.id

    await dao_payment_reports.insert_report(
        db,
        {
            "id": payload.operation_id,
            "account_id": account_id,
            "subscription_id": subscription_id,
            "plan_version_id": version.id,
            "periodicity": payload.periodicity,
            "declared_paid_on": payload.declared_paid_on,
            "declared_amount": payload.declared_amount.amount,
            "declared_currency": payload.declared_amount.currency,
            "declared_method": payload.declared_method,
            "declared_reference_last4": payload.declared_reference_last4,
            "declared_note": payload.declared_note,
            "previous_report_id": payload.previous_report_id,
            "submitted_by": user_id,
        },
    )
    row = await dao_payment_reports.get(db, payload.operation_id)

    if subscription_created and device_id is not None:
        # The change log requires an operation receipt from a member device; the
        # receipt also serves as the durable idempotency record of the submit.
        fingerprint = hashlib.sha256(
            payload.model_dump_json(by_alias=True).encode()
        ).digest()
        now = datetime_now()
        await dao_receipts.record(
            db,
            {
                "account_id": account_id,
                "actor_user_id": user_id,
                "operation_id": payload.operation_id,
                "source_device_id": device_id,
                "contract_version": 1,
                "action": "SubmitPaymentReport",
                "entity_type": "payment_report",
                "entity_key": str(payload.operation_id),
                "request_hash": fingerprint,
                "status": "accepted",
                "entity_version": 1,
                "result_json": {
                    "operationId": str(payload.operation_id),
                    "status": "accepted",
                    "entityVersion": 1,
                    "state": None,
                    "error": None,
                },
                "completed_at": now,
                "result_expires_at": now + timedelta(days=90),
                "purged_at": None,
            },
            commit=False,
        )
        await record_operation(
            db,
            OperationAudit(
                account_id=account_id,
                actor_user_id=user_id,
                actor_device_id=device_id,
                action="SubmitPaymentReport",
                object_type="payment_report",
                object_key=str(payload.operation_id),
                outcome="accepted",
                operation_id=payload.operation_id,
                correlation_id=CORRELATION_ID.get() or uuid7(),
                occurred_at=now,
            ),
        )
        await publish_subscription_change(
            db, account_id, user_id, payload.operation_id, now=now
        )

    return Ok(await report_view(db, row))


async def list_reports(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    status: str | None,
    page: int,
    shows: int,
):
    context = await get_account_context(db, credential, account_id, require_device=True)

    match context:
        case Err(error):
            return Err(error)
        case Ok(account):
            pass

    if not account.owner:
        return Err(AccessDenied())

    rows, total = await dao_payment_reports.page_for_account(
        db, account_id, status, page, shows
    )
    items = [await report_view(db, row) for row in rows]

    return Ok(PaginatedResponse[PaymentReportResponse](items=items, total=total))


async def report_detail(
    db: AsyncSession, credential: str | None, account_id: UUID, report_id: UUID
) -> Result[
    PaymentReportDetailResponse,
    InvalidCredential | AccountNotFound | AccessDenied | ReportNotFound,
]:
    context = await get_account_context(db, credential, account_id, require_device=True)

    match context:
        case Err(error):
            return Err(error)
        case Ok(account):
            pass

    if not account.owner:
        return Err(AccessDenied())

    row = await dao_payment_reports.for_account(db, report_id, account_id)

    if row is Empty:
        return Err(ReportNotFound())

    base = await report_view(db, row)
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

    return Ok(PaymentReportDetailResponse(**base.model_dump(), review=outcome))
