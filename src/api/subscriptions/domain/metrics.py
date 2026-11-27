from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import ConfigDict, Field

from src.core.schema import BaseModel


class MetricsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanStatusCount(MetricsModel):
    plan_code: str
    status: str
    count: Annotated[int, Field(ge=0)]


class ExpiringSubscription(MetricsModel):
    account_id: UUID
    ends_at: datetime


class PendingReportsSummary(MetricsModel):
    count: Annotated[int, Field(ge=0)]
    oldest_created_at: datetime | None = None


class PlanPeriodicityCount(MetricsModel):
    plan_code: str
    periodicity: str
    count: Annotated[int, Field(ge=0)]


class VerifiedAmount(MetricsModel):
    currency: str
    total: Decimal


class SeatOverrun(MetricsModel):
    account_id: UUID
    used: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1)]


class SubscriptionMetricsResponse(MetricsModel):
    accounts_by_plan: list[PlanStatusCount]
    expiring_soon: list[ExpiringSubscription]
    pending_reports: PendingReportsSummary
    periods_by_plan: list[PlanPeriodicityCount]
    verified_amounts: list[VerifiedAmount]
    seats_over_limit: list[SeatOverrun]
    generated_at: datetime
