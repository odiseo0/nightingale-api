from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid7

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.operator_cases import authenticate_operator
from src.api.subscriptions.domain.plans import (
    OperatorPlanPage,
    OperatorPlanResponse,
    OperatorPlanVersionView,
    OperatorPlanView,
    PlanRetirementRequest,
    PlanVersionCreateRequest,
)
from src.api.subscriptions.repository.dao import (
    dao_plan_versions,
    dao_subscription_plans,
)
from src.api.subscriptions.repository.models import SubscriptionPlan
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class PlanNotFound:
    pass


@dataclass(frozen=True, slots=True)
class PlanRetired:
    pass


@dataclass(frozen=True, slots=True)
class VersionConflict:
    pass


CatalogError = (
    InvalidCredential | AccessDenied | PlanNotFound | PlanRetired | VersionConflict
)


def plan_view(plan: SubscriptionPlan, versions, **overrides) -> OperatorPlanView:
    return OperatorPlanView(
        code=plan.code,
        name=plan.name,
        description=plan.description,
        status=overrides.get("status", plan.status),
        version=overrides.get("version", plan.version),
        versions=[
            OperatorPlanVersionView(
                version=row.version,
                seat_limit=row.seat_limit,
                price_30d_usd=row.price_30d_usd,
                price_year_usd=row.price_year_usd,
                currency=row.currency,
                created_at=row.created_at,
            )
            for row in versions
        ],
    )


async def list_plans(
    db: AsyncSession, token: str | None
) -> Result[OperatorPlanPage, CatalogError]:
    operator = await authenticate_operator(db, token, "catalog")

    match operator:
        case Err(error):
            return Err(error)
        case Ok(_):
            pass

    plans = await dao_subscription_plans.all_plans(db)
    versions = await dao_plan_versions.versions_of(db, [plan.id for plan in plans])
    by_plan: dict = {}
    for row in versions:
        by_plan.setdefault(row.plan_id, []).append(row)

    return Ok(
        OperatorPlanPage(
            items=[plan_view(plan, by_plan.get(plan.id, [])) for plan in plans],
            total=len(plans),
        )
    )


async def create_plan_version(
    db: AsyncSession, token: str | None, code: str, payload: PlanVersionCreateRequest
) -> Result[OperatorPlanResponse, CatalogError]:
    async with transaction(db):
        operator = await authenticate_operator(db, token, "catalog")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(_):
                pass

        plan = await dao_subscription_plans.by_code(db, code)

        if plan is Empty:
            return Err(PlanNotFound())

        if plan.status == "retired":
            return Err(PlanRetired())

        latest = await dao_plan_versions.latest_version(db, plan.id)
        next_version = 1 if latest is Empty else latest.version + 1
        applied = await dao_subscription_plans.apply_update(
            db, plan.id, payload.expected_version, {}
        )

        if not applied:
            return Err(VersionConflict())

        await dao_plan_versions.insert_version(
            db,
            uuid7(),
            plan.id,
            next_version,
            payload.seat_limit,
            payload.price_30d_usd,
            payload.price_year_usd,
        )
        versions = await dao_plan_versions.versions_of(db, [plan.id])

    return Ok(
        OperatorPlanResponse(
            plan=plan_view(plan, versions, version=payload.expected_version + 1)
        )
    )


async def retire_plan(
    db: AsyncSession, token: str | None, code: str, payload: PlanRetirementRequest
) -> Result[OperatorPlanResponse, CatalogError]:
    async with transaction(db):
        operator = await authenticate_operator(db, token, "catalog")

        match operator:
            case Err(error):
                return Err(error)
            case Ok(_):
                pass

        plan = await dao_subscription_plans.by_code(db, code)

        if plan is Empty:
            return Err(PlanNotFound())

        applied = await dao_subscription_plans.apply_update(
            db, plan.id, payload.expected_version, {"status": "retired"}
        )

        if not applied:
            return Err(VersionConflict())

        versions = await dao_plan_versions.versions_of(db, [plan.id])

    return Ok(
        OperatorPlanResponse(
            plan=plan_view(
                plan, versions, status="retired", version=payload.expected_version + 1
            )
        )
    )
