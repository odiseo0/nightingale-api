from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from src.api.subscriptions.domain.money import BcvRate, Money, _exact_amount
from src.api.subscriptions.domain.reports import PaymentReport, decide
from src.core.schema import BaseModel

ReviewDecision = Literal["approved", "rejected"]


class ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VerifiedPayment(ReviewModel):
    """What the operator settles at review; never overwrites the declaration (§12.5)."""

    paid_on: date
    amount: Annotated[Decimal, Field(gt=0)]
    currency: Literal["VES", "USD"]

    @model_validator(mode="after")
    def _two_places(self):
        _exact_amount(self.amount, 2)
        return self


class SubscriptionReview(ReviewModel):
    report_id: UUID
    operator_id: UUID
    decision: ReviewDecision
    verified: VerifiedPayment | None = None
    bcv_rate: BcvRate | None = None
    reason: Annotated[str, Field(min_length=1)] | None = None

    @model_validator(mode="after")
    def _coherent_decision(self):
        if self.decision == "approved":
            if self.verified is None:
                raise ValueError("approval requires verified payment data")
            # A VES payment needs the BCV rate applied; USD does not use one (D22).
            if self.verified.currency == "VES" and self.bcv_rate is None:
                raise ValueError("a VES approval requires the applied BCV rate")
        elif self.reason is None:
            raise ValueError("rejection requires a reason")
        return self


class PaymentMismatchError(ValueError):
    pass


def apply_review(report: PaymentReport, review: SubscriptionReview) -> PaymentReport:
    """Return the report in its decided state; one review, one effect (§11.6)."""
    if review.report_id != report.report_id:
        raise ValueError("review does not belong to this report")

    return decide(report, review.decision)


def ensure_full_payment(review: SubscriptionReview, due: Money) -> None:
    """Only the exact due amount approves a full period; partial and excess payments
    are rejected instead (D24)."""
    if review.decision != "approved" or review.verified is None:
        raise ValueError("only approvals are checked against the due amount")

    verified = review.verified
    if verified.currency == due.currency:
        matches = verified.amount == due.amount
    elif verified.currency == "VES":
        if review.bcv_rate is None:
            raise ValueError("a VES approval requires the applied BCV rate")
        expected = (due.amount * review.bcv_rate.rate_ves_per_usd).quantize(
            Decimal("0.01"), rounding="ROUND_HALF_UP"
        )
        matches = verified.amount == expected
    else:
        # Due amounts come from the USD catalog; a VES due with USD verified is out of scope.
        raise PaymentMismatchError("verified currency cannot be compared with the due amount")

    if not matches:
        raise PaymentMismatchError("verified amount does not match the due amount")


class ApprovalRequest(ReviewModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]
    verified_paid_on: date
    verified_amount: Annotated[Decimal, Field(gt=0)]
    verified_currency: Literal["VES", "USD"]
    bcv_rate_id: UUID | None = None

    @model_validator(mode="after")
    def _two_places(self):
        _exact_amount(self.verified_amount, 2)
        return self


class GrantedPeriodResult(ReviewModel):
    starts_at: datetime
    ends_at: datetime
    periodicity: str
    sequence: Annotated[int, Field(ge=1)]


class SubscriptionStateView(ReviewModel):
    status: str
    subscription_version: Annotated[int, Field(ge=1)]


class ApprovalResultResponse(ReviewModel):
    report_id: UUID
    decision: Literal["approved"] = "approved"
    granted_period: GrantedPeriodResult
    subscription: SubscriptionStateView
    duplicate: bool = False


class RejectionRequest(ReviewModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]
    # Safe administrative reason: no secrets or full banking data (§15).
    reason: Annotated[str, Field(min_length=1)]


class RejectionResultResponse(ReviewModel):
    report_id: UUID
    decision: Literal["rejected"] = "rejected"
    reason: str
    duplicate: bool = False
