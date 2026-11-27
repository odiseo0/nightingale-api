import asyncio
import runpy
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.accounts import AccountContext, AccountResponse
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.billing.application.review_cases import (
    BillingApprovalRequest,
    PaymentExceedsBalanceError,
    ReportNotPendingError,
    approve_report,
)
from src.api.billing.domain.payments import CurrencyMismatchError
from src.core import Err, Ok

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c8000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019c8000-0000-7000-8000-000000000010")
PATIENT_ID = UUID("019c8000-0000-7000-8000-000000000020")
CHARGE_ID = UUID("019c8000-0000-7000-8000-000000000030")
GRANT_ID = UUID("019c8000-0000-7000-8000-000000000040")
REPORT_ID = UUID("019c8000-0000-7000-8000-000000000050")
VES_REPORT_ID = UUID("019c8000-0000-7000-8000-000000000051")
RATE_ID = UUID("019c8000-0000-7000-8000-000000000060")
DEVICE_ID = UUID("019c8000-0000-7000-8000-000000000070")


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


def approval(**overrides) -> BillingApprovalRequest:
    base = {
        "operationId": str(uuid7()), "expectedVersion": 1,
        "verifiedPaidOn": "2026-11-26", "verifiedAmount": "40.00",
        "verifiedCurrency": "USD", "method": "transferencia ficticia",
    }
    base.update(overrides)
    return BillingApprovalRequest.model_validate(base)


class BillingApprovalTests(unittest.IsolatedAsyncioTestCase):
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
            VALUES ('{USER_ID}','fixture','approval-owner','Fixture');
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
            INSERT INTO nightingale.patient_billing_grants
                (id,account_id,patient_id,charge_id,token_hash,actions,expires_at,created_by)
            VALUES ('{GRANT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{CHARGE_ID}',
                    '{"c" * 64}',ARRAY['read_charge','submit_report','read_result'],
                    '2026-12-27T15:00:00Z','{USER_ID}');
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method)
            VALUES
                ('{REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                 '2026-11-26',40.00,'USD','transferencia ficticia'),
                ('{VES_REPORT_ID}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                 '2026-11-26',16010.00,'VES','pago movil ficticio');
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

    async def test_approval_creates_one_payment_and_updates_the_balance(self):
        async with self.sessions() as db, db.begin():
            result = await approve_report(db, context(), REPORT_ID, approval())
            self.assertIsInstance(result, Ok)
            self.assertEqual(result.value.amount, Decimal("40.00"))
            self.assertEqual(result.value.balance.paid, Decimal("40.00"))
            self.assertEqual(result.value.balance.state, "partially_paid")

            row = await db.execute(
                text("SELECT status, version FROM nightingale.patient_payment_reports "
                     f"WHERE id='{REPORT_ID}'")
            )
            status, version = row.one()
            self.assertEqual((status, version), ("approved", 2))

            # A retry or a second reviewer never duplicates the payment.
            again = await approve_report(db, context(), REPORT_ID, approval())
            self.assertIsInstance(again.error, ReportNotPendingError)
            count = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_payments "
                     f"WHERE origin_report_id='{REPORT_ID}'")
            )
            self.assertEqual(count, 1)

    async def test_partial_payments_reach_paid_and_excess_is_rejected(self):
        async with self.sessions() as db, db.begin():
            first = await approve_report(db, context(), REPORT_ID, approval())
            self.assertEqual(first.value.balance.state, "partially_paid")

            second = await approve_report(
                db, context(), VES_REPORT_ID,
                approval(verifiedAmount="24015.00", verifiedCurrency="VES"),
            )
            # 24015.00 VES at 400.25 converts to exactly 60.00 USD (D25 snapshot).
            self.assertEqual(second.value.amount, Decimal("60.00"))
            self.assertEqual(second.value.balance.state, "paid")
            stored = await db.scalar(
                text("SELECT exchange_rate FROM nightingale.patient_payments "
                     f"WHERE origin_report_id='{VES_REPORT_ID}'")
            )
            self.assertEqual(stored, Decimal("400.25"))

            extra = uuid7()
            await db.execute(text(f"""
                INSERT INTO nightingale.patient_payment_reports
                    (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                     declared_amount,declared_currency,declared_method)
                VALUES ('{extra}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}','{GRANT_ID}',
                        '2026-11-27',10.00,'USD','efectivo ficticio')
            """))
            exceeded = await approve_report(
                db, context(), extra, approval(verifiedAmount="10.00")
            )
            self.assertIsInstance(exceeded.error, PaymentExceedsBalanceError)
            active = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_payments "
                     f"WHERE charge_id='{CHARGE_ID}' AND status='active'")
            )
            self.assertEqual(active, 2)

    async def test_two_concurrent_reviewers_produce_one_payment(self):
        # Two reviewers dispute the same pending report on separate connections:
        # the report/charge row locks and the origin UQ leave exactly one payment.
        async def contender():
            async with self.sessions() as db:
                try:
                    async with db.begin():
                        return await approve_report(db, context(), REPORT_ID, approval())
                except Exception as error:  # lost the lock race after commit
                    return error

        first, second = await asyncio.gather(contender(), contender())
        outcomes = [first, second]
        accepted = [item for item in outcomes if isinstance(item, Ok)]
        self.assertEqual(len(accepted), 1)
        async with self.sessions() as db:
            count = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_payments "
                     f"WHERE origin_report_id='{REPORT_ID}'")
            )
            self.assertEqual(count, 1)

    async def test_ves_payment_without_rate_is_rejected(self):
        await self.admin.execute(
            f"DELETE FROM nightingale.billing_exchange_rates WHERE id='{RATE_ID}'"
        )
        async with self.sessions() as db, db.begin():
            result = await approve_report(
                db, context(), VES_REPORT_ID,
                approval(verifiedAmount="16010.00", verifiedCurrency="VES"),
            )
            self.assertIsInstance(result.error, CurrencyMismatchError)
            untouched = await db.scalar(
                text("SELECT status FROM nightingale.patient_payment_reports "
                     f"WHERE id='{VES_REPORT_ID}'")
            )
            self.assertEqual(untouched, "pending")


if __name__ == "__main__":
    unittest.main()
