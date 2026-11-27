import asyncio
import runpy
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.quote_cases import (
    PlanNotFound,
    RateDateExists,
    RateUnavailable,
    build_quote,
    list_rates,
    register_rate,
)
from src.api.subscriptions.domain.quotes import BcvRateCreateRequest
from src.core import Err, Ok
from src.core.services.device_tokens import issue_token

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

SEED = """
    INSERT INTO nightingale.subscription_plans (id,code,name,description) VALUES
        ('019c1000-0000-7000-8000-000000000001','independent','Médico independiente','Fixture'),
        ('019c1000-0000-7000-8000-000000000002','small_practice','Consultorio pequeño','Fixture'),
        ('019c1000-0000-7000-8000-000000000003','medical_center','Centro médico','Fixture');
    INSERT INTO nightingale.subscription_plan_versions
        (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd) VALUES
        ('019c1000-0000-7000-8000-000000000011','019c1000-0000-7000-8000-000000000001',1,2,18.00,100.00),
        ('019c1000-0000-7000-8000-000000000012','019c1000-0000-7000-8000-000000000002',1,5,24.00,240.00),
        ('019c1000-0000-7000-8000-000000000013','019c1000-0000-7000-8000-000000000003',1,20,75.00,500.00);
"""


def rate_payload(day: date, value: str = "400.25") -> BcvRateCreateRequest:
    return BcvRateCreateRequest(
        operation_id=uuid7(),
        rate_date=day,
        rate_ves_per_usd=Decimal(value),
        source="bcv-ficticio",
    )


class SubscriptionQuoteTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._prepare())

    @classmethod
    async def _prepare(cls):
        await support["prepare_database"]()
        result = support["migrate"]("upgrade", "head")
        assert result.returncode == 0, result.stderr or result.stdout

    @classmethod
    def tearDownClass(cls):
        async def drop():
            admin = await support["connect_admin"]()
            try:
                await admin.execute(
                    f'DROP DATABASE IF EXISTS "{support["DATABASE"]}" WITH (FORCE)'
                )
            finally:
                await admin.close()

        asyncio.run(drop())

    async def asyncSetUp(self):
        url = support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        self.engine = create_async_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=support["DATABASE"], timeout=10,
        )
        await self.admin.execute(f"""
            TRUNCATE nightingale.subscription_periods, nightingale.subscription_reviews,
                     nightingale.payment_report_evidence, nightingale.payment_reports,
                     nightingale.bcv_exchange_rates, nightingale.platform_operator_credentials,
                     nightingale.platform_operators, nightingale.account_subscriptions,
                     nightingale.subscription_plan_versions, nightingale.subscription_plans
                     CASCADE;
            {SEED}
        """)
        token_id, secret, digest = issue_token()
        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{uuid7()}','fixture','rates-op','rates-op',ARRAY['rates']);
            INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash)
            SELECT '{uuid7()}', id, '{digest.hex()}'
            FROM nightingale.platform_operators WHERE oidc_subject='rates-op';
        """)
        self.rates_token = secret

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def test_register_and_list_rates(self):
        async with self.sessions() as db:
            created = await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 25)))
            self.assertIsInstance(created, Ok)
            self.assertEqual(created.value.rate_ves_per_usd, Decimal("400.25"))

            duplicate = await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 25), "401"))
            self.assertIsInstance(duplicate.error, RateDateExists)

            denied = await register_rate(db, None, rate_payload(date(2026, 11, 26)))
            self.assertEqual(type(denied.error).__name__, "InvalidCredential")

            listed = await list_rates(db, self.rates_token, 1, 100)
            self.assertEqual(listed.value.total, 1)

    async def test_quote_uses_latest_rate_on_or_before_today(self):
        async with self.sessions() as db:
            await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 20), "390.00"))
            await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 24), "400.25"))

            # 2026-11-25 has no publication: the most recent previous rate applies (D22).
            now = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
            quote = await build_quote(db, "independent", "days_30", now)
            self.assertIsInstance(quote, Ok)
            self.assertEqual(quote.value.amount_usd, Decimal("18.00"))
            self.assertEqual(quote.value.bcv_rate, Decimal("400.25"))
            self.assertEqual(quote.value.bcv_rate_date, date(2026, 11, 24))
            self.assertEqual(quote.value.amount_ves, Decimal("7204.50"))
            self.assertEqual(quote.value.rounding_rule, "ROUND_HALF_UP")

            annual = await build_quote(db, "medical_center", "year_1", now)
            self.assertEqual(annual.value.amount_usd, Decimal("500.00"))
            self.assertEqual(annual.value.amount_ves, Decimal("200125.00"))

            # A quote before any publication is unavailable, not zero.
            early = await build_quote(db, "independent", "days_30",
                                      datetime(2026, 11, 1, tzinfo=timezone.utc))
            self.assertIsInstance(early.error, RateUnavailable)

            missing = await build_quote(db, "unknown", "days_30", now)
            self.assertIsInstance(missing.error, PlanNotFound)

    async def test_a_new_rate_never_alters_an_earlier_quote(self):
        # Each case runs on its own session, like one request per get_db session.
        async with self.sessions() as db:
            await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 24), "400.25"))

        now = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
        async with self.sessions() as db:
            first = await build_quote(db, "independent", "days_30", now)

        async with self.sessions() as db:
            await register_rate(db, self.rates_token, rate_payload(date(2026, 11, 25), "410.00"))

        async with self.sessions() as db:
            second = await build_quote(db, "independent", "days_30", now)

        self.assertEqual(first.value.amount_ves, Decimal("7204.50"))
        self.assertEqual(second.value.bcv_rate, Decimal("410.00"))
        self.assertEqual(second.value.amount_ves, Decimal("7380.00"))
        self.assertNotEqual(first.value.quote_id, second.value.quote_id)


if __name__ == "__main__":
    unittest.main()
