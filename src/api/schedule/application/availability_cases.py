from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.api.accounts.domain.accounts import AccountContext
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.domain.errors import AccessDenied
from src.api.schedule.application.exceptions_cases import daily_day
from src.api.schedule.domain.schedule import AbsoluteInterval
from src.api.schedule.repository.dao import dao_blocks
from src.core import Err, Ok, Result

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def local_instant(day: date, minute: int, zone: ZoneInfo) -> datetime:
    """Require one UTC instant; never choose an offset for a gap or a fold."""
    local = datetime.combine(day, time()) + timedelta(minutes=minute)
    candidates = set()

    # fold and round-trip validation use the standard library's IANA rules.
    # https://docs.python.org/3.15/library/zoneinfo.html#using-zoneinfo
    for fold in (0, 1):
        candidate = local.replace(tzinfo=zone, fold=fold).astimezone(UTC)

        if candidate.astimezone(zone).replace(tzinfo=None) == local:
            candidates.add(candidate)

    if len(candidates) != 1:
        raise ValueError("La hora local requiere una resolución explícita")

    return candidates.pop()


def free_intervals(
    opened: list[AbsoluteInterval], busy: list[AbsoluteInterval],
    start: datetime, end: datetime, duration_minutes: int,
) -> list[AbsoluteInterval]:
    """Return maximal free ranges; an interval query does not reserve them."""
    merged: list[tuple[datetime, datetime]] = []

    for interval in sorted(opened, key=lambda item: item.starts_at):
        left, right = max(start, interval.starts_at), min(end, interval.ends_at)

        if left >= right:
            continue

        if merged and left <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], right))
        else:
            merged.append((left, right))

    for interval in sorted(busy, key=lambda item: item.starts_at):
        remaining: list[tuple[datetime, datetime]] = []

        for left, right in merged:
            if interval.ends_at <= left or right <= interval.starts_at:
                remaining.append((left, right))
                continue

            if left < interval.starts_at:
                remaining.append((left, interval.starts_at))

            if interval.ends_at < right:
                remaining.append((interval.ends_at, right))

        merged = remaining

    result = []

    for left, right in merged:
        rounded_start = left.replace(second=0, microsecond=0)

        if rounded_start < left:
            rounded_start += timedelta(minutes=1)

        rounded_end = right.replace(second=0, microsecond=0)

        if rounded_end - rounded_start >= timedelta(minutes=duration_minutes):
            result.append(AbsoluteInterval(starts_at=rounded_start, ends_at=rounded_end))

    return result


async def available_schedule(
    db: AsyncSession, context: AccountContext, professional_id: UUID,
    start: datetime, end: datetime, duration_minutes: int,
    *, occupied: tuple[AbsoluteInterval, ...] = (),
) -> Result[list[AbsoluteInterval], AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """T22 must read real occupancy under the professional lock for acceptance."""
    try:
        zone = ZoneInfo(context.account.time_zone)
        day = start.astimezone(zone).date()
        last = (end - timedelta(microseconds=1)).astimezone(zone).date()
        opened = []

        while day <= last:
            schedule = await daily_day(db, context, professional_id, day)

            if isinstance(schedule, Err):
                return schedule

            for interval in schedule.value.intervals:
                opened.append(AbsoluteInterval(
                    starts_at=local_instant(day, interval.local_start_minute, zone),
                    ends_at=local_instant(day, interval.local_end_minute, zone),
                ))

            if day == last:
                break

            day += timedelta(days=1)
    except (ValueError, OverflowError, ZoneInfoNotFoundError):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    rows = await dao_blocks.overlapping(db, context.account.id, professional_id, start, end)
    busy = [AbsoluteInterval(starts_at=row.starts_at, ends_at=row.ends_at) for row in rows]

    return Ok(free_intervals(opened, busy + list(occupied), start, end, duration_minutes))


