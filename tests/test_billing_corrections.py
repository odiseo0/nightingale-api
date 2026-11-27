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
from src.api.billing.application.charge_cases import apply_charge_operation
from src.api.billing.application.correction_cases import (
    PaymentAlreadyAnnulledError,
    PaymentAnnulmentRequest,
    annul_payment,
)
from src.api.billing.application.direct_payment_cases import (
    DirectPaymentRequest,
    register_direct_payment,
)
from src.api.billing.domain.charges import CancelPatientChargePayload
from src.core import Err, Ok

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019ca000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019ca000-0000-7000-8000-000000000010")
PATIENT_ID = UUID("019ca000-0000-7000-8000-000000000020")
CHARGE_ID = UUID("019ca000-0000-7000-8000-000000000030")
DEVICE_ID = UUID("019ca000-0000-7000-8000-000000000070")


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


def direct(amount: str) -> DirectPaymentRequest:
    return DirectPaymentRequest.model_validate({
        "operationId": str(uuid7()), "expectedVersion": 1,
        "paidOn": "2026-11-27", "amount": amount, "currency": "USD",
        "method": "efectivo ficticio", "evidenceNote": "recibo interno ficticio",
    })


def annulment(reason: str = "duplicado ficticio") -> PaymentAnnulmentRequest:
    return PaymentAnnulmentRequest.model_validate({
        "operationId": str(uuid7()), "expectedVersion": 1, "reason": reason,
    })


class BillingCorrectionTests(unittest.IsolatedAsyncioTestCase):
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
            VALUES ('{USER_ID}','fixture','corrections-owner','Fixture');
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

    async def test_annulment_excludes_the_payment_without_deleting_history(self):
        async with self.sessions() as db, db.begin():
            first = await register_direct_payment(db, context(), CHARGE_ID, direct("40.00"))
            await register_direct_payment(db, context(), CHARGE_ID, direct("25.00"))

            annulled = await annul_payment(
                db, context(), first.value.payment_id, annulment()
            )
            self.assertIsInstance(annulled, Ok)
            self.assertEqual(annulled.value.status, "annulled")
            # The annulled 40.00 stops summing; the active 25.00 remains (§13.5).
            self.assertEqual(annulled.value.balance.paid, Decimal("25.00"))
            self.assertEqual(annulled.value.balance.outstanding, Decimal("75.00"))
            self.assertNotIn("refund", annulled.value.model_dump_json().lower())

            row = await db.execute(
                text("SELECT annulled_by, annulment_reason, version "
                     f"FROM nightingale.patient_payments WHERE id='{first.value.payment_id}'")
            )
            actor, reason, version = row.one()
            self.assertEqual((actor, reason, version), (USER_ID, "duplicado ficticio", 2))

            again = await annul_payment(db, context(), first.value.payment_id, annulment())
            self.assertIsInstance(again.error, PaymentAlreadyAnnulledError)
            missing = await annul_payment(db, context(), uuid7(), annulment())
            self.assertIsInstance(missing.error, AccountObjectNotFound)

    async def test_charge_with_annulled_payments_can_be_cancelled(self):
        async with self.sessions() as db, db.begin():
            paid = await register_direct_payment(db, context(), CHARGE_ID, direct("100.00"))
            blocked = await apply_charge_operation(
                db, context(), "CancelPatientCharge", CHARGE_ID, 1,
                CancelPatientChargePayload(reason="error ficticio"),
            )
            self.assertEqual(blocked.error.code, "CHARGE_HAS_ACTIVE_PAYMENTS")

            # D27: annul the payments first, then the charge can be cancelled
            # keeping all history.
            await annul_payment(db, context(), paid.value.payment_id, annulment())
            cancelled = await apply_charge_operation(
                db, context(), "CancelPatientCharge", CHARGE_ID, 1,
                CancelPatientChargePayload(reason="cargo duplicado ficticio"),
            )
            self.assertIsInstance(cancelled, Ok)
            self.assertEqual(cancelled.value.state.status, "cancelled")
            kept = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_payments "
                     f"WHERE charge_id='{CHARGE_ID}'")
            )
            self.assertEqual(kept, 1)


if __name__ == "__main__":
    unittest.main()
