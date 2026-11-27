from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from src.api.subscriptions.domain.money import _exact_amount
from src.api.subscriptions.domain.periods import Periodicity
from src.core.schema import BaseModel

PlanCode = Literal["independent", "small_practice", "medical_center"]
PlanStatus = Literal["available", "retired"]


class PlanModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanVersion(PlanModel):
    """Historical price/seat configuration; rows are never edited (§7.3)."""

    version: Annotated[int, Field(ge=1)]
    seat_limit: Annotated[int, Field(ge=1)]
    price_30d_usd: Annotated[Decimal, Field(gt=0)]
    price_year_usd: Annotated[Decimal, Field(gt=0)]
    currency: Literal["USD"] = "USD"

    @field_validator("price_30d_usd", "price_year_usd")
    @classmethod
    def _two_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 2)


class Plan(PlanModel):
    code: PlanCode
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    status: PlanStatus = "available"


# Initial catalog decided in D21 (2026-11-26); version 1 of each plan.
INITIAL_PLAN_VERSIONS: dict[PlanCode, PlanVersion] = {
    "independent": PlanVersion(
        version=1, seat_limit=2, price_30d_usd=Decimal("18.00"), price_year_usd=Decimal("100.00")
    ),
    "small_practice": PlanVersion(
        version=1, seat_limit=5, price_30d_usd=Decimal("24.00"), price_year_usd=Decimal("240.00")
    ),
    "medical_center": PlanVersion(
        version=1, seat_limit=20, price_30d_usd=Decimal("75.00"), price_year_usd=Decimal("500.00")
    ),
}


def price_for(version: PlanVersion, periodicity: Periodicity) -> Decimal:
    if periodicity == "days_30":
        return version.price_30d_usd

    return version.price_year_usd


class PlanVersionCreateRequest(PlanModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]
    seat_limit: Annotated[int, Field(ge=1)]
    price_30d_usd: Annotated[Decimal, Field(gt=0)]
    price_year_usd: Annotated[Decimal, Field(gt=0)]

    @field_validator("price_30d_usd", "price_year_usd")
    @classmethod
    def _two_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 2)


class PlanRetirementRequest(PlanModel):
    operation_id: UUID
    expected_version: Annotated[int, Field(ge=1)]


class OperatorPlanVersionView(PlanModel):
    version: Annotated[int, Field(ge=1)]
    seat_limit: Annotated[int, Field(ge=1)]
    price_30d_usd: Decimal
    price_year_usd: Decimal
    currency: Literal["USD"]
    created_at: datetime


class OperatorPlanView(PlanModel):
    code: PlanCode
    name: str
    description: str
    status: PlanStatus
    version: Annotated[int, Field(ge=1)]
    versions: list[OperatorPlanVersionView]


class OperatorPlanResponse(PlanModel):
    plan: OperatorPlanView


class OperatorPlanPage(PlanModel):
    items: list[OperatorPlanView]
    total: Annotated[int, Field(ge=0)]
