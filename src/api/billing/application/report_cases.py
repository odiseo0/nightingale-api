from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID, uuid7

from pydantic import ConfigDict, Field

from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.billing.application.evidence_cases import (
    EvidenceAlreadyPresent,
    store_report_evidence,
)
from src.api.billing.application.patient_cases import GrantNotUsable, usable_grant
from src.api.billing.domain.payments import (
    EVIDENCE_MAX_BYTES,
    PatientBillingGrant,
)
from src.api.billing.repository.dao import (
    dao_charges,
    dao_payments,
    dao_reports,
    dao_reviews,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.services.private_evidence import validate_capture
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.billing.repository.models import PatientPaymentReport


class ReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatientReportSubmit(ReportModel):
    """Required declaration of D26; the capture travels in the same request."""

    operation_id: UUID
    charge_id: UUID
    paid_on: date
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2, allow_inf_nan=False)]
    currency: Literal["USD", "VES"]
    method: Annotated[str, Field(min_length=1)]
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    note: Annotated[str, Field(min_length=1)] | None = None
    previous_report_id: UUID | None = None


class PatientReportView(ReportModel):
    report_id: UUID
    status: Literal["pending", "approved", "rejected"]
    declared_paid_on: date
    declared_amount: Decimal
    declared_currency: str
    declared_method: str
    previous_report_id: UUID | None = None
    created_at: datetime
    duplicate: bool = False


class PatientReportResult(ReportModel):
    """Visible outcome only: never the internal note nor the reviewer identity."""

    decision: Literal["approved", "rejected"]
    decided_at: datetime
    payment_amount: Decimal | None = None
    payment_currency: str | None = None
    payment_paid_on: date | None = None
    reason: str | None = None


class PatientReportDetail(PatientReportView):
    result: PatientReportResult | None = None


@dataclass(frozen=True, slots=True)
class ReportRejected:
    reason: str


@dataclass(frozen=True, slots=True)
class ReportNotFound:
    pass


def _view(row: PatientPaymentReport, duplicate: bool = False) -> PatientReportView:
    return PatientReportView(
        report_id=row.id,
        status=row.status,
        declared_paid_on=row.declared_paid_on,
        declared_amount=row.declared_amount,
        declared_currency=row.declared_currency,
        declared_method=row.declared_method,
        previous_report_id=row.previous_report_id,
        created_at=row.created_at,
        duplicate=duplicate,
    )


async def _granted_charge(
    db: AsyncSession, grant: PatientBillingGrant, charge_id: UUID
):
    """The report target must be inside the grant scope: its own charge, or an
    issued charge of its anchored appointment (§9.2)."""
    charge = await dao_charges.by_id_in_account(db, charge_id, grant.account_id)

    if (
        charge is Empty
        or charge.patient_id != grant.patient_id
        or charge.status == "draft"
    ):
        return None

    if grant.charge_id is not None:
        return charge if grant.charge_id == charge_id else None

    if charge.appointment_id != grant.appointment_id:
        return None

    return charge


async def submit_report(
    db: AsyncSession, secret: str | None, data: PatientReportSubmit, content: bytes
) -> Result[PatientReportView, GrantNotUsable | ReportRejected]:
    """Submission creates a pending report without any balance effect (§10);
    a lost response recovers the same report by its operation id."""
    checked = validate_capture(content, EVIDENCE_MAX_BYTES)

    if isinstance(checked, Err):
        return Err(ReportRejected(checked.error.reason))

    async with transaction(db):
        grant = await usable_grant(db, secret, "submit_report")

        if isinstance(grant, Err):
            return grant

        scope = grant.value
        existing = await dao_reports.by_id_in_account(
            db, data.operation_id, scope.account_id
        )

        if existing is not Empty:
            if existing.grant_id != scope.grant_id:
                return Err(ReportNotFound())
            return Ok(_view(existing, duplicate=True))

        charge = await _granted_charge(db, scope, data.charge_id)

        if charge is None:
            return Err(ReportNotFound())

        if data.previous_report_id is not None:
            previous = await dao_reports.by_id_in_account(
                db, data.previous_report_id, scope.account_id
            )

            if previous is Empty or previous.status != "rejected":
                return Err(ReportRejected("invalid_previous_report"))

        await dao_reports.insert_report(
            db,
            {
                "id": data.operation_id,
                "account_id": scope.account_id,
                "charge_id": charge.id,
                "patient_id": scope.patient_id,
                "grant_id": scope.grant_id,
                "declared_paid_on": data.paid_on,
                "declared_amount": data.amount,
                "declared_currency": data.currency,
                "declared_method": data.method,
                "declared_reference_last4": data.reference_last4,
                "declared_note": data.note,
                "previous_report_id": data.previous_report_id,
            },
        )
        await record_control(
            db,
            ControlAudit(
                account_id=scope.account_id,
                action="SubmitPatientPaymentReport",
                object_type="patient_payment_report",
                object_key=str(data.operation_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=datetime_now(),
            ),
        )
        inserted = await dao_reports.by_id_in_account(
            db, data.operation_id, scope.account_id
        )
        view = _view(inserted)

    # Bytes are written outside the report transaction; a failure leaves an
    # orphan file without any financial effect (§11.1).
    stored = await store_report_evidence(
        db, scope.account_id, data.operation_id, content
    )

    if isinstance(stored, Err) and not isinstance(stored.error, EvidenceAlreadyPresent):
        return Err(
            ReportRejected(
                stored.error.reason if hasattr(stored.error, "reason") else "evidence"
            )
        )

    return Ok(view)


async def list_own_reports(
    db: AsyncSession, secret: str | None
) -> Result[dict[str, object], GrantNotUsable]:
    grant = await usable_grant(db, secret, "read_result")

    if isinstance(grant, Err):
        return grant

    scope = grant.value
    rows, _ = await dao_reports.page_inbox(
        db,
        scope.account_id,
        1,
        100,
        charge_id=scope.charge_id,
        patient_id=scope.patient_id,
    )
    visible = [
        row
        for row in rows
        if scope.charge_id is not None
        or row.grant_id == scope.grant_id
        or await _granted_charge(db, scope, row.charge_id) is not None
    ]

    return Ok({"items": [_view(row) for row in visible], "total": len(visible)})


async def read_own_report(
    db: AsyncSession, secret: str | None, report_id: UUID
) -> Result[PatientReportDetail, GrantNotUsable | ReportNotFound]:
    grant = await usable_grant(db, secret, "read_result")

    if isinstance(grant, Err):
        return grant

    scope = grant.value
    row = await dao_reports.by_id_in_account(db, report_id, scope.account_id)

    if (
        row is Empty
        or (scope.charge_id is not None and row.charge_id != scope.charge_id)
        or (
            scope.charge_id is None
            and row.grant_id != scope.grant_id
            and await _granted_charge(db, scope, row.charge_id) is None
        )
    ):
        return Err(ReportNotFound())

    result = None
    review = await dao_reviews.by_report(db, row.id)

    if review is not Empty:
        paid = None

        if review.decision == "approved":
            payments = await dao_payments.of_charge(db, row.charge_id, scope.account_id)
            paid = next((p for p in payments if p.origin_report_id == row.id), None)
        result = PatientReportResult(
            decision=review.decision,
            decided_at=review.created_at,
            payment_amount=None if paid is None else paid.amount,
            payment_currency=None if paid is None else paid.currency,
            payment_paid_on=None if paid is None else paid.paid_on,
            reason=review.reason if review.decision == "rejected" else None,
        )

    return Ok(PatientReportDetail(**_view(row).model_dump(), result=result))
