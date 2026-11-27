from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.subscriptions.domain.subscriptions import commercial_availability
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_subscription_periods,
)
from src.core import Err, Ok, Result
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class CommerciallySuspended:
    pass


async def ensure_commercially_available(
    db: AsyncSession, account_id: UUID
) -> Result[None, CommerciallySuspended]:
    """Commercial gate for operational writes (D24, §17): suspension blocks new
    operational writes; grace keeps normal service; reads, renewal and the
    subscription routes are never gated here. It runs after personal
    authorization and changes neither roles nor tokens. Accounts without a
    commercial relation are not gated (enforcement of never-paid accounts is a
    separate product decision)."""
    subscription = await dao_account_subscriptions.by_account(db, account_id)

    if subscription is Empty:
        return Ok(None)

    period = await dao_subscription_periods.latest_period(db, subscription.id)
    status = commercial_availability(
        subscription.status,
        None if period is Empty else period.ends_at,
        datetime_now(),
    )

    # "cancelled" only remains after the paid time ends (§16.3); both states
    # mean there is no commercial vigencia left.
    if status in ("suspended", "cancelled"):
        return Err(CommerciallySuspended())

    return Ok(None)
