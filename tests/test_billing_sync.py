import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.policies import projection_allowed
from src.api.billing.application.direct_payment_cases import (
    DirectPaymentRequest,
    register_direct_payment,
)
from src.api.billing.application.projection_cases import snapshot_billing
from tests.test_billing_corrections import ACCOUNT_ID, CHARGE_ID, PATIENT_ID, USER_ID, context

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))


class BillingAudienceTests(unittest.TestCase):
    def test_billing_audience_needs_owner_or_the_read_grant(self):
        self.assertTrue(projection_allowed("billing_charge", "billing", True, []))
        self.assertTrue(projection_allowed("billing_payment", "billing", False, [], billing=True))
        self.assertFalse(projection_allowed("billing_charge", "billing", False, []))
        self.assertFalse(projection_allowed("billing_payment", "billing", False, ["conditions"]))
        self.assertFalse(projection_allowed("billing_charge", "members", True, []))


class BillingSnapshotTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.patient_payments, nightingale.charge_histories,
                     nightingale.audit_events, nightingale.devices,
                     nightingale.patient_charges, nightingale.account_patients,
                     nightingale.patients, nightingale.account_sync_heads,
                     nightingale.account_memberships, nightingale.accounts,
                     nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','sync-owner','Fixture');
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
            VALUES
                ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                 100.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}'),
                ('019ca000-0000-7000-8000-000000000031','{ACCOUNT_ID}','{PATIENT_ID}',
                 'Borrador ficticio',50.00,'USD','base','draft',NULL,'{USER_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def test_snapshot_projects_balances_and_payments_without_drafts_or_bytes(self):
        async with self.sessions() as db, db.begin():
            paid = await register_direct_payment(
                db, context(), CHARGE_ID,
                DirectPaymentRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 1,
                    "paidOn": "2026-11-27", "amount": "40.00", "currency": "USD",
                    "method": "efectivo ficticio", "evidenceNote": "recibo ficticio",
                }),
            )
            items = await snapshot_billing(db, context())
            kinds = {(item.entity_type, str(item.entity_key)) for item in items}
            self.assertIn(("billing_charge", str(CHARGE_ID)), kinds)
            self.assertIn(("billing_payment", str(paid.value.payment_id)), kinds)
            # Drafts never travel; nothing carries bytes or storage keys.
            self.assertNotIn(
                ("billing_charge", "019ca000-0000-7000-8000-000000000031"), kinds
            )
            for item in items:
                body = item.state.model_dump_json()
                self.assertNotIn("storage", body)
                self.assertNotIn("referenceLast4", body)

            charge = next(
                item for item in items if item.entity_type == "billing_charge"
            )
            self.assertEqual(charge.state.balance.paid, 40)
            self.assertEqual(charge.state.balance.state, "partially_paid")

    async def test_snapshot_is_empty_without_the_financial_grant(self):
        from src.api.accounts.domain.accounts import BillingPermissions

        assistant = context()
        assistant = type(assistant)(
            actor=assistant.actor, account=assistant.account,
            device_status="active", owner=False,
            billing_permissions=BillingPermissions(),
        )
        async with self.sessions() as db, db.begin():
            self.assertEqual(await snapshot_billing(db, assistant), [])
            granted = type(assistant)(
                actor=assistant.actor, account=assistant.account,
                device_status="active", owner=False,
                billing_permissions=BillingPermissions(billing_read="granted"),
            )
            self.assertNotEqual(await snapshot_billing(db, granted), [])


if __name__ == "__main__":
    unittest.main()
