from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.accounts_cases import count_active_members
from src.api.subscriptions.domain.subscriptions import SeatUsage
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_plan_versions,
)
from src.core import Err, Ok, Result
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class SeatLimitReached:
    used: int
    limit: int


async def ensure_seat_available(
    db: AsyncSession, account_id: UUID
) -> Result[None, SeatLimitReached]:
    """Check the plan seat limit inside the caller's transaction (D21, §8.3).

    The subscription row lock serializes seat-consuming operations of the same
    account, so two concurrent acceptances of the last seat have one winner.
    Accounts without a commercial relation are not limited here; commercial
    enforcement is a separate concern (T24).
    """
    subscription = await dao_account_subscriptions.by_account_for_update(db, account_id)

    if subscription is Empty:
        return Ok(None)

    version = await dao_plan_versions.get(db, subscription.plan_version_id)

    if version is Empty:
        return Ok(None)

    usage = SeatUsage(
        used=await count_active_members(db, account_id), limit=version.seat_limit
    )

    if not usage.can_add():
        return Err(SeatLimitReached(used=usage.used, limit=usage.limit))

    return Ok(None)
