import hashlib
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import update as sql_update

from src.api.accounts.application.accounts_cases import (
    count_active_members,
    get_account_context,
)
from src.api.accounts.domain.errors import AccountNotFound
from src.api.audit.application.audit_cases import record_operation
from src.api.audit.domain.audit import OperationAudit
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.projection_cases import (
    publish_subscription_change,
)
from src.api.subscriptions.domain.subscriptions import (
    GRACE_DAYS,
    CancellationRequest,
    CurrentPeriodView,
    PlanChangeRequest,
    PlanSummaryView,
    PlanVersionSummaryView,
    SeatUsageView,
    SubscriptionResponse,
    commercial_availability,
)
from src.api.subscriptions.repository.dao import (
    dao_account_subscriptions,
    dao_plan_versions,
    dao_subscription_periods,
    dao_subscription_plans,
)
from src.api.subscriptions.repository.models import AccountSubscription
from src.api.sync.repository.dao import dao_receipts
from src.core import Err, Ok, Result
from src.core.constants import CORRELATION_ID
from src.core.db import transaction
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class SubscriptionNotFound:
    pass


@dataclass(frozen=True, slots=True)
class PlanUnavailable:
    pass


@dataclass(frozen=True, slots=True)
class VersionConflict:
    pass


ChangeError = (
    InvalidCredential
    | AccountNotFound
    | AccessDenied
    | SubscriptionNotFound
    | PlanUnavailable
    | VersionConflict
)


async def subscription_response(db: AsyncSession, subscription) -> SubscriptionResponse:
    version = await dao_plan_versions.get(db, subscription.plan_version_id)
    plan = await dao_subscription_plans.get(db, version.plan_id)
    period = await dao_subscription_periods.latest_period(db, subscription.id)
    now = datetime_now()
    ends_at = None if period is Empty else period.ends_at
    status = commercial_availability(subscription.status, ends_at, now)

    return SubscriptionResponse(
        plan=PlanSummaryView(code=plan.code, name=plan.name),
        plan_version=PlanVersionSummaryView(
            version=version.version,
            seat_limit=version.seat_limit,
            price_30d_usd=version.price_30d_usd,
            price_year_usd=version.price_year_usd,
            currency=version.currency,
        ),
        status=status,
        current_period=None
        if period is Empty
        else CurrentPeriodView(
            starts_at=period.starts_at,
            ends_at=period.ends_at,
            periodicity=period.periodicity,
        ),
        grace_ends_at=ends_at + timedelta(days=GRACE_DAYS)
        if ends_at is not None and status == "grace"
        else None,
        seats=SeatUsageView(
            used=await count_active_members(db, subscription.account_id),
            limit=version.seat_limit,
        ),
        subscription_version=subscription.version,
        updated_at=subscription.updated_at,
    )


async def get_subscription(
    db: AsyncSession, credential: str | None, account_id: UUID
) -> Result[
    SubscriptionResponse,
    InvalidCredential | AccountNotFound | AccessDenied | SubscriptionNotFound,
]:
    context = await get_account_context(db, credential, account_id, require_device=True)

    match context:
        case Err(error):
            return Err(error)
        case Ok(account):
            pass

    if not account.owner:
        return Err(AccessDenied())

    subscription = await dao_account_subscriptions.by_account_for_update(db, account_id)

    if subscription is Empty:
        return Err(SubscriptionNotFound())

    return Ok(await subscription_response(db, subscription))


