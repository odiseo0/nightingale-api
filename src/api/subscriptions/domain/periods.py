from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import ConfigDict

from src.core.schema import BaseModel

# Civil rules of D22 are evaluated in the account's civil zone (America/Caracas).
CARACAS = ZoneInfo("America/Caracas")

Periodicity = Literal["days_30", "year_1"]

THIRTY_DAYS = timedelta(days=30)


class PeriodModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServicePeriod(PeriodModel):
    starts_at: datetime
    ends_at: datetime
    periodicity: Periodicity


def add_civil_year(day: date) -> date:
    """Same civil date next year; Feb 29 ends on Feb 28 (D22)."""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return day.replace(year=day.year + 1, day=28)


def period_end(starts_at: datetime, periodicity: Periodicity) -> datetime:
    """Exclusive end of the period starting at the given aware instant."""
    if starts_at.tzinfo is None:
        raise ValueError("starts_at must be timezone-aware")

    if periodicity == "days_30":
        return starts_at + THIRTY_DAYS

    local_start = starts_at.astimezone(CARACAS)
    local_end = add_civil_year(local_start.date())
    return local_start.replace(
        year=local_end.year, month=local_end.month, day=local_end.day
    ).astimezone(starts_at.tzinfo)


def next_period_start(
    last_ends_at: datetime | None, approval_instant: datetime
) -> datetime:
    """Early renewal keeps paid days; late renewal starts at approval (D22)."""
    if approval_instant.tzinfo is None:
        raise ValueError("approval_instant must be timezone-aware")

    if last_ends_at is not None and last_ends_at > approval_instant:
        return last_ends_at

    return approval_instant


def compute_period(
    last_ends_at: datetime | None,
    approval_instant: datetime,
    periodicity: Periodicity,
) -> ServicePeriod:
    starts_at = next_period_start(last_ends_at, approval_instant)

    return ServicePeriod(
        starts_at=starts_at,
        ends_at=period_end(starts_at, periodicity),
        periodicity=periodicity,
    )
