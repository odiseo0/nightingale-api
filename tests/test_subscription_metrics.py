import asyncio
import runpy
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.metrics_cases import subscription_metrics
from src.core import Err, Ok
from src.core.services.device_tokens import issue_token
from tests.test_subscription_reports import F_ACCOUNT, F_SEED, F_USER, F_PLAN, F_VERSION

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

OTHER_USER = "019c7000-0000-7000-8000-000000000001"
OTHER_ACCOUNT = "019c7000-0000-7000-8000-000000000010"
OTHER_PLAN = "019c7000-0000-7000-8000-000000000020"
OTHER_VERSION = "019c7000-0000-7000-8000-000000000021"
OPERATOR_ID = "019c7000-0000-7000-8000-000000000030"


class SubscriptionMetricsTests(unittest.IsolatedAsyncioTestCase):
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
        now = datetime.now(timezone.utc)
        ends_soon = now + timedelta(days=3)
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
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{OTHER_USER}','fixture','metrics-other','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{OTHER_ACCOUNT}','clinic','{OTHER_USER}','Otra','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{OTHER_ACCOUNT}','{OTHER_USER}'),('{OTHER_ACCOUNT}','{F_USER}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{OTHER_ACCOUNT}',0);
            INSERT INTO nightingale.subscription_plans (id,code,name,description)
            VALUES ('{OTHER_PLAN}','small_practice','Consultorio','Fixture');
            INSERT INTO nightingale.subscription_plan_versions
                (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
            VALUES ('{OTHER_VERSION}','{OTHER_PLAN}',1,1,24.00,240.00);
            INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id,status)
            VALUES ('{uuid7()}','{F_ACCOUNT}','{F_VERSION}','active'),
                   ('{uuid7()}','{OTHER_ACCOUNT}','{OTHER_VERSION}','suspended');
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{OPERATOR_ID}','fixture','metrics-op','op',ARRAY['metrics']);
        """)
        # One report approved in USD, one in VES, one still pending: pending is
        # never verified income and currencies stay separate (§22).
        for index, (account, subscription_plan, currency, amount, decision) in enumerate((
            (F_ACCOUNT, F_VERSION, "USD", "18.00", "approved"),
            (OTHER_ACCOUNT, OTHER_VERSION, "VES", "7204.50", "approved"),
            (F_ACCOUNT, F_VERSION, "USD", "24.00", "pending"),
        )):
            report_id = uuid7()
            subscription = await self.admin.fetchval(
                "SELECT id FROM nightingale.account_subscriptions WHERE account_id=$1",
                account,
            )
            user = F_USER if account == F_ACCOUNT else OTHER_USER
            await self.admin.execute(f"""
                INSERT INTO nightingale.payment_reports
                    (id,account_id,subscription_id,plan_version_id,periodicity,status,
                     declared_paid_on,declared_amount,declared_currency,declared_method,submitted_by)
                VALUES ('{report_id}','{account}','{subscription}','{subscription_plan}',
                        'days_30','{decision if decision == "pending" else "approved"}',
                        '2026-11-20',{amount},'{currency}','fixture','{user}')
            """)
            if decision == "approved":
                review_id = uuid7()
                await self.admin.execute(f"""
                    INSERT INTO nightingale.subscription_reviews
                        (id,report_id,operator_id,decision,verified_paid_on,
                         verified_amount,verified_currency)
                    VALUES ('{review_id}','{report_id}','{OPERATOR_ID}','approved',
                            '2026-11-20',{amount},'{currency}')
                """)
                await self.admin.execute(f"""
                    INSERT INTO nightingale.subscription_periods
                        (id,subscription_id,plan_version_id,periodicity,starts_at,ends_at,
                         sequence,origin_review_id)
                    VALUES ('{uuid7()}','{subscription}','{subscription_plan}','days_30',
                            '{ends_soon - timedelta(days=30)}','{ends_soon}',1,'{review_id}')
                """)
        _, self.metrics_token, digest = self._token()
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash)
            VALUES ('{uuid7()}','{OPERATOR_ID}','{self.digest}')
        """)

    def _token(self):
        token_id, secret, digest = issue_token()
        self.digest = digest.hex()
        return token_id, secret, digest

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def test_metrics_require_their_own_action(self):
        token_id, secret, digest = issue_token()
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{uuid7()}','fixture','review-only','op',ARRAY['review']);
            INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash)
            SELECT '{uuid7()}', id, '{digest.hex()}' FROM nightingale.platform_operators
            WHERE oidc_subject='review-only';
        """)
        async with self.sessions() as db:
            denied = await subscription_metrics(db, secret)
            self.assertIsInstance(denied.error, __import__(
                "src.api.authorization.domain.errors", fromlist=["AccessDenied"]
            ).AccessDenied)
            self.assertEqual(
                type((await subscription_metrics(db, None)).error).__name__,
                "InvalidCredential",
            )

    async def test_indicators_match_the_persisted_state(self):
        async with self.sessions() as db:
            result = await subscription_metrics(db, self.metrics_token)
        self.assertIsInstance(result, Ok)
        metrics = result.value

        by_plan = {(row.plan_code, row.status): row.count for row in metrics.accounts_by_plan}
        self.assertEqual(by_plan, {("independent", "active"): 1, ("small_practice", "suspended"): 1})

        self.assertEqual(len(metrics.expiring_soon), 2)
        self.assertEqual(metrics.pending_reports.count, 1)
        self.assertIsNotNone(metrics.pending_reports.oldest_created_at)

        periods = {(row.plan_code, row.periodicity): row.count for row in metrics.periods_by_plan}
        self.assertEqual(periods, {("independent", "days_30"): 1, ("small_practice", "days_30"): 1})

        amounts = {row.currency: row.total for row in metrics.verified_amounts}
        self.assertEqual(amounts, {"USD": Decimal("18.00"), "VES": Decimal("7204.50")})

        overruns = metrics.seats_over_limit
        self.assertEqual(len(overruns), 1)
        self.assertEqual((overruns[0].used, overruns[0].limit), (2, 1))
        self.assertEqual(str(overruns[0].account_id), OTHER_ACCOUNT)


if __name__ == "__main__":
    unittest.main()
