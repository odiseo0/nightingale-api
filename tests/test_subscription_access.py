import asyncio
import runpy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.access_cases import (
    CommerciallySuspended,
    ensure_commercially_available,
)
from src.core import Err, Ok
from tests.test_subscription_reports import F_ACCOUNT, F_SEED, F_USER, F_VERSION

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

VERSION_ID = F_VERSION
SUBSCRIPTION_ID = "019c6000-0000-7000-8000-000000000030"
OPERATOR_ID = "019c6000-0000-7000-8000-000000000040"


class SubscriptionAccessTests(unittest.IsolatedAsyncioTestCase):
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
        """)

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def gate(self):
        async with self.sessions() as db:
            return await ensure_commercially_available(db, UUID(F_ACCOUNT))

    async def make_subscription(self, status: str, ends_at: datetime | None):
        await self.admin.execute(f"""
            INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id,status)
            VALUES ('{SUBSCRIPTION_ID}','{F_ACCOUNT}','{VERSION_ID}','{status}')
        """)

    async def make_period(self, ends_at: datetime):
        report_id = uuid7()
        review_id = uuid7()
        await self.admin.execute(f"""
            INSERT INTO nightingale.payment_reports
                (id,account_id,subscription_id,plan_version_id,periodicity,
                 declared_paid_on,declared_amount,declared_currency,declared_method,submitted_by)
            VALUES ('{report_id}','{F_ACCOUNT}','{SUBSCRIPTION_ID}','{VERSION_ID}',
                    'days_30','2026-11-01',18.00,'USD','fixture','{F_USER}')
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.subscription_reviews
                (id,report_id,operator_id,decision,verified_paid_on,verified_amount,verified_currency)
            VALUES ('{review_id}','{report_id}','{OPERATOR_ID}','approved','2026-11-01',18.00,'USD')
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.subscription_periods
                (id,subscription_id,plan_version_id,periodicity,starts_at,ends_at,sequence,origin_review_id)
            VALUES ('{uuid7()}','{SUBSCRIPTION_ID}','{VERSION_ID}','days_30',
                    '{ends_at - timedelta(days=30)}','{ends_at}',1,'{review_id}')
        """)

    async def test_accounts_without_subscription_are_not_gated(self):
        self.assertIsInstance(await self.gate(), Ok)

    async def test_active_and_grace_keep_normal_service(self):
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{OPERATOR_ID}','fixture','gate-op','op',ARRAY['review'])
        """)
        now = datetime.now(timezone.utc)
        await self.make_subscription("active", None)
        await self.make_period(now + timedelta(days=10))
        self.assertIsInstance(await self.gate(), Ok)

        # Three days past the end: inside the 7-day grace (D24).
        await self.admin.execute(f"""
            UPDATE nightingale.subscription_periods
            SET starts_at='{now - timedelta(days=33)}', ends_at='{now - timedelta(days=3)}'
        """)
        self.assertIsInstance(await self.gate(), Ok)

    async def test_suspension_blocks_after_grace_without_touching_data(self):
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{OPERATOR_ID}','fixture','gate-op','op',ARRAY['review'])
        """)
        now = datetime.now(timezone.utc)
        await self.make_subscription("active", None)
        await self.make_period(now - timedelta(days=10))
        result = await self.gate()
        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, CommerciallySuspended)

        # Nothing was deleted or deactivated by the gate.
        members = await self.admin.fetchval(
            f"SELECT count(*) FROM nightingale.account_memberships WHERE account_id='{F_ACCOUNT}'"
        )
        self.assertEqual(members, 1)

    async def test_cancelled_blocks_only_after_paid_time_ends(self):
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{OPERATOR_ID}','fixture','gate-op','op',ARRAY['review'])
        """)
        now = datetime.now(timezone.utc)
        await self.make_subscription("cancelled", None)
        await self.make_period(now + timedelta(days=5))
        self.assertIsInstance(await self.gate(), Ok)

        await self.admin.execute(f"""
            UPDATE nightingale.subscription_periods
            SET starts_at='{now - timedelta(days=40)}', ends_at='{now - timedelta(days=10)}'
        """)
        self.assertIsInstance((await self.gate()).error, CommerciallySuspended)


if __name__ == "__main__":
    unittest.main()
