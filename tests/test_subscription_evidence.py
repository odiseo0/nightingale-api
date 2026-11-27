import asyncio
import hashlib
import runpy
import unittest
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.evidence_cases import (
    EvidenceAlreadyPresent,
    EvidenceNotFound,
    EvidenceRejected,
    ReportNotFound,
    ReportNotPending,
    read_evidence,
    store_evidence,
)
from src.core import Err, Ok
from src.settings.storage_settings import storage_settings

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = "019c3000-0000-7000-8000-000000000001"
ACCOUNT_ID = "019c3000-0000-7000-8000-000000000010"
PLAN_ID = "019c3000-0000-7000-8000-000000000020"
VERSION_ID = "019c3000-0000-7000-8000-000000000021"
SUBSCRIPTION_ID = "019c3000-0000-7000-8000-000000000030"
REPORT_ID = "019c3000-0000-7000-8000-000000000040"

PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-image" * 4
PDF = b"%PDF-1.4 fixture"


class SubscriptionEvidenceTests(unittest.IsolatedAsyncioTestCase):
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
            VALUES ('{USER_ID}','fixture','evidence-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.subscription_plans (id,code,name,description)
            VALUES ('{PLAN_ID}','independent','Fixture','Fixture');
            INSERT INTO nightingale.subscription_plan_versions
                (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
            VALUES ('{VERSION_ID}','{PLAN_ID}',1,2,18.00,100.00);
            INSERT INTO nightingale.account_subscriptions (id,account_id,plan_version_id)
            VALUES ('{SUBSCRIPTION_ID}','{ACCOUNT_ID}','{VERSION_ID}');
            INSERT INTO nightingale.payment_reports
                (id,account_id,subscription_id,plan_version_id,periodicity,
                 declared_paid_on,declared_amount,declared_currency,declared_method,submitted_by)
            VALUES ('{REPORT_ID}','{ACCOUNT_ID}','{SUBSCRIPTION_ID}','{VERSION_ID}',
                    'days_30','2026-11-20',18.00,'USD','transferencia ficticia','{USER_ID}');
        """)

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()
        # Local fallback files live under STORAGE_ROOT/<account>; remove fixtures.
        folder = Path(storage_settings.STORAGE_ROOT) / ACCOUNT_ID
        if folder.is_dir():
            for item in folder.iterdir():
                item.unlink()
            folder.rmdir()

    async def test_valid_capture_is_stored_privately_with_metadata(self):
        async with self.sessions() as db:
            result = await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, PNG)
            self.assertIsInstance(result, Ok)

            row = await self.admin.fetchrow(
                "SELECT content_type,size_bytes,sha256,storage_key "
                f"FROM nightingale.payment_report_evidence WHERE report_id='{REPORT_ID}'"
            )
            self.assertEqual(row["content_type"], "image/png")
            self.assertEqual(row["size_bytes"], len(PNG))
            self.assertEqual(row["sha256"], hashlib.sha256(PNG).hexdigest())
            self.assertNotIn("http", row["storage_key"])

            content_type, content = (await read_evidence(db, ACCOUNT_ID, REPORT_ID)).value
            self.assertEqual(content_type, "image/png")
            self.assertEqual(content, PNG)

    async def test_signature_size_and_single_capture_rules(self):
        async with self.sessions() as db:
            # A GIF declared as anything is rejected by its real signature (OWASP).
            rejected = await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, b"GIF89a-not-allowed")
            self.assertEqual(rejected.error, EvidenceRejected("invalid_type"))

            empty = await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, b"")
            self.assertEqual(empty.error, EvidenceRejected("invalid_size"))

            oversized = await store_evidence(
                db, ACCOUNT_ID, REPORT_ID, USER_ID,
                b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024),
            )
            self.assertEqual(oversized.error, EvidenceRejected("invalid_size"))

            self.assertIsInstance(
                await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, PDF), Ok
            )
            duplicate = await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, PNG)
            self.assertIsInstance(duplicate.error, EvidenceAlreadyPresent)

    async def test_evidence_never_crosses_accounts_or_decided_reports(self):
        other_report = str(uuid7())
        async with self.sessions() as db:
            missing = await store_evidence(db, ACCOUNT_ID, other_report, USER_ID, PNG)
            self.assertIsInstance(missing.error, ReportNotFound)

        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('019c3000-0000-7000-8000-000000000050','fixture','op','op',ARRAY['review']);
            INSERT INTO nightingale.subscription_reviews
                (id,report_id,operator_id,decision,reason)
            VALUES ('019c3000-0000-7000-8000-000000000051','{REPORT_ID}',
                    '019c3000-0000-7000-8000-000000000050','rejected','fixture');
            UPDATE nightingale.payment_reports SET status='rejected'
            WHERE id='{REPORT_ID}';
        """)
        async with self.sessions() as db:
            decided = await store_evidence(db, ACCOUNT_ID, REPORT_ID, USER_ID, PNG)
            self.assertIsInstance(decided.error, ReportNotPending)

            nothing = await read_evidence(db, ACCOUNT_ID, REPORT_ID)
            self.assertIsInstance(nothing.error, EvidenceNotFound)


if __name__ == "__main__":
    unittest.main()
