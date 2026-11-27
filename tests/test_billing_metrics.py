import asyncio
import runpy
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.billing.application.correction_cases import annul_payment
from src.api.billing.application.direct_payment_cases import (
    DirectPaymentRequest,
    register_direct_payment,
)
from src.api.billing.application.metrics_cases import billing_metrics
from tests.test_billing_corrections import ACCOUNT_ID, CHARGE_ID, PATIENT_ID, USER_ID, context

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

WINDOW_FROM = datetime(2026, 11, 1, tzinfo=timezone.utc)
WINDOW_UNTIL = datetime(2026, 12, 1, tzinfo=timezone.utc)


def direct(amount: str, currency: str = "USD") -> DirectPaymentRequest:
    return DirectPaymentRequest.model_validate({
        "operationId": str(uuid7()), "expectedVersion": 1,
        "paidOn": "2026-11-27", "amount": amount, "currency": currency,
        "method": "efectivo ficticio", "evidenceNote": "recibo ficticio",
    })


class BillingMetricsTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.billing_reviews, nightingale.patient_payments,
                     nightingale.patient_payment_reports, nightingale.patient_billing_grants,
                     nightingale.charge_histories, nightingale.audit_events,
                     nightingale.devices, nightingale.patient_charges,
                     nightingale.account_patients, nightingale.patients,
                     nightingale.account_sync_heads, nightingale.account_memberships,
                     nightingale.accounts, nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','metrics-owner','Fixture');
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
                ('019ca000-0000-7000-8000-000000000032','{ACCOUNT_ID}','{PATIENT_ID}',
                 'Control ficticio',7204.50,'VES','base','issued',
                 '2026-11-27T15:00:00Z','{USER_ID}'),
                ('019ca000-0000-7000-8000-000000000033','{ACCOUNT_ID}','{PATIENT_ID}',
                 'Borrador ficticio',50.00,'USD','base','draft',NULL,'{USER_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def test_panel_separates_currencies_and_states(self):
        async with self.sessions() as db, db.begin():
            partial = await register_direct_payment(
                db, context(), CHARGE_ID, direct("40.00")
            )
            await register_direct_payment(
                db, context(), "019ca000-0000-7000-8000-000000000032", direct("7204.50", "VES")
            )
            annulled = await register_direct_payment(
                db, context(), CHARGE_ID, direct("10.00")
            )
            from src.api.billing.application.correction_cases import PaymentAnnulmentRequest

            await annul_payment(
                db, context(), annulled.value.payment_id,
                PaymentAnnulmentRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 1,
                    "reason": "duplicado ficticio",
                }),
            )

            panel = await billing_metrics(db, ACCOUNT_ID, WINDOW_FROM, WINDOW_UNTIL)
            charged = {a.currency: a.amount for a in panel.charged}
            self.assertEqual(charged, {"USD": Decimal("100.00"), "VES": Decimal("7204.50")})
            collected = {a.currency: a.amount for a in panel.collected}
            # Annulled payments never count as collected; currencies never mix.
            self.assertEqual(collected, {"USD": Decimal("40.00"), "VES": Decimal("7204.50")})
            outstanding = {a.currency: a.amount for a in panel.outstanding}
            self.assertEqual(outstanding, {"USD": Decimal("60.00"), "VES": Decimal("0.00")})
            annulments = {a.currency: a.amount for a in panel.annulments}
            self.assertEqual(annulments, {"USD": Decimal("10.00")})
            self.assertEqual(panel.partially_paid, 1)
            self.assertEqual(panel.paid_charges, 1)
            self.assertEqual(panel.pending_review, 0)
            self.assertEqual(panel.basis_charged_by, "issueDate")
            self.assertEqual(panel.basis_collected_by, "approvalDate")

            empty = await billing_metrics(
                db, ACCOUNT_ID, WINDOW_UNTIL, WINDOW_UNTIL + timedelta(days=30)
            )
            self.assertEqual(empty.charged, [])
            self.assertEqual(empty.paid_charges, 0)


if __name__ == "__main__":
    unittest.main()
