import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.billing.application.evidence_cases import store_report_evidence
from src.api.billing.application.review_cases import (
    review_detail,
    review_evidence,
    review_inbox,
)
from src.core import Err
from src.settings.storage_settings import storage_settings

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c7000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019c7000-0000-7000-8000-000000000010")
OTHER_ACCOUNT_ID = UUID("019c7000-0000-7000-8000-000000000011")
PATIENT_ID = UUID("019c7000-0000-7000-8000-000000000020")
CHARGE_ID = UUID("019c7000-0000-7000-8000-000000000030")
GRANT_ID = UUID("019c7000-0000-7000-8000-000000000040")
REPORT_ID = UUID("019c7000-0000-7000-8000-000000000050")
SECOND_REPORT_ID = UUID("019c7000-0000-7000-8000-000000000051")
PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-review" * 4


class BillingReviewTests(unittest.IsolatedAsyncioTestCase):
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
            VALUES ('{USER_ID}','fixture','review-owner','Fixture');
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
                    '{"b" * 64}',ARRAY['read_charge','submit_report','read_result'],
                    '2026-12-27T15:00:00Z','{USER_ID}');
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method,
                 declared_reference_last4)
            VALUES
                ('{REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                 '2026-11-26',40.00,'USD','transferencia ficticia','0071'),
                ('{SECOND_REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                 '2026-11-27',60.00,'USD','transferencia ficticia','0071');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()
        folder = Path(storage_settings.STORAGE_ROOT) / str(ACCOUNT_ID)
        if folder.is_dir():
            for item in folder.iterdir():
                item.unlink()
            folder.rmdir()

    async def test_inbox_filters_and_never_crosses_accounts(self):
        async with self.sessions() as db:
            inbox = await review_inbox(db, ACCOUNT_ID, 1, 100)
            self.assertEqual(inbox["total"], 2)
            self.assertEqual(
                {item.report_id for item in inbox["items"]},
                {REPORT_ID, SECOND_REPORT_ID},
            )
            other = await review_inbox(db, OTHER_ACCOUNT_ID, 1, 100)
            self.assertEqual(other["total"], 0)

    async def test_detail_shows_chain_review_and_reference_warnings(self):
        async with self.sessions() as db:
            await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PNG)
            detail = await review_detail(db, ACCOUNT_ID, REPORT_ID)
            self.assertEqual(detail.value.evidence.content_type, "image/png")
            self.assertIsNone(detail.value.review)
            # Same partial reference on the sibling report only warns (§10.5).
            self.assertEqual(
                [w.report_id for w in detail.value.reference_warnings],
                [SECOND_REPORT_ID],
            )

        await self.admin.execute(f"""
            INSERT INTO nightingale.billing_reviews
                (id,report_id,account_id,reviewer_id,decision,reason,internal_note)
            VALUES ('{uuid7()}','{REPORT_ID}','{ACCOUNT_ID}','{USER_ID}',
                    'rejected','captura ilegible ficticia','nota interna del revisor');
            UPDATE nightingale.patient_payment_reports SET status='rejected', version=2
            WHERE id='{REPORT_ID}';
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method,previous_report_id)
            VALUES ('{uuid7()}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                    '2026-11-28',40.00,'USD','transferencia ficticia','{REPORT_ID}');
        """)
        async with self.sessions() as db:
            detail = await review_detail(db, ACCOUNT_ID, REPORT_ID)
            self.assertEqual(detail.value.review.decision, "rejected")
            self.assertEqual(detail.value.review.internal_note, "nota interna del revisor")
            self.assertEqual(len(detail.value.resubmissions), 1)
            pending = await review_inbox(db, ACCOUNT_ID, 1, 100)
            self.assertEqual(pending["total"], 2)

            foreign = await review_detail(db, OTHER_ACCOUNT_ID, REPORT_ID)
            self.assertIsInstance(foreign.error, AccountObjectNotFound)

    async def test_evidence_download_is_account_scoped(self):
        async with self.sessions() as db:
            await store_report_evidence(db, ACCOUNT_ID, REPORT_ID, PNG)
            content_type, content = (
                await review_evidence(db, ACCOUNT_ID, REPORT_ID)
            ).value
            self.assertEqual((content_type, content), ("image/png", PNG))

            crossed = await review_evidence(db, OTHER_ACCOUNT_ID, REPORT_ID)
            self.assertIsInstance(crossed.error, AccountObjectNotFound)
            missing = await review_evidence(db, ACCOUNT_ID, uuid7())
            self.assertIsInstance(missing.error, AccountObjectNotFound)


if __name__ == "__main__":
    unittest.main()
