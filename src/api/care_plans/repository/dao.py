from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

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


class _Scoped:
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        *,
        lock: bool = False,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row


class _HistoryPage:
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class _PlanScoped:
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        plan_id: UUID,
        offset: int,
        shows: int,
        *,
        extra_where=None,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.plan_id == plan_id
        )

        if extra_where is not None:
            statement = extra_where(statement)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.created_at, self.model.id)
            .offset(offset)
            .limit(shows)
        )

        return list(rows), total

    async def valid_for_plan(
        self, db: AsyncSession, account_id: UUID, plan_id: UUID
    ):
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.plan_id == plan_id,
                self.model.record_status == "valid",
            )
        )

        return list(rows)


class CarePlanDAO(_Scoped, DAO[CarePlan, BaseModel, BaseModel]):
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
            statement.order_by(self.model.created_at, self.model.id)
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


class CarePlanHistoryDAO(
    _HistoryPage, DAO[CarePlanHistory, BaseModel, BaseModel]
):
    pass


class CarePlanGoalDAO(_Scoped, _PlanScoped, DAO[CarePlanGoal, BaseModel, BaseModel]):
    pass


class CarePlanGoalHistoryDAO(
    _HistoryPage, DAO[CarePlanGoalHistory, BaseModel, BaseModel]
):
    pass


class CarePlanActionDAO(
    _Scoped, _PlanScoped, DAO[CarePlanAction, BaseModel, BaseModel]
):
    pass


class CarePlanActionHistoryDAO(
    _HistoryPage, DAO[CarePlanActionHistory, BaseModel, BaseModel]
):
    pass


class CarePlanReviewDAO(
    _Scoped, _PlanScoped, DAO[CarePlanReview, BaseModel, BaseModel]
):
    pass


class CarePlanReviewHistoryDAO(
    _HistoryPage, DAO[CarePlanReviewHistory, BaseModel, BaseModel]
):
    pass


dao_care_plans = CarePlanDAO(CarePlan)
dao_care_plan_histories = CarePlanHistoryDAO(CarePlanHistory)
dao_care_plan_goals = CarePlanGoalDAO(CarePlanGoal)
dao_care_plan_goal_histories = CarePlanGoalHistoryDAO(CarePlanGoalHistory)
dao_care_plan_actions = CarePlanActionDAO(CarePlanAction)
dao_care_plan_action_histories = CarePlanActionHistoryDAO(CarePlanActionHistory)
dao_care_plan_reviews = CarePlanReviewDAO(CarePlanReview)
dao_care_plan_review_histories = CarePlanReviewHistoryDAO(CarePlanReviewHistory)
