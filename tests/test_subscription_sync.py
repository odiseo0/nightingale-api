import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.policies import projection_allowed
from src.api.subscriptions.application.projection_cases import subscription_projections
from src.api.subscriptions.application.report_cases import store_report
from src.core.db import transaction
from tests.test_subscription_reports import F_ACCOUNT, F_SEED, F_USER, submission

DEVICE_ID = "019c4000-0000-7000-8000-000000000060"

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))


class SubscriptionSyncTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.change_log, nightingale.devices, nightingale.subscription_periods,
                     nightingale.subscription_reviews, nightingale.payment_report_evidence,
                     nightingale.payment_reports, nightingale.bcv_exchange_rates,
                     nightingale.platform_operator_credentials, nightingale.platform_operators,
                     nightingale.account_subscriptions, nightingale.subscription_plan_versions,
                     nightingale.subscription_plans, nightingale.accounts,
                     nightingale.app_users CASCADE;
            {F_SEED}
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.devices
                (id,user_id,display_name,client_version,local_schema_version,created_at,updated_at)
            VALUES ('{DEVICE_ID}','{F_USER}','Fixture','0.1.0',1,
                    '2026-11-26T00:00:00Z','2026-11-26T00:00:00Z')
        """)

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def change_rows(self):
        return await self.admin.fetch("""
            SELECT entity_type,audience,projection_json,sequence,ordinal,group_size
            FROM nightingale.change_log ORDER BY sequence,ordinal
        """)

    async def test_first_submission_publishes_a_minimal_group(self):
        async with self.sessions() as db:
            result = await store_report(
                db, UUID(F_ACCOUNT), UUID(F_USER), submission(), device_id=UUID(DEVICE_ID)
            )
            self.assertEqual(result.value.status, "pending")

        rows = await self.change_rows()
        self.assertEqual([row["entity_type"] for row in rows],
                         ["subscription", "subscription_admin"])
        self.assertEqual([row["audience"] for row in rows], ["members", "owner"])
        self.assertEqual(rows[0]["group_size"], 2)

        import json
        members = json.loads(rows[0]["projection_json"])
        self.assertEqual(members["status"], "pending_activation")
        self.assertEqual(members["planCode"], "independent")
        # Members never receive seats, reports, rates or evidence (§18.2).
        for forbidden in ("seats", "declared", "evidence", "bcvRate", "review"):
            self.assertNotIn(forbidden, members)

        admin = json.loads(rows[1]["projection_json"])
        self.assertEqual(admin["seats"], {"used": 1, "limit": 2})

        # Commercial changes do not touch the permission epoch (§18.4).
        head = await self.admin.fetchrow(
            f"SELECT last_sequence,permission_epoch FROM nightingale.account_sync_heads "
            f"WHERE account_id='{F_ACCOUNT}'"
        )
        self.assertEqual(head["last_sequence"], 1)
        # The initial epoch (1) is unchanged: availability is not a permission change.
        self.assertEqual(head["permission_epoch"], 1)

    async def test_snapshot_projection_reflects_the_current_availability(self):
        # Operator approvals have no member device receipt, so the delta journal
        # only carries account-actor changes; consumers recover approvals through
        # the snapshot projection, which always reflects current state (§18.3).
        async with self.sessions() as db:
            await store_report(
                db, UUID(F_ACCOUNT), UUID(F_USER), submission(), device_id=UUID(DEVICE_ID)
            )

        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('019c4000-0000-7000-8000-000000000070','fixture','op','op',ARRAY['review']);
            INSERT INTO nightingale.subscription_reviews
                (id,report_id,operator_id,decision,verified_paid_on,verified_amount,verified_currency)
            SELECT '019c4000-0000-7000-8000-000000000071', id,
                   '019c4000-0000-7000-8000-000000000070','approved','2026-11-20',18.00,'USD'
            FROM nightingale.payment_reports LIMIT 1;
            INSERT INTO nightingale.subscription_periods
                (id,subscription_id,plan_version_id,periodicity,starts_at,ends_at,sequence,origin_review_id)
            SELECT '019c4000-0000-7000-8000-000000000072', id, plan_version_id,
                   'days_30','2026-11-26T00:00:00Z','2026-12-26T00:00:00Z',1,
                   '019c4000-0000-7000-8000-000000000071'
            FROM nightingale.account_subscriptions LIMIT 1;
            UPDATE nightingale.account_subscriptions SET status='active', version=2;
        """)
        async with self.sessions() as db:
            members, admin = await subscription_projections(db, UUID(F_ACCOUNT))
            self.assertEqual(members.status, "active")
            self.assertIsNotNone(members.current_period_ends_at)
            self.assertIsNone(members.grace_ends_at)
            self.assertEqual(admin.seats.used, 1)

        # Only the submission published delta rows; the approval is recovered by snapshot.
        rows = await self.change_rows()
        self.assertEqual(len(rows), 2)

    async def test_projection_audiences_follow_the_policy(self):
        self.assertTrue(projection_allowed("subscription", "members", False, []))
        self.assertTrue(projection_allowed("subscription_admin", "owner", True, []))
        self.assertFalse(projection_allowed("subscription_admin", "owner", False, []))
        self.assertFalse(projection_allowed("subscription_admin", "members", True, []))


if __name__ == "__main__":
    unittest.main()
