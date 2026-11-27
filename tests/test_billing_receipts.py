import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.billing.application.direct_payment_cases import (
    DirectPaymentRequest,
    register_direct_payment,
)
from src.api.billing.application.receipt_cases import read_receipt
from src.core import Err
from src.settings.storage_settings import storage_settings
from tests.test_billing_corrections import ACCOUNT_ID, CHARGE_ID, PATIENT_ID, USER_ID, context

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))


class BillingReceiptTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.payment_receipts, nightingale.patient_payments,
                     nightingale.charge_histories, nightingale.audit_events,
                     nightingale.devices, nightingale.patient_charges,
                     nightingale.account_patients, nightingale.patients,
                     nightingale.account_sync_heads, nightingale.account_memberships,
                     nightingale.accounts, nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','receipts-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.devices
                (id,user_id,display_name,client_version,local_schema_version)
            VALUES ('019ca000-0000-7000-8000-000000000070','{USER_ID}','Fixture device','0.1.0',1);
            INSERT INTO nightingale.patients (id) VALUES ('{PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio');
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,description,amount,currency,price_source,
                 status,issued_at,created_by)
            VALUES ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                    100.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}');
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

    async def test_receipt_is_a_private_pdf_with_frozen_snapshot(self):
        async with self.sessions() as db, db.begin():
            paid = await register_direct_payment(
                db, context(), CHARGE_ID,
                DirectPaymentRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 1,
                    "paidOn": "2026-11-27", "amount": "40.00", "currency": "USD",
                    "method": "efectivo ficticio", "referenceLast4": "0071",
                    "evidenceNote": "recibo interno ficticio",
                }),
            )
            content_type, content = (
                await read_receipt(db, ACCOUNT_ID, paid.value.payment_id)
            ).value
            self.assertEqual(content_type, "application/pdf")
            self.assertTrue(content.startswith(b"%PDF-1.4"))
            self.assertIn(b"no es una factura fiscal", content)
            self.assertIn(b"40.00 USD", content)
            self.assertIn(b"0071", content)

            # One receipt per payment: a second download returns the same bytes.
            again_type, again = (
                await read_receipt(db, ACCOUNT_ID, paid.value.payment_id)
            ).value
            self.assertEqual((again_type, again), (content_type, content))

            missing = await read_receipt(db, ACCOUNT_ID, uuid7())
            self.assertIsInstance(missing.error, AccountObjectNotFound)


if __name__ == "__main__":
    unittest.main()