async def _record_change(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    device_id: UUID,
    operation_id: UUID,
    action: str,
    subscription_version: int,
    now,
) -> None:
    await dao_receipts.record(
        db,
        {
            "account_id": account_id,
            "actor_user_id": user_id,
            "operation_id": operation_id,
            "source_device_id": device_id,
            "contract_version": 1,
            "action": action,
            "entity_type": "subscription",
            "entity_key": str(account_id),
            "request_hash": hashlib.sha256(
                f"{action}:{account_id}:{operation_id}".encode()
            ).digest(),
            "status": "accepted",
            "entity_version": subscription_version,
            "result_json": {
                "operationId": str(operation_id),
                "status": "accepted",
                "entityVersion": subscription_version,
                "state": None,
                "error": None,
            },
            "completed_at": now,
            "result_expires_at": now + timedelta(days=90),
            "purged_at": None,
        },
        commit=False,
    )
    await record_operation(
        db,
        OperationAudit(
            account_id=account_id,
            actor_user_id=user_id,
            actor_device_id=device_id,
            action=action,
            object_type="subscription",
            object_key=str(account_id),
            outcome="accepted",
            operation_id=operation_id,
            correlation_id=CORRELATION_ID.get() or uuid7(),
            occurred_at=now,
        ),
    )
    await publish_subscription_change(db, account_id, user_id, operation_id, now=now)


async def _apply_change(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    device_id: UUID,
    operation_id: UUID,
    expected_version: int,
    action: str,
    changes: dict,
) -> Result[SubscriptionResponse, SubscriptionNotFound | VersionConflict]:
    subscription = await dao_account_subscriptions.by_account_for_update(db, account_id)

    if subscription is Empty:
        return Err(SubscriptionNotFound())

    if subscription.version != expected_version:
        return Err(VersionConflict())

    now = datetime_now()
    await db.execute(
        sql_update(AccountSubscription)
        .where(AccountSubscription.id == subscription.id)
        .values(**changes, version=expected_version + 1, updated_at=now)
    )
    await _record_change(
        db,
        account_id,
        user_id,
        device_id,
        operation_id,
        action,
        expected_version + 1,
        now,
    )
    updated = await dao_account_subscriptions.by_account_for_update(db, account_id)

    return Ok(await subscription_response(db, updated))


async def change_plan(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    device_id: UUID,
    payload: PlanChangeRequest,
) -> Result[
    SubscriptionResponse, SubscriptionNotFound | PlanUnavailable | VersionConflict
]:
    """D24: no proration; the new plan and price apply from the next approved
    period. A lower seat limit never deactivates members (D21); it only blocks
    new additions through the seat check."""
    async with transaction(db):
        plan = await dao_subscription_plans.by_code(db, payload.plan_code)

        if plan is Empty or plan.status == "retired":
            return Err(PlanUnavailable())

        version = await dao_plan_versions.latest_version(db, plan.id)

        return await _apply_change(
            db,
            account_id,
            user_id,
            device_id,
            payload.operation_id,
            payload.expected_version,
            "ChangeSubscriptionPlan",
            {"plan_version_id": version.id},
        )


async def cancel_subscription(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID,
    device_id: UUID,
    payload: CancellationRequest,
) -> Result[SubscriptionResponse, SubscriptionNotFound | VersionConflict]:
    """Cancelling stops the ordinary renewal; paid time and data are kept (§16.3)."""
    async with transaction(db):
        return await _apply_change(
            db,
            account_id,
            user_id,
            device_id,
            payload.operation_id,
            payload.expected_version,
            "CancelSubscription",
            {"status": "cancelled"},
        )


async def change_plan_for_owner(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    payload: PlanChangeRequest,
) -> Result[SubscriptionResponse, ChangeError]:
    return await _owner_change(db, credential, account_id, payload, change_plan)


async def cancel_for_owner(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    payload: CancellationRequest,
) -> Result[SubscriptionResponse, ChangeError]:
    return await _owner_change(db, credential, account_id, payload, cancel_subscription)


async def _owner_change(db, credential, account_id, payload, case):
    async with transaction(db):
        context = await get_account_context(
            db, credential, account_id, require_device=True
        )

        match context:
            case Err(error):
                return Err(error)
            case Ok(account):
                pass

        if not account.owner:
            return Err(AccessDenied())

    return await case(
        db, account_id, account.actor.user_id, account.actor.device_id, payload
    )
