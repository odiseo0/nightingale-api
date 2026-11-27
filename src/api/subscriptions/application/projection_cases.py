from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import count_active_members
from src.api.subscriptions.domain.subscriptions import (
    GRACE_DAYS,
    SeatUsageView,
    SubscriptionAdminProjection,
    SubscriptionProjection,
    commercial_availability,
)
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_plan_versions,
    dao_subscription_periods,
    dao_subscription_plans,
)
from src.api.sync.domain.downloads import SyncItem
from src.api.sync.repository.dao import dao_changes, dao_heads
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def subscription_projections(db: AsyncSession, account_id: UUID):
    """Build the members/admin projections from current state; None without a
    commercial relation. Projections are validated models before any commit."""
    subscription = await dao_account_subscriptions.by_account_for_update(db, account_id)

    if subscription is Empty:
        return None

    version = await dao_plan_versions.get(db, subscription.plan_version_id)
    plan = await dao_subscription_plans.get(db, version.plan_id)
    period = await dao_subscription_periods.latest_period(db, subscription.id)
    now = datetime_now()
    ends_at = None if period is Empty else period.ends_at
    status = commercial_availability(subscription.status, ends_at, now)

    grace_ends_at = (
        ends_at + timedelta(days=GRACE_DAYS)
        if ends_at is not None and status in ("grace", "suspended")
        else None
    )
    members = SubscriptionProjection(
        plan_code=plan.code,
        status=status,
        current_period_ends_at=ends_at,
        grace_ends_at=grace_ends_at,
        subscription_version=subscription.version,
        updated_at=subscription.updated_at,
    )
    admin = SubscriptionAdminProjection(
        **members.model_dump(),
        seats=SeatUsageView(
            used=await count_active_members(db, account_id), limit=version.seat_limit
        ),
    )

    return members, admin


async def snapshot_subscription(db: AsyncSession, context) -> list:
    projections = await subscription_projections(db, context.account.id)

    if projections is None:
        return []

    members, admin = projections

    return [
        SyncItem(
            entity_type="subscription",
            entity_key=context.account.id,
            entity_version=members.subscription_version,
            state=members,
        ),
        SyncItem(
            entity_type="subscription_admin",
            entity_key=context.account.id,
            entity_version=admin.subscription_version,
            state=admin,
        ),
    ]


async def publish_subscription_change(
    db: AsyncSession,
    account_id: UUID,
    actor_user_id: UUID,
    operation_id: UUID,
    now=None,
) -> None:
    """Append the commercial change to the sync journal inside the caller's
    transaction (§18.4): availability changes do not touch permission_epoch.

    change_log.actor_user_id is the account owner who drives the commercial
    relation; the deciding operator stays in subscription_reviews and audit.
    """
    projections = await subscription_projections(db, account_id)

    if projections is None:
        return

    members, admin = projections
    head = await dao_heads.lock_account(db, account_id)
    # The journal trigger requires accepted_at to equal the receipt completed_at.
    now = now or datetime_now()
    sequence = await dao_heads.advance(
        db, head, now, permission_changed=False, commit=False
    )
    group = [
        ("subscription", members),
        ("subscription_admin", admin),
    ]
    group_id = uuid7()

    for ordinal, (entity_type, state) in enumerate(group, 1):
        await dao_changes.append(
            db,
            {
                "account_id": account_id,
                "sequence": sequence,
                "ordinal": ordinal,
                "group_id": group_id,
                "group_size": len(group),
                "source_account_id": account_id,
                "actor_user_id": actor_user_id,
                "operation_id": operation_id,
                "entity_type": entity_type,
                "entity_key": str(account_id),
                "entity_version": state.subscription_version,
                "change_kind": "upsert",
                "audience": "members" if entity_type == "subscription" else "owner",
                "projection_json": state.model_dump(mode="json", by_alias=True),
                "previous_starts_at": None,
                "previous_ends_at": None,
                "accepted_at": now,
            },
            commit=False,
        )
