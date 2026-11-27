import asyncio
import runpy
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.review_cases import approve_report
from src.api.subscriptions.application.subscription_cases import (
    PlanUnavailable,
    VersionConflict,
    cancel_subscription,
    change_plan,
    subscription_response,
)
from src.api.subscriptions.application.report_cases import store_report
from src.api.subscriptions.domain.reviews import ApprovalRequest
from src.api.subscriptions.domain.subscriptions import CancellationRequest, PlanChangeRequest
from src.api.subscriptions.repository.dao import dao_account_subscriptions
from src.core import Err, Ok
from src.core.db import transaction
from src.core.services.device_tokens import issue_token
from tests.test_subscription_reports import F_ACCOUNT, F_SEED, F_USER, submission

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

DEVICE_ID = "019c5000-0000-7000-8000-000000000060"
ACCOUNT = UUID(F_ACCOUNT)
USER = UUID(F_USER)


class SubscriptionRenewalTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._prepare())

    @classmethod
    async def _prepare(cls):
        await SUPPORT["prepare_database"]()
        result = SUPPORT["migrate"]("upgrade", "head")
        assert result.returncode == 0, result.stderr or result.stdout

    @classmethod
    def tearDownClass(cls):
        async def drop():
            admin = await SUPPORT["connect_admin"]()
            try:
                await admin.execute(
                    f'DROP DATABASE IF EXISTS "{SUPPORT["DATABASE"]}" WITH (FORCE)'
                )
            finally:
                await admin.close()

        asyncio.run(drop())

    async def asyncSetUp(self):
        url = SUPPORT["database_url"]("nightingale_app", SUPPORT["APP_PASSWORD"])
        self.engine = create_async_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=SUPPORT["DATABASE"], timeout=10,
        )
        await self.admin.execute(f"""
            TRUNCATE nightingale.change_log, nightingale.devices, nightingale.audit_events,
                     nightingale.operation_receipts, nightingale.subscription_periods,
                     nightingale.subscription_reviews, nightingale.payment_report_evidence,
                     nightingale.payment_reports, nightingale.bcv_exchange_rates,
                     nightingale.platform_operator_credentials, nightingale.platform_operators,
                     nightingale.account_subscriptions, nightingale.subscription_plan_versions,
                     nightingale.subscription_plans, nightingale.accounts,
                     nightingale.app_users CASCADE;
            {F_SEED}
            INSERT INTO nightingale.devices
                (id,user_id,display_name,client_version,local_schema_version,created_at,updated_at)
            VALUES ('{DEVICE_ID}','{F_USER}','Fixture','0.1.0',1,
                    '2026-11-26T00:00:00Z','2026-11-26T00:00:00Z');
            INSERT INTO nightingale.subscription_plans (id,code,name,description)
            VALUES ('019c5000-0000-7000-8000-000000000020','small_practice','Consultorio','Fixture');
            INSERT INTO nightingale.subscription_plan_versions
                (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
            VALUES ('019c5000-0000-7000-8000-000000000021',
                    '019c5000-0000-7000-8000-000000000020',1,5,24.00,240.00);
        """)
        token_id, secret, digest = issue_token()
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{uuid7()}','fixture','renewal-op','op',ARRAY['review']);
            INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash)
            SELECT '{uuid7()}', id, '{digest.hex()}'
            FROM nightingale.platform_operators WHERE oidc_subject='renewal-op';
        """)
        self.operator_token = secret

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def approve(self, report_id, amount="18.00"):
        async with self.sessions() as db:
            return await approve_report(
                db, self.operator_token, report_id,
                ApprovalRequest(
                    operation_id=uuid7(), expected_version=1,
                    verified_paid_on=datetime.now(timezone.utc).date(),
                    verified_amount=Decimal(amount),
                    verified_currency="USD",
                ),
            )

    async def current(self):
        async with self.sessions() as db:
            subscription = await dao_account_subscriptions.by_account_for_update(db, ACCOUNT)
            return await subscription_response(db, subscription)

    async def test_early_renewal_keeps_paid_days_and_late_renewal_starts_now(self):
        first_report = uuid7()
        async with self.sessions() as db:
            await store_report(db, ACCOUNT, USER, submission(first_report),
                               device_id=UUID(DEVICE_ID))
        approved = await self.approve(first_report)
        self.assertIsInstance(approved, Ok)
        first_end = approved.value.granted_period.ends_at
        self.assertEqual(approved.value.granted_period.sequence, 1)

        # Early renewal: a second approved report starts exactly at the previous end.
        second_report = uuid7()
        async with self.sessions() as db:
            await store_report(db, ACCOUNT, USER, submission(second_report),
                               device_id=UUID(DEVICE_ID))
        renewed = await self.approve(second_report)
        self.assertEqual(renewed.value.granted_period.sequence, 2)
        self.assertEqual(renewed.value.granted_period.starts_at, first_end)
        self.assertEqual(
            renewed.value.granted_period.ends_at - renewed.value.granted_period.starts_at,
            timedelta(days=30),
        )

        # Late renewal: with everything expired, the new period starts at approval.
        past = datetime.now(timezone.utc) - timedelta(days=40)
        await self.admin.execute(f"""
            UPDATE nightingale.subscription_periods
            SET starts_at='{past - timedelta(days=60)}', ends_at='{past - timedelta(days=30)}'
            WHERE sequence=1
        """)
        await self.admin.execute(f"""
            UPDATE nightingale.subscription_periods
            SET starts_at='{past - timedelta(days=30)}', ends_at='{past}'
            WHERE sequence=2
        """)
        third_report = uuid7()
        async with self.sessions() as db:
            await store_report(db, ACCOUNT, USER, submission(third_report),
                               device_id=UUID(DEVICE_ID))
        before = datetime.now(timezone.utc)
        late = await self.approve(third_report)
        self.assertEqual(late.value.granted_period.sequence, 3)
        self.assertGreaterEqual(late.value.granted_period.starts_at, before)
        self.assertGreater(late.value.granted_period.starts_at, past)

    async def test_plan_change_applies_to_the_next_period_without_touching_history(self):
        report = uuid7()
        async with self.sessions() as db:
            await store_report(db, ACCOUNT, USER, submission(report),
                               device_id=UUID(DEVICE_ID))
        await self.approve(report)
        state = await self.current()
        self.assertEqual(state.plan.code, "independent")

        async with self.sessions() as db:
            stale = await change_plan(db, ACCOUNT, USER, UUID(DEVICE_ID),
                                      PlanChangeRequest(operation_id=uuid7(),
                                                        expected_version=99,
                                                        plan_code="small_practice"))
        self.assertIsInstance(stale.error, VersionConflict)

        async with self.sessions() as db:
            unknown = await change_plan(db, ACCOUNT, USER, UUID(DEVICE_ID),
                                        PlanChangeRequest(operation_id=uuid7(),
                                                          expected_version=state.subscription_version,
                                                          plan_code="unknown"))
        self.assertIsInstance(unknown.error, PlanUnavailable)

        async with self.sessions() as db:
            changed = await change_plan(db, ACCOUNT, USER, UUID(DEVICE_ID),
                                        PlanChangeRequest(operation_id=uuid7(),
                                                          expected_version=state.subscription_version,
                                                          plan_code="small_practice"))
        self.assertIsInstance(changed, Ok)
        self.assertEqual(changed.value.plan.code, "small_practice")
        self.assertEqual(changed.value.seats.limit, 5)

        # The approved period keeps the version it was paid with (§16.1).
        period_version = await self.admin.fetchval(
            "SELECT pv.version || '-' || p.code FROM nightingale.subscription_periods sp "
            "JOIN nightingale.subscription_plan_versions pv ON pv.id=sp.plan_version_id "
            "JOIN nightingale.subscription_plans p ON p.id=pv.plan_id"
        )
        self.assertEqual(period_version, "1-independent")

    async def test_cancellation_keeps_paid_time_and_blocks_nothing_retroactively(self):
        report = uuid7()
        async with self.sessions() as db:
            await store_report(db, ACCOUNT, USER, submission(report),
                               device_id=UUID(DEVICE_ID))
        await self.approve(report)
        state = await self.current()

        async with self.sessions() as db:
            cancelled = await cancel_subscription(
                db, ACCOUNT, USER, UUID(DEVICE_ID),
                CancellationRequest(operation_id=uuid7(),
                                    expected_version=state.subscription_version),
            )
        self.assertIsInstance(cancelled, Ok)
        # Paid time continues: the effective status stays active until the end (§16.3).
        self.assertEqual(cancelled.value.status, "active")
        stored = await self.admin.fetchval(
            f"SELECT status FROM nightingale.account_subscriptions WHERE account_id='{F_ACCOUNT}'"
        )
        self.assertEqual(stored, "cancelled")
        periods = await self.admin.fetchval(
            "SELECT count(*) FROM nightingale.subscription_periods"
        )
        self.assertEqual(periods, 1)


if __name__ == "__main__":
    unittest.main()
