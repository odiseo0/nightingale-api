from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.subscriptions.repository.models import (
    AccountSubscription,
    BcvExchangeRate,
    PaymentReport,
    PaymentReportEvidence,
    PlatformOperator,
    PlatformOperatorCredential,
    SubscriptionPeriod,
    SubscriptionPlan,
    SubscriptionPlanVersion,
    SubscriptionReview,
)
from src.core.db import DAO
from src.core.db.model import Base
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType, datetime_now


class SubscriptionPlanDAO(DAO[SubscriptionPlan, BaseModel, BaseModel]):
    async def by_code(
        self, db: AsyncSession, code: str
    ) -> SubscriptionPlan | EmptyType:
        row = await db.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.code == code)
        )

        return Empty if row is None else row

    async def all_plans(self, db: AsyncSession) -> list[SubscriptionPlan]:
        rows = await db.scalars(
            select(SubscriptionPlan).order_by(SubscriptionPlan.code)
        )

        return list(rows)

    async def insert_plan(
        self, db: AsyncSession, plan_id: UUID, code: str, name: str, description: str
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": plan_id,
                "code": code,
                "name": name,
                "description": description,
            },
        )

    async def apply_update(
        self, db: AsyncSession, plan_id: UUID, expected_version: int, changes: dict
    ) -> bool:
        """Optimistic catalog update; False when another writer won the version."""
        result = await db.execute(
            update(SubscriptionPlan)
            .where(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.version == expected_version,
            )
            .values(**changes, version=expected_version + 1, updated_at=datetime_now())
        )

        return result.rowcount == 1


class SubscriptionPlanVersionDAO(DAO[SubscriptionPlanVersion, BaseModel, BaseModel]):
    async def insert_version(
        self,
        db: AsyncSession,
        version_id: UUID,
        plan_id: UUID,
        version: int,
        seat_limit: int,
        price_30d_usd: Decimal,
        price_year_usd: Decimal,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": version_id,
                "plan_id": plan_id,
                "version": version,
                "seat_limit": seat_limit,
                "price_30d_usd": price_30d_usd,
                "price_year_usd": price_year_usd,
            },
        )

    async def latest_version(
        self, db: AsyncSession, plan_id: UUID
    ) -> SubscriptionPlanVersion | EmptyType:
        row = await db.scalar(
            select(SubscriptionPlanVersion)
            .where(SubscriptionPlanVersion.plan_id == plan_id)
            .order_by(SubscriptionPlanVersion.version.desc())
            .limit(1)
        )

        return Empty if row is None else row

    async def versions_of(
        self, db: AsyncSession, plan_ids: list[UUID]
    ) -> list[SubscriptionPlanVersion]:
        rows = await db.scalars(
            select(SubscriptionPlanVersion)
            .where(SubscriptionPlanVersion.plan_id.in_(plan_ids))
            .order_by(SubscriptionPlanVersion.plan_id, SubscriptionPlanVersion.version)
        )

        return list(rows)


class AccountSubscriptionDAO(DAO[AccountSubscription, BaseModel, BaseModel]):
    async def by_account(
        self, db: AsyncSession, account_id: UUID
    ) -> AccountSubscription | EmptyType:
        row = await db.scalar(
            select(AccountSubscription).where(AccountSubscription.account_id == account_id)
        )

        return Empty if row is None else row

    async def by_account_for_update(
        self, db: AsyncSession, account_id: UUID
    ) -> AccountSubscription | EmptyType:
        row = await db.scalar(
            select(AccountSubscription)
            .where(AccountSubscription.account_id == account_id)
            .with_for_update()
        )

        return Empty if row is None else row

    async def insert_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        account_id: UUID,
        plan_version_id: UUID,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": subscription_id,
                "account_id": account_id,
                "plan_version_id": plan_version_id,
            },
        )

    async def apply_approval(
        self, db: AsyncSession, subscription_id: UUID, plan_version_id: UUID
    ) -> int:
        row = await db.scalar(
            select(AccountSubscription).where(AccountSubscription.id == subscription_id)
        )
        next_version = row.version + 1
        await db.execute(
            update(AccountSubscription)
            .where(AccountSubscription.id == subscription_id)
            .values(
                status="active",
                plan_version_id=plan_version_id,
                version=next_version,
                updated_at=datetime_now(),
            )
        )

        return next_version


