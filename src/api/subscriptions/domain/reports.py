from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from src.api.subscriptions.domain.money import Money
from src.api.subscriptions.domain.periods import Periodicity
from src.api.subscriptions.domain.plans import PlanCode
from src.core.schema import BaseModel

ReportStatus = Literal["pending", "approved", "rejected"]

# D24: JPG/PNG/PDF up to 5 MB, one capture per report.
EVIDENCE_CONTENT_TYPES = ("image/jpeg", "image/png", "application/pdf")
EVIDENCE_MAX_BYTES = 5 * 1024 * 1024


class ReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeclaredPayment(ReportModel):
    """What the client states; immutable after submission (§12.5)."""

    paid_on: date
    amount: Money
    method: Annotated[str, Field(min_length=1)]
    # Text, exactly four digits: leading zeros are significant and never unique (§12.6).
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    note: Annotated[str, Field(min_length=1)] | None = None


class PaymentReport(ReportModel):
    report_id: UUID
    account_id: UUID
    plan_code: PlanCode
    periodicity: Periodicity
    declared: DeclaredPayment
    status: ReportStatus = "pending"
    previous_report_id: UUID | None = None
    version: Annotated[int, Field(ge=1)] = 1


class EvidenceMetadata(ReportModel):
    content_type: Literal["image/jpeg", "image/png", "application/pdf"]
    size_bytes: Annotated[int, Field(gt=0, le=EVIDENCE_MAX_BYTES)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ReportNotPendingError(ValueError):
    pass


def ensure_pending(report: PaymentReport) -> None:
    if report.status != "pending":
        raise ReportNotPendingError(f"report is {report.status}")


def decide(
    report: PaymentReport, decision: Literal["approved", "rejected"]
) -> PaymentReport:
    """A decided report is never reopened; corrections are new submissions (§15)."""
    ensure_pending(report)

    return report.model_copy(update={"status": decision, "version": report.version + 1})


def resubmission(report: PaymentReport, new_report_id: UUID) -> PaymentReport:
    """New presentation linked to the previous one, back to pending (§15)."""
    if report.status == "pending":
        raise ReportNotPendingError("a pending report cannot be resubmitted")

    return PaymentReport(
        report_id=new_report_id,
        account_id=report.account_id,
        plan_code=report.plan_code,
        periodicity=report.periodicity,
        declared=report.declared,
        status="pending",
        previous_report_id=report.report_id,
    )


def detect_content_type(content: bytes) -> str | None:
    """Real file signature, never the client Content-Type (OWASP upload rules)."""
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    if content.startswith(b"%PDF-"):
        return "application/pdf"

    return None


class PaymentReportCreateRequest(ReportModel):
    operation_id: UUID
    plan_code: PlanCode
    periodicity: Periodicity
    declared_paid_on: date
    declared_amount: Money
    declared_method: Annotated[str, Field(min_length=1)]
    declared_reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    declared_note: Annotated[str, Field(min_length=1)] | None = None
    previous_report_id: UUID | None = None


class EvidenceView(ReportModel):
    content_type: str
    size_bytes: Annotated[int, Field(gt=0)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    uploaded_at: datetime


class GrantedPeriodView(ReportModel):
    starts_at: datetime
    ends_at: datetime
    periodicity: Periodicity
    sequence: Annotated[int, Field(ge=1)]


class ReviewOutcomeView(ReportModel):
    decision: Literal["approved", "rejected"]
    decided_at: datetime
    granted_period: GrantedPeriodView | None = None
    reason: str | None = None


class PaymentReportResponse(ReportModel):
    report_id: UUID
    plan_code: PlanCode
    periodicity: Periodicity
    status: ReportStatus
    declared: DeclaredPayment
    evidence: EvidenceView | None = None
    previous_report_id: UUID | None = None
    created_at: datetime
    version: Annotated[int, Field(ge=1)]


class PaymentReportDetailResponse(PaymentReportResponse):
    review: ReviewOutcomeView | None = None


class OperatorPaymentReportView(ReportModel):
    report_id: UUID
    account_id: UUID
    plan_code: PlanCode
    periodicity: Periodicity
    status: ReportStatus
    declared: DeclaredPayment
    evidence: EvidenceView | None = None
    previous_report_id: UUID | None = None
    submitted_by: UUID
    created_at: datetime
    version: Annotated[int, Field(ge=1)]


class OperatorPaymentReportPage(ReportModel):
    items: list[OperatorPaymentReportView]
    total: Annotated[int, Field(ge=0)]


class ReferenceWarning(ReportModel):
    """Partial-reference coincidences only warn the operator; they never
    reject or delete anything by themselves (§12.6, D24)."""

    report_id: UUID
    account_id: UUID
    status: ReportStatus
    declared_paid_on: date
    declared_amount: Money


class OperatorPaymentReportDetail(OperatorPaymentReportView):
    review: ReviewOutcomeView | None = None
    resubmissions: list[UUID] = Field(default_factory=list)
    reference_warnings: list[ReferenceWarning] = Field(default_factory=list)
