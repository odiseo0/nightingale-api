from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from src.api.billing.domain.money import (
    BalanceState,
    BcvRate,
    Currency,
    usd_to_ves,
    ves_to_usd,
)
from src.core.schema import BaseModel

ReportStatus = Literal["pending", "approved", "rejected"]
PaymentOrigin = Literal["patient_report", "staff_entry"]
PaymentStatus = Literal["active", "annulled"]
GrantAction = Literal["read_charge", "submit_report", "read_result", "read_receipt"]

# D28 reuses the D24 capture policy: JPG/PNG/PDF up to 5 MB, one capture per report.
EVIDENCE_CONTENT_TYPES = ("image/jpeg", "image/png", "application/pdf")
EVIDENCE_MAX_BYTES = 5 * 1024 * 1024


class PaymentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeclaredPayment(PaymentModel):
    """What the patient states; immutable after submission (§10.4, D26)."""

    paid_on: date
    amount: Annotated[Decimal, Field(gt=0)]
    currency: Currency
    method: Annotated[str, Field(min_length=1)]
    # Optional and always partial; never full bank numbers (D26).
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    note: Annotated[str, Field(min_length=1)] | None = None

    @field_validator("amount")
    @classmethod
    def _two_places(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("amount must be finite")
        exponent = value.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise ValueError("amount admits at most 2 decimal places")
        return value


class PatientPaymentReport(PaymentModel):
    report_id: UUID
    account_id: UUID
    charge_id: UUID
    patient_id: UUID
    grant_id: UUID
    declared: DeclaredPayment
    status: ReportStatus = "pending"
    previous_report_id: UUID | None = None
    version: Annotated[int, Field(ge=1)] = 1


class ReportNotPendingError(ValueError):
    pass


def ensure_pending(report: PatientPaymentReport) -> None:
    if report.status != "pending":
        raise ReportNotPendingError(f"report is {report.status}")


def decide(
    report: PatientPaymentReport, decision: Literal["approved", "rejected"]
) -> PatientPaymentReport:
    """A decided report is never reopened; corrections are new submissions (§10.4)."""
    ensure_pending(report)

    return report.model_copy(update={"status": decision, "version": report.version + 1})


def resubmission(
    report: PatientPaymentReport, new_report_id: UUID, declared: DeclaredPayment
) -> PatientPaymentReport:
    """New presentation linked to the rejected one; the original keeps its history."""
    if report.status == "pending":
        raise ReportNotPendingError("a pending report cannot be resubmitted")

    return PatientPaymentReport(
        report_id=new_report_id,
        account_id=report.account_id,
        charge_id=report.charge_id,
        patient_id=report.patient_id,
        grant_id=report.grant_id,
        declared=declared,
        status="pending",
        previous_report_id=report.report_id,
    )


class VerifiedPayment(PaymentModel):
    """What the reviewer verified; never overwrites the declaration (§12.2)."""

    paid_on: date
    amount: Annotated[Decimal, Field(gt=0)]
    currency: Currency
    method: Annotated[str, Field(min_length=1)]
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    internal_note: Annotated[str, Field(min_length=1)] | None = None


class Conversion(PaymentModel):
    """Explicit prior conversion snapshot for a payment in another currency (D25)."""

    amount_usd: Annotated[Decimal, Field(gt=0)]
    exchange_rate: Annotated[Decimal, Field(gt=0)]
    exchange_rate_date: date
    exchange_rate_source: Annotated[str, Field(min_length=1)]


class CurrencyMismatchError(ValueError):
    pass


def convert_verified(
    verified: VerifiedPayment, charge_currency: Currency, rate: BcvRate | None
) -> tuple[Decimal, Conversion | None]:
    """Applied amount in the charge currency plus its conversion snapshot.

    A payment in the charge currency needs no rate; USD paid in VES (or the
    reverse) requires the BCV rate verified by the reviewer and is never
    revalued afterwards (§14.2–§14.3, D25).
    """
    if verified.currency == charge_currency:
        return verified.amount, None

    if rate is None:
        raise CurrencyMismatchError(
            "a payment in another currency requires the BCV rate"
        )

    if charge_currency == "USD":
        applied = ves_to_usd(verified.amount, rate)
        usd_amount = applied
    else:
        applied = usd_to_ves(verified.amount, rate)
        usd_amount = verified.amount

    conversion = Conversion(
        amount_usd=usd_amount,
        exchange_rate=rate.rate_ves_per_usd,
        exchange_rate_date=rate.rate_date,
        exchange_rate_source=rate.source,
    )

    return applied, conversion


class PatientPayment(PaymentModel):
    payment_id: UUID
    account_id: UUID
    charge_id: UUID
    patient_id: UUID
    origin: PaymentOrigin
    origin_report_id: UUID | None = None
    amount: Annotated[Decimal, Field(gt=0)]
    currency: Currency
    conversion: Conversion | None = None
    paid_on: date
    method: Annotated[str, Field(min_length=1)]
    reference_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    status: PaymentStatus = "active"
    annulled_at: datetime | None = None
    annulled_by: UUID | None = None
    annulment_reason: Annotated[str, Field(min_length=1)] | None = None
    registered_by: UUID
    version: Annotated[int, Field(ge=1)] = 1


def new_payment(
    payment_id: UUID,
    report: PatientPaymentReport | None,
    charge_id: UUID,
    account_id: UUID,
    patient_id: UUID,
    verified: VerifiedPayment,
    charge_currency: Currency,
    rate: BcvRate | None,
    registered_by: UUID,
) -> PatientPayment:
    """Approved payment applied to a single charge (D26); origin stays distinguishable."""
    applied, conversion = convert_verified(verified, charge_currency, rate)
    origin: PaymentOrigin = "patient_report" if report is not None else "staff_entry"

    return PatientPayment(
        payment_id=payment_id,
        account_id=account_id,
        charge_id=charge_id,
        patient_id=patient_id,
        origin=origin,
        origin_report_id=report.report_id if report is not None else None,
        amount=applied,
        currency=charge_currency,
        conversion=conversion,
        paid_on=verified.paid_on,
        method=verified.method,
        reference_last4=verified.reference_last4,
        registered_by=registered_by,
    )


def annul(
    payment: PatientPayment, now: datetime, actor: UUID, reason: str
) -> PatientPayment:
    """Annulment excludes the payment from the active balance without deleting
    history and never claims a refund (§13.5, D27)."""
    if payment.status == "annulled":
        raise ValueError("payment is already annulled")
    if now.tzinfo is None:
        raise ValueError("instants must be timezone-aware")

    return payment.model_copy(
        update={
            "status": "annulled",
            "annulled_at": now,
            "annulled_by": actor,
            "annulment_reason": reason,
            "version": payment.version + 1,
        }
    )


class PatientBillingGrant(PaymentModel):
    """Limited patient access by concrete object and action; the UUID alone
    authorizes nothing (D28)."""

    grant_id: UUID
    account_id: UUID
    patient_id: UUID
    appointment_id: UUID | None = None
    charge_id: UUID | None = None
    actions: Annotated[list[GrantAction], Field(min_length=1)]
    expires_at: datetime
    revoked_at: datetime | None = None

    def usable(self, action: GrantAction, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("instants must be timezone-aware")

        return (
            self.revoked_at is None and now < self.expires_at and action in self.actions
        )


class GrantObjectRequiredError(ValueError):
    pass


def ensure_grant_object(grant: PatientBillingGrant) -> None:
    if grant.appointment_id is None and grant.charge_id is None:
        raise GrantObjectRequiredError("a grant needs a concrete appointment or charge")


class GrantCreateRequest(PaymentModel):
    """Staff request for a limited patient link; the client operationId becomes
    the grant id, so a retry never creates a second grant."""

    operation_id: UUID
    patient_id: UUID
    appointment_id: UUID | None = None
    charge_id: UUID | None = None
    actions: Annotated[list[GrantAction], Field(min_length=1)]

    @model_validator(mode="after")
    def concrete_object(self) -> Self:
        if self.appointment_id is None and self.charge_id is None:
            raise ValueError("a grant needs a concrete appointment or charge")
        return self


class GrantIssuedResponse(PaymentModel):
    grant_id: UUID
    secret: str | None
    duplicate: bool = False
    actions: list[GrantAction]
    expires_at: datetime


class GrantResponse(PaymentModel):
    grant_id: UUID
    patient_id: UUID
    appointment_id: UUID | None = None
    charge_id: UUID | None = None
    actions: list[GrantAction]
    expires_at: datetime
    revoked_at: datetime | None = None
    status: Literal["active", "expired", "revoked"]


class PatientChargeView(PaymentModel):
    """Minimal patient projection (§9.3): no internal notes, no other charges,
    no clinical content."""

    charge_id: UUID
    description: str
    amount: Decimal
    currency: str
    outstanding: Decimal
    balance_state: BalanceState
    issued_at: datetime
    review_state: ReportStatus | None = None


class GrantRevokeRequest(PaymentModel):
    operation_id: UUID


class BillingPaymentProjection(PaymentModel):
    """Financial delta/snapshot projection by reference (§16.1); never bytes,
    bank data, internal notes or conversion internals."""

    payment_id: UUID
    charge_id: UUID
    patient_id: UUID
    origin: PaymentOrigin
    amount: Decimal
    currency: str
    status: PaymentStatus
    paid_on: date
    registered_by: UUID
    updated_at: datetime