dao_subscription_plans = SubscriptionPlanDAO(SubscriptionPlan)
dao_plan_versions = SubscriptionPlanVersionDAO(SubscriptionPlanVersion)
dao_account_subscriptions = AccountSubscriptionDAO(AccountSubscription)


class PlatformOperatorDAO(DAO[PlatformOperator, BaseModel, BaseModel]):
    async def insert_operator(self, db: AsyncSession, values: dict) -> None:
        await self.create(db, commit=False, obj_in=values)

    async def by_oidc(
        self, db: AsyncSession, issuer: str, subject: str
    ) -> PlatformOperator | EmptyType:
        row = await db.scalar(
            select(PlatformOperator).where(
                PlatformOperator.oidc_issuer == issuer,
                PlatformOperator.oidc_subject == subject,
            )
        )

        return Empty if row is None else row

    async def page(self, db: AsyncSession, page: int, shows: int) -> tuple[list, int]:
        statement = select(PlatformOperator)
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(PlatformOperator.created_at, PlatformOperator.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total

    async def by_credential_hash(
        self, db: AsyncSession, token_hash: str
    ) -> PlatformOperator | EmptyType:
        row = await db.scalar(
            select(PlatformOperator)
            .join(
                PlatformOperatorCredential,
                PlatformOperatorCredential.operator_id == PlatformOperator.id,
            )
            .where(
                PlatformOperatorCredential.token_hash == token_hash,
                PlatformOperatorCredential.revoked_at.is_(None),
            )
        )

        return Empty if row is None else row


class PlatformOperatorCredentialDAO(DAO[PlatformOperatorCredential, BaseModel, BaseModel]):
    async def insert_credential(
        self, db: AsyncSession, credential_id: UUID, operator_id: UUID, token_hash: str
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": credential_id,
                "operator_id": operator_id,
                "token_hash": token_hash,
            },
        )

    async def revoke_all(self, db: AsyncSession, operator_id: UUID, now) -> None:
        await db.execute(
            update(PlatformOperatorCredential)
            .where(
                PlatformOperatorCredential.operator_id == operator_id,
                PlatformOperatorCredential.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )


dao_platform_operators = PlatformOperatorDAO(PlatformOperator)
dao_operator_credentials = PlatformOperatorCredentialDAO(PlatformOperatorCredential)


class BcvRateDAO(DAO[BcvExchangeRate, BaseModel, BaseModel]):
    async def insert_rate(
        self,
        db: AsyncSession,
        rate_id: UUID,
        rate_date: date,
        rate_ves_per_usd: Decimal,
        source: str,
        registered_by: UUID,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": rate_id,
                "rate_date": rate_date,
                "rate_ves_per_usd": rate_ves_per_usd,
                "source": source,
                "registered_by": registered_by,
            },
        )

    async def by_date(
        self, db: AsyncSession, rate_date: date
    ) -> BcvExchangeRate | EmptyType:
        row = await db.scalar(
            select(BcvExchangeRate).where(BcvExchangeRate.rate_date == rate_date)
        )

        return Empty if row is None else row

    async def latest_on_or_before(
        self, db: AsyncSession, day: date
    ) -> BcvExchangeRate | EmptyType:
        row = await db.scalar(
            select(BcvExchangeRate)
            .where(BcvExchangeRate.rate_date <= day)
            .order_by(BcvExchangeRate.rate_date.desc())
            .limit(1)
        )

        return Empty if row is None else row

    async def page(
        self, db: AsyncSession, page: int, shows: int
    ) -> tuple[list[BcvExchangeRate], int]:
        statement = select(BcvExchangeRate)
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(BcvExchangeRate.rate_date.desc())
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total


dao_bcv_rates = BcvRateDAO(BcvExchangeRate)


