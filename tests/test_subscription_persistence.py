import asyncio
import runpy
import unittest
from datetime import datetime, timezone
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = "019c0000-0000-7000-8000-0000000000a1"
ACCOUNT_ID = "019c0000-0000-7000-8000-0000000000a2"
OTHER_ACCOUNT_ID = "019c0000-0000-7000-8000-0000000000a3"
PLAN_ID = "019c0000-0000-7000-8000-0000000000b1"
VERSION_ID = "019c0000-0000-7000-8000-0000000000c1"
SUBSCRIPTION_ID = "019c0000-0000-7000-8000-0000000000d1"
OPERATOR_ID = "019c0000-0000-7000-8000-0000000000f1"
RATE_ID = "019c0000-0000-7000-8000-0000000000f2"
REPORT_ID = "019c0000-0000-7000-8000-0000000000f3"
REVIEW_ID = "019c0000-0000-7000-8000-0000000000f4"


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class SubscriptionPersistenceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # One random database for the whole class; the probe helper fixes its
        # name at load time, so per-test creation would collide.
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
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=support["DATABASE"], timeout=10,
        )
        self.app = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_app",
            password=support["APP_PASSWORD"], database=support["DATABASE"], timeout=10,
        )
        await self.admin.execute("""
            TRUNCATE nightingale.subscription_periods, nightingale.subscription_reviews,
                     nightingale.payment_report_evidence, nightingale.payment_reports,
                     nightingale.bcv_exchange_rates, nightingale.platform_operator_credentials,
                     nightingale.platform_operators, nightingale.account_subscriptions,
                     nightingale.subscription_plan_versions, nightingale.subscription_plans,
                     nightingale.accounts, nightingale.app_users CASCADE;
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','subscription-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES
                ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                 'Fixture','Fixture','VE','Fixture','Fixture'),
                ('{OTHER_ACCOUNT_ID}','clinic','{USER_ID}','Otra','America/Caracas',
                 'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}'),('{OTHER_ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0),('{OTHER_ACCOUNT_ID}',0);
            INSERT INTO nightingale.subscription_plans (id,code,name,description)
            VALUES ('{PLAN_ID}','independent','Fixture','Fixture');
            INSERT INTO nightingale.subscription_plan_versions
                (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
            VALUES ('{VERSION_ID}','{PLAN_ID}',1,2,18.00,100.00);
            INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id)
            VALUES ('{SUBSCRIPTION_ID}','{ACCOUNT_ID}','{VERSION_ID}');
            INSERT INTO nightingale.platform_operators (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('{OPERATOR_ID}','fixture','operator','Operador',ARRAY['review']);
            INSERT INTO nightingale.bcv_exchange_rates (id,rate_date,rate_ves_per_usd,source,registered_by)
            VALUES ('{RATE_ID}','2026-11-20',400.25,'bcv-ficticio','{OPERATOR_ID}');
        """)

    async def asyncTearDown(self):
        await self.app.close()
        await self.admin.close()

    async def insert_report(self, report_id=REPORT_ID, account_id=ACCOUNT_ID,
                            subscription_id=SUBSCRIPTION_ID, last4="0071"):
        await self.app.execute(f"""
            INSERT INTO nightingale.payment_reports
                (id,account_id,subscription_id,plan_version_id,periodicity,
                 declared_paid_on,declared_amount,declared_currency,declared_method,
                 declared_reference_last4,submitted_by)
            VALUES ('{report_id}','{account_id}','{subscription_id}','{VERSION_ID}',
                    'days_30','2026-11-20',18.00,'USD','transferencia ficticia',
                    '{last4}','{USER_ID}')
        """)

    async def insert_review(self, review_id=REVIEW_ID, report_id=REPORT_ID,
                            decision="approved", reason="NULL",
                            verified="'2026-11-20',18.00,'USD'"):
        await self.app.execute(f"""
            INSERT INTO nightingale.subscription_reviews
                (id,report_id,operator_id,decision,verified_paid_on,verified_amount,
                 verified_currency,reason)
            VALUES ('{review_id}','{report_id}','{OPERATOR_ID}','{decision}',
                    {verified},{reason})
        """)

    async def test_runtime_role_can_write_through_grants_but_not_delete(self):
        code = await self.app.fetchval(
            "SELECT code FROM nightingale.subscription_plans WHERE id=$1", PLAN_ID
        )
        self.assertEqual(code, "independent")
        for statement in (
            "DELETE FROM nightingale.subscription_plans",
            "DROP TABLE nightingale.subscription_plans",
            "DELETE FROM nightingale.payment_reports",
            "DELETE FROM nightingale.subscription_reviews",
        ):
            with self.assertRaises(asyncpg.InsufficientPrivilegeError, msg=statement):
                await self.app.execute(statement)

    async def test_plan_versions_are_unique_positive_and_usd(self):
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.admin.execute(f"""
                INSERT INTO nightingale.subscription_plan_versions
                    (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
                VALUES ('019c0000-0000-7000-8000-0000000000c2','{PLAN_ID}',1,3,20.00,200.00)
            """)
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.admin.execute(f"""
                INSERT INTO nightingale.subscription_plan_versions
                    (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
                VALUES ('019c0000-0000-7000-8000-0000000000c3','{PLAN_ID}',2,0,20.00,200.00)
            """)

    async def test_one_subscription_per_account(self):
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.admin.execute(f"""
                INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id)
                VALUES ('019c0000-0000-7000-8000-0000000000d2','{ACCOUNT_ID}','{VERSION_ID}')
            """)

    async def test_periods_do_not_overlap_but_touch_and_need_one_review(self):
        await self.insert_report()
        await self.insert_review()
        insert = """
            INSERT INTO nightingale.subscription_periods
                (id,subscription_id,plan_version_id,periodicity,starts_at,ends_at,
                 sequence,origin_review_id)
            VALUES ($1,$2,$3,'days_30',$4,$5,$6,$7)
        """
        await self.app.execute(
            insert, "019c0000-0000-7000-8000-0000000000e1", SUBSCRIPTION_ID, VERSION_ID,
            ts("2027-01-01T00:00:00Z"), ts("2027-01-31T00:00:00Z"), 1, REVIEW_ID,
        )
        # [starts, ends): a period starting exactly at the previous end does not overlap.
        await self.insert_report("019c0000-0000-7000-8000-0000000000f5")
        await self.insert_review("019c0000-0000-7000-8000-0000000000f6",
                                 "019c0000-0000-7000-8000-0000000000f5")
        await self.app.execute(
            insert, "019c0000-0000-7000-8000-0000000000e2", SUBSCRIPTION_ID, VERSION_ID,
            ts("2027-01-31T00:00:00Z"), ts("2027-03-02T00:00:00Z"), 2,
            "019c0000-0000-7000-8000-0000000000f6",
        )
        with self.assertRaises(asyncpg.ExclusionViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e3", SUBSCRIPTION_ID, VERSION_ID,
                ts("2027-01-15T00:00:00Z"), ts("2027-02-15T00:00:00Z"), 3, REVIEW_ID,
            )
        # One approval produces at most one ordinary period (§11.6).
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e4", SUBSCRIPTION_ID, VERSION_ID,
                ts("2027-03-02T00:00:00Z"), ts("2027-04-01T00:00:00Z"), 4, REVIEW_ID,
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e5", SUBSCRIPTION_ID, VERSION_ID,
                ts("2027-04-01T00:00:00Z"), ts("2027-04-01T00:00:00Z"), 5, REVIEW_ID,
            )

    async def test_reports_never_cross_accounts_and_last4_is_not_unique(self):
        await self.insert_report()
        # Same partial reference in another report is allowed (§12.6).
        await self.insert_report("019c0000-0000-7000-8000-0000000000f5", last4="0071")
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            # The subscription belongs to ACCOUNT_ID; the report cannot claim another.
            await self.insert_report(
                "019c0000-0000-7000-8000-0000000000f7", account_id=OTHER_ACCOUNT_ID
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.insert_report(
                "019c0000-0000-7000-8000-0000000000f8", last4="071"
            )

    async def test_evidence_is_single_private_metadata_per_report(self):
        await self.insert_report()
        insert = """
            INSERT INTO nightingale.payment_report_evidence
                (id,report_id,storage_key,content_type,size_bytes,sha256,uploaded_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
        """
        await self.app.execute(
            insert, "019c0000-0000-7000-8000-0000000000e6", REPORT_ID,
            "evidence/fixture-1", "image/png", 1024, "a" * 64, USER_ID,
        )
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e7", REPORT_ID,
                "evidence/fixture-2", "image/png", 1024, "b" * 64, USER_ID,
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e8",
                "019c0000-0000-7000-8000-0000000000f5", "evidence/fixture-3",
                "image/gif", 1024, "c" * 64, USER_ID,
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000e9",
                "019c0000-0000-7000-8000-0000000000f5", "evidence/fixture-4",
                "image/png", 5242881, "d" * 64, USER_ID,
            )

    async def test_reviews_enforce_one_decision_and_coherence(self):
        await self.insert_report()
        with self.assertRaises(asyncpg.CheckViolationError):
            # Approved without verified data.
            await self.insert_review(verified="NULL,NULL,NULL")
        with self.assertRaises(asyncpg.CheckViolationError):
            # Rejected without reason.
            await self.insert_review(decision="rejected")
        await self.insert_review()
        with self.assertRaises(asyncpg.UniqueViolationError):
            # The same report cannot be decided twice.
            await self.insert_review("019c0000-0000-7000-8000-0000000000f9")

    async def test_bcv_rate_is_unique_per_date(self):
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(f"""
                INSERT INTO nightingale.bcv_exchange_rates
                    (id,rate_date,rate_ves_per_usd,source,registered_by)
                VALUES ('019c0000-0000-7000-8000-0000000000fa','2026-11-20',401.00,
                        'bcv-ficticio','{OPERATOR_ID}')
            """)

    async def test_failed_transaction_leaves_no_partial_state(self):
        transaction = self.app.transaction()
        await transaction.start()
        await self.insert_report()
        await transaction.rollback()
        count = await self.app.fetchval(
            "SELECT count(*) FROM nightingale.payment_reports WHERE account_id=$1",
            ACCOUNT_ID,
        )
        self.assertEqual(count, 0)

    async def test_downgrade_and_reapply(self):
        result = support["migrate"]("downgrade", "20261126_01")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.payment_reports') IS NOT NULL"
        )
        self.assertFalse(exists)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.subscription_plans') IS NOT NULL"
        )
        self.assertTrue(exists)
        result = support["migrate"]("downgrade", "20261122_01")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.subscription_plans') IS NOT NULL"
        )
        self.assertFalse(exists)
        result = support["migrate"]("upgrade", "head")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.subscription_reviews') IS NOT NULL"
        )
        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
