from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from src.api.subscriptions.domain.money import ROUNDING_RULE, _exact_amount
from src.api.subscriptions.domain.periods import Periodicity
from src.api.subscriptions.domain.plans import PlanCode
from src.core.schema import BaseModel


class QuoteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BcvRateCreateRequest(QuoteModel):
    operation_id: UUID
    rate_date: date
    rate_ves_per_usd: Annotated[Decimal, Field(gt=0)]
    source: Annotated[str, Field(min_length=1)]

    @field_validator("rate_ves_per_usd")
    @classmethod
    def _six_places(cls, value: Decimal) -> Decimal:
        return _exact_amount(value, 6)


class BcvRateResponse(QuoteModel):
    rate_id: UUID
    rate_date: date
    rate_ves_per_usd: Decimal
    source: str
    registered_at: datetime


class BcvRatePage(QuoteModel):
    items: list[BcvRateResponse]
    total: Annotated[int, Field(ge=0)]


class QuoteRequest(QuoteModel):
    operation_id: UUID
    plan_code: PlanCode
    periodicity: Periodicity


class QuoteResponse(QuoteModel):
    quote_id: UUID
    plan_code: PlanCode
    plan_version: Annotated[int, Field(ge=1)]
    periodicity: Periodicity
    amount_usd: Decimal
    bcv_rate: Decimal
    bcv_rate_date: date
    bcv_rate_source: str
    amount_ves: Decimal
    rounding_rule: Literal["ROUND_HALF_UP"] = ROUNDING_RULE
    quoted_at: datetime
