import asyncio
import hashlib
import runpy
import unittest
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.billing.application.evidence_cases import (
    EvidenceAlreadyPresent,
    EvidenceNotFound,
    ReportNotFound,
    ReportNotPending,
    read_report_evidence,
    store_report_evidence,
)
from src.core import Err, Ok
from src.core.services.private_evidence import EvidenceRejected
from src.settings.storage_settings import storage_settings

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = "019c4000-0000-7000-8000-000000000001"
ACCOUNT_ID = "019c4000-0000-7000-8000-000000000010"
OTHER_ACCOUNT_ID = "019c4000-0000-7000-8000-000000000011"
PATIENT_ID = "019c4000-0000-7000-8000-000000000020"
CHARGE_ID = "019c4000-0000-7000-8000-000000000030"
GRANT_ID = "019c4000-0000-7000-8000-000000000040"
REPORT_ID = "019c4000-0000-7000-8000-000000000050"

PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-image" * 4
PDF = b"%PDF-1.4 fixture"


class BillingEvidenceTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.patient_payment_evidence, nightingale.billing_reviews,
                     nightingale.patient_payment_reports, nightingale.patient_billing_grants,
                     nightingale.patient_charges, nightingale.account_patients,
                     nightingale.patients, nightingale.account_sync_heads,
                     nightingale.account_memberships, nightingale.accounts,
                     nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','billing-evidence','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture'),
                   ('{OTHER_ACCOUNT_ID}','clinic','{USER_ID}','Otra','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}'),('{OTHER_ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0),('{OTHER_ACCOUNT_ID}',0);
            INSERT INTO nightingale.patients (id) VALUES ('{PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio');
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,description,amount,currency,price_source,
                 status,issued_at,created_by)
            VALUES ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                    100.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}');
            INSERT INTO nightingale.patient_billing_grants
                (id,account_id,patient_id,charge_id,token_hash,actions,expires_at,created_by)
            VALUES ('{GRANT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{CHARGE_ID}',
                    '{"a" * 64}',ARRAY['read_charge','submit_report'],
                    '2026-12-27T15:00:00Z','{USER_ID}');
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method)
            VALUES ('{REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                    '2026-11-26',40.00,'USD','transferencia ficticia');
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
            result = await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PNG)
            self.assertIsInstance(result, Ok)

            row = await self.admin.fetchrow(
                "SELECT content_type,size_bytes,sha256,storage_key "
                f"FROM nightingale.patient_payment_evidence WHERE report_id='{REPORT_ID}'"
            )
            self.assertEqual(row["content_type"], "image/png")
            self.assertEqual(row["size_bytes"], len(PNG))
            self.assertEqual(row["sha256"], hashlib.sha256(PNG).hexdigest())
            self.assertNotIn("http", row["storage_key"])

            content_type, content = (
                await read_report_evidence(db, ACCOUNT_ID, REPORT_ID)
            ).value
            self.assertEqual((content_type, content), ("image/png", PNG))

    async def test_signature_size_and_single_capture_rules(self):
        async with self.sessions() as db:
            rejected = await store_report_evidence(
                db, ACCOUNT_ID, REPORT_ID, b"GIF89a-not-allowed"
            )
            self.assertEqual(rejected.error, EvidenceRejected("invalid_type"))

            empty = await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, b"")
            self.assertEqual(empty.error, EvidenceRejected("invalid_size"))

            oversized = await store_report_evidence(
                db, ACCOUNT_ID, REPORT_ID, b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024)
            )
            self.assertEqual(oversized.error, EvidenceRejected("invalid_size"))

            self.assertIsInstance(
                await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PDF), Ok
            )
            duplicate = await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PNG)
            self.assertIsInstance(duplicate.error, EvidenceAlreadyPresent)

    async def test_evidence_never_crosses_accounts_or_decided_reports(self):
        async with self.sessions() as db:
            # The report belongs to ACCOUNT_ID; another account sees a uniform 404.
            crossed = await store_report_evidence(db, OTHER_ACCOUNT_ID, REPORT_ID, PNG)
            self.assertIsInstance(crossed.error, ReportNotFound)

            missing = await store_report_evidence(db, ACCOUNT_ID, uuid7(), PNG)
            self.assertIsInstance(missing.error, ReportNotFound)

        await self.admin.execute(f"""
            INSERT INTO nightingale.billing_reviews
                (id,report_id,account_id,reviewer_id,decision,reason)
            VALUES ('{uuid7()}','{REPORT_ID}','{ACCOUNT_ID}','{USER_ID}',
                    'rejected','captura ilegible ficticia');
            UPDATE nightingale.patient_payment_reports SET status='rejected', version=2
            WHERE id='{REPORT_ID}';
        """)
        async with self.sessions() as db:
            decided = await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PNG)
            self.assertIsInstance(decided.error, ReportNotPending)

            nothing = await read_report_evidence(db, ACCOUNT_ID, REPORT_ID)
            self.assertIsInstance(nothing.error, EvidenceNotFound)


if __name__ == "__main__":
    unittest.main()