class PaymentReportDAO(DAO[PaymentReport, BaseModel, BaseModel]):
    async def insert_report(self, db: AsyncSession, values: dict) -> None:
        await self.create(db, commit=False, obj_in=values)

    async def page_for_account(
        self,
        db: AsyncSession,
        account_id: UUID,
        status: str | None,
        page: int,
        shows: int,
    ) -> tuple[list[PaymentReport], int]:
        statement = select(PaymentReport).where(PaymentReport.account_id == account_id)

        if status is not None:
            statement = statement.where(PaymentReport.status == status)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(PaymentReport.created_at.desc(), PaymentReport.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total

    async def page_for_operator(
        self,
        db: AsyncSession,
        status: str | None,
        account_id: UUID | None,
        page: int,
        shows: int,
    ) -> tuple[list[PaymentReport], int]:
        statement = select(PaymentReport)

        if status is not None:
            statement = statement.where(PaymentReport.status == status)

        if account_id is not None:
            statement = statement.where(PaymentReport.account_id == account_id)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(PaymentReport.created_at, PaymentReport.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total

    async def reference_matches(
        self, db: AsyncSession, account_id: UUID, last4: str, exclude_id: UUID
    ) -> list[PaymentReport]:
        rows = await db.scalars(
            select(PaymentReport)
            .where(
                PaymentReport.account_id == account_id,
                PaymentReport.declared_reference_last4 == last4,
                PaymentReport.id != exclude_id,
            )
            .order_by(PaymentReport.created_at)
        )

        return list(rows)

    async def resubmissions_of(self, db: AsyncSession, report_id: UUID) -> list[UUID]:
        rows = await db.scalars(
            select(PaymentReport.id)
            .where(PaymentReport.previous_report_id == report_id)
            .order_by(PaymentReport.created_at)
        )

        return list(rows)

    async def by_id_for_update(
        self, db: AsyncSession, report_id: UUID
    ) -> PaymentReport | EmptyType:
        row = await db.scalar(
            select(PaymentReport).where(PaymentReport.id == report_id).with_for_update()
        )

        return Empty if row is None else row

    async def mark_decided(
        self, db: AsyncSession, report_id: UUID, decision: str, expected_version: int
    ) -> bool:
        result = await db.execute(
            update(PaymentReport)
            .where(
                PaymentReport.id == report_id, PaymentReport.version == expected_version
            )
            .values(
                status=decision, version=expected_version + 1, updated_at=datetime_now()
            )
        )

        return result.rowcount == 1

    async def for_account(
        self, db: AsyncSession, report_id: UUID, account_id: UUID, *, lock: bool = False
    ) -> PaymentReport | EmptyType:
        statement = select(PaymentReport).where(
            PaymentReport.id == report_id, PaymentReport.account_id == account_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement)

        return Empty if row is None else row


class PaymentReportEvidenceDAO(DAO[PaymentReportEvidence, BaseModel, BaseModel]):
    async def by_report(
        self, db: AsyncSession, report_id: UUID
    ) -> PaymentReportEvidence | EmptyType:
        row = await db.scalar(
            select(PaymentReportEvidence).where(
                PaymentReportEvidence.report_id == report_id
            )
        )

        return Empty if row is None else row


dao_payment_reports = PaymentReportDAO(PaymentReport)
dao_report_evidence = PaymentReportEvidenceDAO(PaymentReportEvidence)


class SubscriptionReviewDAO(DAO[SubscriptionReview, BaseModel, BaseModel]):
    async def insert_review(self, db: AsyncSession, values: dict) -> None:
        await self.create(db, commit=False, obj_in=values)

    async def by_report(
        self, db: AsyncSession, report_id: UUID
    ) -> SubscriptionReview | EmptyType:
        row = await db.scalar(
            select(SubscriptionReview).where(SubscriptionReview.report_id == report_id)
        )

        return Empty if row is None else row


dao_subscription_reviews = SubscriptionReviewDAO(SubscriptionReview)


class SubscriptionPeriodDAO(DAO[SubscriptionPeriod, BaseModel, BaseModel]):
    async def latest_period(
        self, db: AsyncSession, subscription_id: UUID
    ) -> SubscriptionPeriod | EmptyType:
        row = await db.scalar(
            select(SubscriptionPeriod)
            .where(SubscriptionPeriod.subscription_id == subscription_id)
            .order_by(SubscriptionPeriod.sequence.desc())
            .limit(1)
        )

        return Empty if row is None else row

    async def period_by_origin(
        self, db: AsyncSession, origin_review_id: UUID
    ) -> SubscriptionPeriod | EmptyType:
        row = await db.scalar(
            select(SubscriptionPeriod).where(
                SubscriptionPeriod.origin_review_id == origin_review_id
            )
        )

        return Empty if row is None else row

    async def insert_period(
        self,
        db: AsyncSession,
        period_id: UUID,
        subscription_id: UUID,
        plan_version_id: UUID,
        periodicity: str,
        starts_at: datetime,
        ends_at: datetime,
        sequence: int,
        origin_review_id: UUID,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": period_id,
                "subscription_id": subscription_id,
                "plan_version_id": plan_version_id,
                "periodicity": periodicity,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "sequence": sequence,
                "origin_review_id": origin_review_id,
            },
        )


dao_subscription_periods = SubscriptionPeriodDAO(SubscriptionPeriod)


class MetricsDAO(DAO[AccountSubscription, BaseModel, BaseModel]):
    """Bounded administrative aggregates (§22); never patient or clinical data."""

    async def accounts_by_plan(self, db: AsyncSession) -> list[tuple]:
        rows = await db.execute(
            select(
                SubscriptionPlan.code,
                AccountSubscription.status,
                func.count(),
            )
            .join(
                SubscriptionPlanVersion,
                SubscriptionPlanVersion.id == AccountSubscription.plan_version_id,
            )
            .join(SubscriptionPlan, SubscriptionPlan.id == SubscriptionPlanVersion.plan_id)
            .group_by(SubscriptionPlan.code, AccountSubscription.status)
            .order_by(SubscriptionPlan.code, AccountSubscription.status)
        )

        return list(rows.all())

    async def expiring_soon(self, db: AsyncSession, until) -> list[tuple]:
        latest = (
            select(
                SubscriptionPeriod.subscription_id,
                func.max(SubscriptionPeriod.sequence).label("sequence"),
            )
            .group_by(SubscriptionPeriod.subscription_id)
            .subquery()
        )
        rows = await db.execute(
            select(AccountSubscription.account_id, SubscriptionPeriod.ends_at)
            .join(
                SubscriptionPeriod,
                SubscriptionPeriod.subscription_id == AccountSubscription.id,
            )
            .join(
                latest,
                (latest.c.subscription_id == SubscriptionPeriod.subscription_id)
                & (latest.c.sequence == SubscriptionPeriod.sequence),
            )
            .where(
                SubscriptionPeriod.ends_at > func.now(),
                SubscriptionPeriod.ends_at <= until,
            )
            .order_by(SubscriptionPeriod.ends_at)
        )

        return list(rows.all())

    async def pending_reports(self, db: AsyncSession) -> tuple[int, object]:
        row = (
            await db.execute(
                select(func.count(), func.min(PaymentReport.created_at)).where(
                    PaymentReport.status == "pending"
                )
            )
        ).one()

        return row[0], row[1]

    async def periods_by_plan(self, db: AsyncSession) -> list[tuple]:
        rows = await db.execute(
            select(
                SubscriptionPlan.code,
                SubscriptionPeriod.periodicity,
                func.count(),
            )
            .join(
                SubscriptionPlanVersion,
                SubscriptionPlanVersion.id == SubscriptionPeriod.plan_version_id,
            )
            .join(SubscriptionPlan, SubscriptionPlan.id == SubscriptionPlanVersion.plan_id)
            .group_by(SubscriptionPlan.code, SubscriptionPeriod.periodicity)
            .order_by(SubscriptionPlan.code, SubscriptionPeriod.periodicity)
        )

        return list(rows.all())

    async def verified_amounts(self, db: AsyncSession) -> list[tuple]:
        # Historical verified amounts stay in their own currency; VES is never
        # revalued nor mixed with USD (§22).
        rows = await db.execute(
            select(SubscriptionReview.verified_currency, func.sum(SubscriptionReview.verified_amount))
            .where(SubscriptionReview.decision == "approved")
            .group_by(SubscriptionReview.verified_currency)
            .order_by(SubscriptionReview.verified_currency)
        )

        return list(rows.all())

    async def seats_over_limit(self, db: AsyncSession) -> list[tuple]:
        from src.api.accounts.repository.models import AccountMembership

        active = (
            select(
                AccountMembership.account_id,
                func.count().label("used"),
            )
            .where(AccountMembership.status == "active")
            .group_by(AccountMembership.account_id)
            .subquery()
        )
        rows = await db.execute(
            select(AccountSubscription.account_id, active.c.used, SubscriptionPlanVersion.seat_limit)
            .join(active, active.c.account_id == AccountSubscription.account_id)
            .join(
                SubscriptionPlanVersion,
                SubscriptionPlanVersion.id == AccountSubscription.plan_version_id,
            )
            .where(active.c.used > SubscriptionPlanVersion.seat_limit)
            .order_by(AccountSubscription.account_id)
        )

        return list(rows.all())


dao_metrics = MetricsDAO(AccountSubscription)
