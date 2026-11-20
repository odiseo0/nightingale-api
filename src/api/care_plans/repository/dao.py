from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel

from .models import (
    CarePlan,
    CarePlanAction,
    CarePlanActionHistory,
    CarePlanGoal,
    CarePlanGoalHistory,
    CarePlanHistory,
    CarePlanReview,
    CarePlanReviewHistory,
)


class CarePlanDAO(DAO[CarePlan, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        query,
    ) -> tuple[list[CarePlan], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.plan_status is not None:
            statement = statement.where(self.model.plan_status == query.plan_status)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.date_added, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(
        self, db: AsyncSession, account_id: UUID
    ) -> list[CarePlan]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


dao_care_plans = CarePlanDAO(CarePlan)
dao_care_plan_histories = DAO(CarePlanHistory)
dao_care_plan_goals = DAO(CarePlanGoal)
dao_care_plan_goal_histories = DAO(CarePlanGoalHistory)
dao_care_plan_actions = DAO(CarePlanAction)
dao_care_plan_action_histories = DAO(CarePlanActionHistory)
dao_care_plan_reviews = DAO(CarePlanReview)
dao_care_plan_review_histories = DAO(CarePlanReviewHistory)
