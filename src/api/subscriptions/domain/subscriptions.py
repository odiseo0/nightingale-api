from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from src.core.schema import BaseModel

SubscriptionStatus = Literal[
    "pending_activation", "active", "grace", "suspended", "cancelled"
]

# Grace decided in D24 (2026-11-26): 7 days of normal service after the period ends.
GRACE_DAYS = 7


class SubscriptionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SeatUsage(SubscriptionModel):
    """Seats count active unique memberships per account, owner included (D21)."""

    used: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1)]

    @property
    def available(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def over_limit(self) -> bool:
        return self.used > self.limit

    def can_add(self) -> bool:
        # Over-limit accounts keep their members but cannot add or reactivate (D21).
        return self.used < self.limit


def commercial_availability(
    status: SubscriptionStatus,
    current_period_ends_at: datetime | None,
    now: datetime,
) -> SubscriptionStatus:
    """Effective commercial condition from server dates, not just the stored label (§10.2)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    if current_period_ends_at is None:
        return "cancelled" if status == "cancelled" else "pending_activation"

    # Cancellation stops the ordinary renewal but never cuts paid time (§16.3).
    if now < current_period_ends_at:
        return "active"

    if status == "cancelled":
        return "cancelled"

    if now < current_period_ends_at + timedelta(days=GRACE_DAYS):
        return "grace"

    return "suspended"


class SubscriptionProjection(SubscriptionModel):
    """Minimal commercial availability for members (§18.1); never reports,
    rates, review reasons or evidence."""

    plan_code: str
    status: SubscriptionStatus
    current_period_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None
    subscription_version: Annotated[int, Field(ge=1)]
    updated_at: datetime


class SeatUsageView(SubscriptionModel):
    used: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1)]


class SubscriptionAdminProjection(SubscriptionProjection):
    """Owner-only administration view: seat limit and consumption (§18.2)."""

    seats: SeatUsageView


class CurrentPeriodView(SubscriptionModel):
    starts_at: datetime
    ends_at: datetime
    periodicity: str


class PlanSummaryView(SubscriptionModel):
    code: str
    name: str


class PlanVersionSummaryView(SubscriptionModel):
    version: Annotated[int, Field(ge=1)]
    seat_limit: Annotated[int, Field(ge=1)]
    price_30d_usd: Decimal
    price_year_usd: Decimal
    currency: str


class SubscriptionResponse(SubscriptionModel):
    plan: PlanSummaryView
    plan_version: PlanVersionSummaryView
    status: SubscriptionStatus
    current_period: CurrentPeriodView | None = None
    grace_ends_at: datetime | None = None
    seats: SeatUsageView
    subscription_version: Annotated[int, Field(ge=1)]
    updated_at: datetime


class PlanChangeRequest(SubscriptionModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]
    plan_code: str


class CancellationRequest(SubscriptionModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]
