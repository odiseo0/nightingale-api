import asyncio
import runpy
import unittest
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.accounts import AccountContext, AccountResponse
from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.billing.application.direct_payment_cases import (
    ChargeNotIssuedError,
    DirectPaymentRequest,
    register_direct_payment,
)
from src.api.billing.application.review_cases import (
    BillingRejectionRequest,
    PaymentExceedsBalanceError,
    ReportNotPendingError,
    reject_report,
)
from src.core import Err, Ok

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c9000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019c9000-0000-7000-8000-000000000010")
PATIENT_ID = UUID("019c9000-0000-7000-8000-000000000020")
CHARGE_ID = UUID("019c9000-0000-7000-8000-000000000030")
DRAFT_ID = UUID("019c9000-0000-7000-8000-000000000031")
GRANT_ID = UUID("019c9000-0000-7000-8000-000000000040")
REPORT_ID = UUID("019c9000-0000-7000-8000-000000000050")
RATE_ID = UUID("019c9000-0000-7000-8000-000000000060")
DEVICE_ID = UUID("019c9000-0000-7000-8000-000000000070")


def context() -> AccountContext:
    from datetime import datetime, timezone

    now = datetime(2026, 11, 27, tzinfo=timezone.utc)
    return AccountContext(
        actor=AuthenticatedActor(user_id=USER_ID, device_id=DEVICE_ID, token_id=uuid7()),
        account=AccountResponse(
            id=ACCOUNT_ID, kind="independent", owner_user_id=USER_ID,
            display_name="Fixture", time_zone="America/Caracas",
            location_name="Fixture", location_address="Fixture",
            location_country="VE", location_state="Fixture",
            location_city="Fixture", status="active", no_show_grace_minutes=15,
            created_at=now, updated_at=now, version=1,
        ),
        device_status="active",
        owner=True,
    )


def direct(**overrides) -> DirectPaymentRequest:
    base = {
        "operationId": str(uuid7()), "expectedVersion": 1,
        "paidOn": "2026-11-27", "amount": "25.00", "currency": "USD",
        "method": "efectivo ficticio", "evidenceNote": "recibo interno ficticio 12",
    }
    base.update(overrides)
    return DirectPaymentRequest.model_validate(base)


class DirectPaymentAndRejectionTests(unittest.IsolatedAsyncioTestCase):
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
                     nightingale.billing_exchange_rates, nightingale.audit_events,
                     nightingale.devices, nightingale.patient_charges,
                     nightingale.account_patients, nightingale.patients,
                     nightingale.account_sync_heads, nightingale.account_memberships,
                     nightingale.accounts, nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','direct-owner','Fixture');
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
            VALUES ('{DEVICE_ID}','{USER_ID}','Fixture device','0.1.0',1);
            INSERT INTO nightingale.patients (id) VALUES ('{PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio');
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,description,amount,currency,price_source,
                 status,issued_at,created_by)
            VALUES
                ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                 100.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}'),
                ('{DRAFT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Borrador ficticio',
                 50.00,'USD','base','draft',NULL,'{USER_ID}');
            INSERT INTO nightingale.patient_billing_grants
                (id,account_id,patient_id,charge_id,token_hash,actions,expires_at,created_by)
            VALUES ('{GRANT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{CHARGE_ID}',
                    '{"d" * 64}',ARRAY['read_charge','submit_report','read_result'],
                    '2026-12-27T15:00:00Z','{USER_ID}');
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method)
            VALUES ('{REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                    '2026-11-26',40.00,'USD','transferencia ficticia');
            INSERT INTO nightingale.billing_exchange_rates
                (id,account_id,rate_date,rate_ves_per_usd,source,registered_by)
            VALUES ('{RATE_ID}','{ACCOUNT_ID}','2026-11-26',400.25,'bcv-ficticio','{USER_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def test_rejection_keeps_balance_evidence_and_allows_resubmission(self):
        async with self.sessions() as db, db.begin():
            rejected = await reject_report(
                db, context(), REPORT_ID,
                BillingRejectionRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 1,
                    "reason": "captura ilegible ficticia",
                }),
            )
            self.assertIsInstance(rejected, Ok)
            self.assertEqual(rejected.value.status, "rejected")

            payments = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_payments")
            )
            self.assertEqual(payments, 0)
            status = await db.scalar(
                text("SELECT status FROM nightingale.patient_charges "
                     f"WHERE id='{CHARGE_ID}'")
            )
            self.assertEqual(status, "issued")

            again = await reject_report(
                db, context(), REPORT_ID,
                BillingRejectionRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 2,
                    "reason": "otra vez",
                }),
            )
            self.assertIsInstance(again.error, ReportNotPendingError)
            missing = await reject_report(
                db, context(), uuid7(),
                BillingRejectionRequest.model_validate({
                    "operationId": str(uuid7()), "expectedVersion": 1, "reason": "x",
                }),
            )
            self.assertIsInstance(missing.error, AccountObjectNotFound)

    async def test_direct_payment_has_its_own_origin_and_respects_the_balance(self):
        async with self.sessions() as db, db.begin():
            paid = await register_direct_payment(db, context(), CHARGE_ID, direct())
            self.assertIsInstance(paid, Ok)
            self.assertEqual(paid.value.origin, "staff_entry")
            self.assertEqual(paid.value.balance.paid, Decimal("25.00"))
            self.assertEqual(paid.value.balance.state, "partially_paid")

            origin = await db.scalar(
                text("SELECT origin FROM nightingale.patient_payments "
                     f"WHERE id='{paid.value.payment_id}'")
            )
            self.assertEqual(origin, "staff_entry")

            # A VES direct payment converts with the frozen BCV snapshot (D25).
            ves = await register_direct_payment(
                db, context(), CHARGE_ID,
                direct(amount="30018.75", currency="VES"),
            )
            self.assertEqual(ves.value.amount, Decimal("75.00"))
            self.assertEqual(ves.value.exchange_rate, Decimal("400.25"))
            self.assertEqual(ves.value.balance.state, "paid")

            exceeded = await register_direct_payment(
                db, context(), CHARGE_ID, direct(amount="1.00")
            )
            self.assertIsInstance(exceeded.error, PaymentExceedsBalanceError)

    async def test_direct_payment_needs_an_issued_charge(self):
        async with self.sessions() as db, db.begin():
            draft = await register_direct_payment(db, context(), DRAFT_ID, direct())
            self.assertIsInstance(draft.error, ChargeNotIssuedError)
            missing = await register_direct_payment(db, context(), uuid7(), direct())
            self.assertIsInstance(missing.error, AccountObjectNotFound)


if __name__ == "__main__":
    unittest.main()
