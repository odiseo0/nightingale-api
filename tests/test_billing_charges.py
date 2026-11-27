import asyncio
import runpy
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.accounts import (
    AccountContext,
    AccountResponse,
    BillingPermissions,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.authorization.domain.errors import AccessDenied
from src.api.billing.application.charge_cases import apply_charge_operation
from src.api.billing.domain.charges import (
    CancelPatientChargePayload,
    CreatePatientChargePayload,
    IssuePatientChargePayload,
    UpdatePatientChargePayload,
)
from src.core import Err, Ok

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c0000-0000-7000-8000-0000000000a1")
ASSISTANT_ID = UUID("019c0000-0000-7000-8000-0000000000a4")
ACCOUNT_ID = UUID("019c0000-0000-7000-8000-0000000000a2")
PROFESSIONAL_ID = UUID("019c0000-0000-7000-8000-0000000000b1")
PATIENT_ID = UUID("019c0000-0000-7000-8000-0000000000c1")
SERVICE_ID = UUID("019c0000-0000-7000-8000-0000000000d1")


def context(owner: bool = True, billing: BillingPermissions | None = None) -> AccountContext:
    now = datetime(2026, 11, 27, tzinfo=timezone.utc)
    return AccountContext(
        actor=AuthenticatedActor(user_id=USER_ID if owner else ASSISTANT_ID,
                                 device_id=uuid7(), token_id=uuid7()),
        account=AccountResponse(
            id=ACCOUNT_ID, kind="independent", owner_user_id=USER_ID,
            display_name="Fixture", time_zone="America/Caracas",
            location_name="Fixture", location_address="Fixture",
            location_country="VE", location_state="Fixture",
            location_city="Fixture", status="active", no_show_grace_minutes=15,
            created_at=now, updated_at=now, version=1,
        ),
        device_status="active",
        owner=owner,
        billing_permissions=billing or BillingPermissions(),
    )


class ChargePayloadTests(unittest.TestCase):
    def test_create_requires_price_source_or_manual_reason(self):
        base = {"patientId": str(PATIENT_ID)}
        # Service without amount resolves the price; free charge needs a description.
        CreatePatientChargePayload.model_validate({**base, "serviceId": str(SERVICE_ID)})
        CreatePatientChargePayload.model_validate({**base, "description": "Curso ficticio",
                                                   "amount": "0.00", "currency": "USD",
                                                   "adjustReason": "beca ficticia"})
        for invalid in (
            {**base, "amount": "18.00", "currency": "USD"},  # manual without reason
            {**base, "amount": "18.00", "adjustReason": "x"},  # amount without currency
            {**base, "currency": "USD"},  # currency without amount
            base,  # neither service nor description/amount
            {**base, "amount": "-1.00", "currency": "USD", "adjustReason": "x"},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                CreatePatientChargePayload.model_validate(invalid)

    def test_update_requires_at_least_one_coherent_field(self):
        with self.assertRaises(ValidationError):
            UpdatePatientChargePayload.model_validate({})
        with self.assertRaises(ValidationError):
            UpdatePatientChargePayload.model_validate({"amount": "20.00"})
        UpdatePatientChargePayload.model_validate({"description": "Nueva descripción"})


class ChargeOperationTests(unittest.IsolatedAsyncioTestCase):
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
        await self.admin.execute("""
            TRUNCATE nightingale.charge_histories, nightingale.patient_payments,
                     nightingale.patient_charges, nightingale.service_offer_prices,
                     nightingale.service_prices, nightingale.account_patients,
                     nightingale.patients, nightingale.professional_services,
                     nightingale.services, nightingale.account_professionals,
                     nightingale.professionals, nightingale.account_sync_heads,
                     nightingale.account_memberships, nightingale.accounts,
                     nightingale.app_users CASCADE;
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','charges-owner','Fixture'),
                   ('{ASSISTANT_ID}','fixture','charges-assistant','Asistente');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','independent','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}'),('{ACCOUNT_ID}','{ASSISTANT_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.professionals (id,user_id,public_name)
            VALUES ('{PROFESSIONAL_ID}','{USER_ID}','Profesional ficticio');
            INSERT INTO nightingale.account_professionals (account_id,professional_id,user_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{USER_ID}');
            INSERT INTO nightingale.patients (id) VALUES ('{PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio');
            INSERT INTO nightingale.services (id,professional_id,name,default_duration_minutes)
            VALUES ('{SERVICE_ID}','{PROFESSIONAL_ID}','Consulta ficticia',30);
            INSERT INTO nightingale.professional_services (account_id,professional_id,service_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}');
            INSERT INTO nightingale.service_prices (professional_id,service_id,amount,currency)
            VALUES ('{PROFESSIONAL_ID}','{SERVICE_ID}',18.00,'USD');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def create_charge(self, db, ctx, **payload) -> tuple:
        charge_id = uuid7()
        result = await apply_charge_operation(
            db, ctx, "CreatePatientCharge", charge_id, 0,
            CreatePatientChargePayload.model_validate(
                {"patientId": str(PATIENT_ID), **payload}
            ),
        )
        return charge_id, result

    async def test_create_from_service_snapshots_price_and_description(self):
        async with self.sessions() as db, db.begin():
            charge_id, result = await self.create_charge(
                db, context(), serviceId=str(SERVICE_ID)
            )
            self.assertIsInstance(result, Ok)
            state = result.value.state
            self.assertEqual((state.amount, state.currency, state.price_source),
                             (Decimal("18.00"), "USD", "base"))
            self.assertEqual(state.description, "Consulta ficticia")
            self.assertEqual(state.status, "draft")
            self.assertEqual(state.balance.state, "unpaid")
            change = result.value.changes[0]
            self.assertEqual((change.entity_type, change.audience), ("billing_charge", "billing"))
            history = await db.scalar(
                text("SELECT action FROM nightingale.charge_histories "
                     "WHERE charge_id=:id"),
                {"id": charge_id},
            )
            self.assertEqual(history, "created")

    async def test_assistant_needs_the_billing_charges_grant(self):
        async with self.sessions() as db, db.begin():
            _, denied = await self.create_charge(
                db, context(owner=False), serviceId=str(SERVICE_ID)
            )
            self.assertIsInstance(denied, Err)
            self.assertIsInstance(denied.error, AccessDenied)

            granted = BillingPermissions(billing_charges="granted")
            _, allowed = await self.create_charge(
                db, context(owner=False, billing=granted), serviceId=str(SERVICE_ID)
            )
            self.assertIsInstance(allowed, Ok)

    async def test_unknown_patient_or_link_is_a_uniform_404(self):
        async with self.sessions() as db, db.begin():
            _, missing = await self.create_charge(
                db, context(), patientId=str(uuid7()), serviceId=str(SERVICE_ID)
            )
            self.assertIsInstance(missing.error, AccountObjectNotFound)
            _, bad_link = await self.create_charge(
                db, context(), serviceId=str(SERVICE_ID), appointmentId=str(uuid7())
            )
            self.assertIsInstance(bad_link.error, AccountObjectNotFound)

    async def test_manual_adjustment_and_draft_edition(self):
        async with self.sessions() as db, db.begin():
            charge_id, created = await self.create_charge(
                db, context(), description="Cargo libre ficticio", amount="25.00",
                currency="USD", adjustReason="ajuste autorizado ficticio",
            )
            self.assertEqual(created.value.state.price_source, "manual")
            updated = await apply_charge_operation(
                db, context(), "UpdatePatientCharge", charge_id, 1,
                UpdatePatientChargePayload.model_validate(
                    {"amount": "20.00", "currency": "USD",
                     "adjustReason": "descuento ficticio"}
                ),
            )
            self.assertIsInstance(updated, Ok)
            self.assertEqual(updated.value.state.amount, Decimal("20.00"))
            actions = await db.scalar(
                text("SELECT array_agg(action ORDER BY created_at, id) "
                     "FROM nightingale.charge_histories WHERE charge_id=:id"),
                {"id": charge_id},
            )
            self.assertEqual(actions, ["created", "amount_adjusted"])

    async def test_issue_freeze_cancel_and_payment_guard(self):
        async with self.sessions() as db, db.begin():
            charge_id, _ = await self.create_charge(db, context(), serviceId=str(SERVICE_ID))
            issued = await apply_charge_operation(
                db, context(), "IssuePatientCharge", charge_id, 1,
                IssuePatientChargePayload(),
            )
            self.assertEqual(issued.value.state.status, "issued")
            # The snapshot is frozen: edits after issue are rejected.
            frozen = await apply_charge_operation(
                db, context(), "UpdatePatientCharge", charge_id, 2,
                UpdatePatientChargePayload.model_validate({"description": "otra"}),
            )
            self.assertEqual(frozen.error.code, "CHARGE_NOT_DRAFT")

            # An active payment blocks cancellation (D27).
            await db.execute(text("""
                INSERT INTO nightingale.patient_payments
                    (id,account_id,charge_id,patient_id,origin,amount,currency,paid_on,
                     method,registered_by)
                VALUES (:id,:account,:charge,:patient,'staff_entry',18.00,'USD',
                        '2026-11-27','efectivo ficticio',:actor)
            """), {"id": uuid7(), "account": ACCOUNT_ID, "charge": charge_id,
                    "patient": PATIENT_ID, "actor": USER_ID})
            blocked = await apply_charge_operation(
                db, context(), "CancelPatientCharge", charge_id, 2,
                CancelPatientChargePayload(reason="error ficticio"),
            )
            self.assertIsInstance(blocked.error, AccountRuleError)
            self.assertEqual(blocked.error.code, "CHARGE_HAS_ACTIVE_PAYMENTS")

    async def test_cancel_without_payments_keeps_history(self):
        async with self.sessions() as db, db.begin():
            charge_id, _ = await self.create_charge(db, context(), serviceId=str(SERVICE_ID))
            await apply_charge_operation(
                db, context(), "IssuePatientCharge", charge_id, 1,
                IssuePatientChargePayload(),
            )
            cancelled = await apply_charge_operation(
                db, context(), "CancelPatientCharge", charge_id, 2,
                CancelPatientChargePayload(reason="cita cancelada ficticia"),
            )
            self.assertEqual(cancelled.value.state.status, "cancelled")
            stale = await apply_charge_operation(
                db, context(), "CancelPatientCharge", charge_id, 2,
                CancelPatientChargePayload(reason="otra"),
            )
            self.assertEqual(stale.error.code, "VERSION_CONFLICT")

    async def test_offline_prepared_draft_revalidates_the_current_price(self):
        # D28: the operation was prepared while offline; acceptance resolves the
        # CURRENT catalog price, never a stale local copy.
        async with self.sessions() as db, db.begin():
            from sqlalchemy import text as sql

            await db.execute(sql(
                "UPDATE nightingale.service_prices SET amount=20.00, version=version+1 "
                f"WHERE service_id='{SERVICE_ID}'"
            ))
            _, result = await self.create_charge(db, context(), serviceId=str(SERVICE_ID))
            self.assertEqual(result.value.state.amount, Decimal("20.00"))

    async def test_missing_price_is_reported(self):
        async with self.sessions() as db, db.begin():
            await self.admin.execute(
                f"DELETE FROM nightingale.service_prices "
                f"WHERE service_id='{SERVICE_ID}'"
            )
            _, result = await self.create_charge(db, context(), serviceId=str(SERVICE_ID))
            self.assertIsInstance(result, Err)
            self.assertEqual(result.error.code, "PRICE_NOT_DEFINED")


if __name__ == "__main__":
    unittest.main()
