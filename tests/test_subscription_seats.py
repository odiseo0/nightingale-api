import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.seat_cases import (
    SeatLimitReached,
    ensure_seat_available,
)
from src.core import Err, Ok
from src.core.db import transaction

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

OWNER_ID = "019c2000-0000-7000-8000-000000000001"
MEMBER_ID = "019c2000-0000-7000-8000-000000000002"
ACCOUNT_ID = "019c2000-0000-7000-8000-000000000010"
PLAN_ID = "019c2000-0000-7000-8000-000000000020"
VERSION_ID = "019c2000-0000-7000-8000-000000000021"
SUBSCRIPTION_ID = "019c2000-0000-7000-8000-000000000030"


class SubscriptionSeatTests(unittest.IsolatedAsyncioTestCase):
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
                     nightingale.subscription_plan_versions, nightingale.subscription_plans,
                     nightingale.accounts, nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{OWNER_ID}','fixture','seat-owner','Fixture'),
                   ('{MEMBER_ID}','fixture','seat-member','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','clinic','{OWNER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{OWNER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.subscription_plans (id,code,name,description)
            VALUES ('{PLAN_ID}','independent','Fixture','Fixture');
            INSERT INTO nightingale.subscription_plan_versions
                (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
            VALUES ('{VERSION_ID}','{PLAN_ID}',1,2,18.00,100.00);
            INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id)
            VALUES ('{SUBSCRIPTION_ID}','{ACCOUNT_ID}','{VERSION_ID}');
        """)

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def test_seat_check_counts_active_memberships_against_the_plan(self):
        async with self.sessions() as db:
            async with transaction(db):
                # One active membership (owner), limit 2: one seat left.
                self.assertIsInstance(await ensure_seat_available(db, ACCOUNT_ID), Ok)

        await self.admin.execute(f"""
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{MEMBER_ID}')
        """)
        async with self.sessions() as db:
            async with transaction(db):
                result = await ensure_seat_available(db, ACCOUNT_ID)
                self.assertIsInstance(result, Err)
                self.assertEqual(result.error, SeatLimitReached(used=2, limit=2))

        # An inactive membership frees its seat for the check (D21).
        await self.admin.execute(f"""
            UPDATE nightingale.account_memberships SET status='inactive'
            WHERE account_id='{ACCOUNT_ID}' AND user_id='{MEMBER_ID}'
        """)
        async with self.sessions() as db:
            async with transaction(db):
                self.assertIsInstance(await ensure_seat_available(db, ACCOUNT_ID), Ok)

    async def test_accounts_without_subscription_are_not_limited_here(self):
        await self.admin.execute(
            f"DELETE FROM nightingale.account_subscriptions WHERE id='{SUBSCRIPTION_ID}'"
        )
        async with self.sessions() as db:
            async with transaction(db):
                self.assertIsInstance(await ensure_seat_available(db, ACCOUNT_ID), Ok)

    async def test_two_racing_acceptances_have_a_single_winner(self):
        barrier = asyncio.Event()

        async def occupy(user_id: str):
            async with self.sessions() as db:
                async with transaction(db):
                    result = await ensure_seat_available(db, ACCOUNT_ID)
                    barrier.set()
                    await asyncio.sleep(0.2)

                    if isinstance(result, Err):
                        return "denied"

                    await db.execute(
                        text(
                            "INSERT INTO nightingale.account_memberships (account_id,user_id) "
                            f"VALUES ('{ACCOUNT_ID}','{user_id}')"
                        )
                    )
                    return "accepted"

        await self.admin.execute(f"""
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('019c2000-0000-7000-8000-000000000003','fixture','seat-racer','Fixture')
        """)
        first, second = await asyncio.gather(occupy(MEMBER_ID), occupy(
            "019c2000-0000-7000-8000-000000000003"
        ))

        # Limit 2 with the owner occupying one seat: exactly one racer wins.
        self.assertEqual(sorted([first, second]), ["accepted", "denied"])
        count = await self.admin.fetchval(
            "SELECT count(*) FROM nightingale.account_memberships "
            f"WHERE account_id='{ACCOUNT_ID}' AND status='active'"
        )
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
