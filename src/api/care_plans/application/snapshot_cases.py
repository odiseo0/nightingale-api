from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.care_plans.application.plan_cases import (
    action_response,
    goal_response,
    plan_response,
    review_response,
)
from src.api.care_plans.repository.dao import (
    dao_care_plan_actions,
    dao_care_plan_goals,
    dao_care_plan_reviews,
    dao_care_plans,
)
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_care_plans(
    db: AsyncSession, context: AccountContext
) -> list[SyncItem]:
    account_id = context.account.id
    items: list[SyncItem] = []

    for plan in await dao_care_plans.valid_snapshot(db, account_id):
        state = plan_response(plan)
        items.append(
            SyncItem(
                entity_type="care_plan",
                entity_key=plan.id,
                entity_version=plan.version,
                state=state,
            )
        )
        for goal in (await dao_care_plan_goals.get_multi(
            db, where={"account_id": account_id, "plan_id": plan.id, "record_status": "valid"},
            shows=None, ordering=[("date_added", False), ("id", False)], include_total=False,
        ))[0]:
            items.append(
                SyncItem(
                    entity_type="care_plan_goal",
                    entity_key=goal.id,
                    entity_version=goal.version,
                    state=goal_response(goal),
                )
            )
        for action in (await dao_care_plan_actions.get_multi(
            db, where={"account_id": account_id, "plan_id": plan.id, "record_status": "valid"},
            shows=None, ordering=[("date_added", False), ("id", False)], include_total=False,
        ))[0]:
            items.append(
                SyncItem(
                    entity_type="care_plan_action",
                    entity_key=action.id,
                    entity_version=action.version,
                    state=action_response(action),
                )
            )
        for review in (await dao_care_plan_reviews.get_multi(
            db, where={"account_id": account_id, "plan_id": plan.id, "record_status": "valid"},
            shows=None, ordering=[("date_added", False), ("id", False)], include_total=False,
        ))[0]:
            items.append(
                SyncItem(
                    entity_type="care_plan_review",
                    entity_key=review.id,
                    entity_version=review.version,
                    state=review_response(review),
                )
            )

    return items
