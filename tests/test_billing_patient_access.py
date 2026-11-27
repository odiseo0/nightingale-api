import asyncio
import hashlib
import runpy
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.accounts.domain.accounts import AccountContext, AccountResponse
from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.billing.application.grant_cases import issue_grant, revoke_grant
from src.api.billing.application.patient_cases import (
    GrantNotUsable,
    read_patient_charges,
    usable_grant,
)
from src.api.billing.domain.payments import GrantCreateRequest
from src.core import Err, Ok

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c5000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019c5000-0000-7000-8000-000000000010")
PATIENT_ID = UUID("019c5000-0000-7000-8000-000000000020")
OTHER_PATIENT_ID = UUID("019c5000-0000-7000-8000-000000000021")
CHARGE_ID = UUID("019c5000-0000-7000-8000-000000000030")
DRAFT_ID = UUID("019c5000-0000-7000-8000-000000000031")
APPOINTMENT_ID = UUID("019c5000-0000-7000-8000-000000000040")
PROFESSIONAL_ID = UUID("019c5000-0000-7000-8000-000000000050")
SERVICE_ID = UUID("019c5000-0000-7000-8000-000000000051")
DEVICE_ID = UUID("019c5000-0000-7000-8000-000000000060")


def context() -> AccountContext:
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


def grant_request(**overrides) -> GrantCreateRequest:
    base = {
        "operationId": str(uuid7()),
        "patientId": str(PATIENT_ID),
        "chargeId": str(CHARGE_ID),
        "actions": ["read_charge", "submit_report", "read_result"],
    }
    base.update(overrides)
    return GrantCreateRequest.model_validate(base)


class PatientAccessTests(unittest.IsolatedAsyncioTestCase):
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
            TRUNCATE nightingale.audit_events, nightingale.devices,
                     nightingale.patient_billing_grants, nightingale.patient_payments,
                     nightingale.patient_charges, nightingale.appointment_histories,
                     nightingale.appointments, nightingale.professional_services,
                     nightingale.services, nightingale.account_patients,
                     nightingale.patients, nightingale.account_professionals,
                     nightingale.professionals, nightingale.account_sync_heads,
                     nightingale.account_memberships, nightingale.accounts,
                     nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','grants-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','independent','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.devices
                (id,user_id,display_name,client_version,local_schema_version)
            VALUES ('{DEVICE_ID}','{USER_ID}','Fixture device','0.1.0',1);
            INSERT INTO nightingale.professionals (id,user_id,public_name)
            VALUES ('{PROFESSIONAL_ID}','{USER_ID}','Profesional ficticio');
            INSERT INTO nightingale.account_professionals (account_id,professional_id,user_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{USER_ID}');
            INSERT INTO nightingale.patients (id)
            VALUES ('{PATIENT_ID}'),('{OTHER_PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio'),
                   ('{ACCOUNT_ID}','{OTHER_PATIENT_ID}','Otro ficticio');
            INSERT INTO nightingale.services (id,professional_id,name,default_duration_minutes)
            VALUES ('{SERVICE_ID}','{PROFESSIONAL_ID}','Consulta ficticia',30);
            INSERT INTO nightingale.professional_services (account_id,professional_id,service_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}');
            INSERT INTO nightingale.appointments
                (id,account_id,patient_id,professional_id,service_id,starts_at,ends_at,status,
                 version,service_name_snapshot,offered_duration_minutes_snapshot,
                 professional_name_snapshot,location_name_snapshot,location_address_snapshot,
                 location_country_snapshot,location_state_snapshot,location_city_snapshot,
                 time_zone_snapshot)
            VALUES
                ('{APPOINTMENT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}',
                 '2026-12-01T13:00:00Z','2026-12-01T13:30:00Z','scheduled',1,
                 'Consulta ficticia',30,'Profesional ficticio','Fixture','Fixture','VE',
                 'Fixture','Fixture','America/Caracas');
            INSERT INTO nightingale.appointment_histories
                (appointment_id,account_id,starts_at,ends_at,status,version,
                 service_name_snapshot,offered_duration_minutes_snapshot,
                 professional_name_snapshot,location_name_snapshot,location_address_snapshot,
                 location_country_snapshot,location_state_snapshot,location_city_snapshot,
                 time_zone_snapshot,action,actor_kind,actor_user_id,changed_at)
            VALUES
                ('{APPOINTMENT_ID}','{ACCOUNT_ID}','2026-12-01T13:00:00Z','2026-12-01T13:30:00Z',
                 'scheduled',1,'Consulta ficticia',30,'Profesional ficticio','Fixture','Fixture',
                 'VE','Fixture','Fixture','America/Caracas','created','staff','{USER_ID}',
                 CURRENT_TIMESTAMP);
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,appointment_id,description,amount,currency,
                 price_source,status,issued_at,created_by)
            VALUES
                ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{APPOINTMENT_ID}',
                 'Consulta ficticia',100.00,'USD','base','issued',
                 '2026-12-01T14:00:00Z','{USER_ID}'),
                ('{DRAFT_ID}','{ACCOUNT_ID}','{PATIENT_ID}','{APPOINTMENT_ID}',
                 'Borrador ficticio',50.00,'USD','base','draft',NULL,'{USER_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def test_issue_delivers_the_secret_once_and_retries_idempotently(self):
        async with self.sessions() as db, db.begin():
            data = grant_request()
            issued = await issue_grant(db, context(), data)
            self.assertIsInstance(issued, Ok)
            self.assertIsNotNone(issued.value.secret)
            # The expiry of a charge grant is bounded to 30 days (D28).
            self.assertLessEqual(
                issued.value.expires_at,
                datetime.now(timezone.utc) + timedelta(days=31),
            )

            stored = await db.scalar(
                text("SELECT token_hash FROM nightingale.patient_billing_grants "
                     "WHERE id=:id"),
                {"id": data.operation_id},
            )
            self.assertEqual(
                stored, hashlib.sha256(issued.value.secret.encode()).hexdigest()
            )
            self.assertNotEqual(stored, issued.value.secret)

            retry = await issue_grant(db, context(), data)
            self.assertTrue(retry.value.duplicate)
            self.assertIsNone(retry.value.secret)
            count = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_billing_grants")
            )
            self.assertEqual(count, 1)

    async def test_appointment_grant_expires_thirty_days_after_the_end(self):
        async with self.sessions() as db, db.begin():
            data = grant_request(chargeId=None, appointmentId=str(APPOINTMENT_ID))
            issued = await issue_grant(db, context(), data)
            self.assertEqual(
                issued.value.expires_at,
                datetime(2026, 12, 31, 13, 30, tzinfo=timezone.utc),
            )

    async def test_valid_link_reads_only_its_charge_without_drafts(self):
        async with self.sessions() as db, db.begin():
            issued = await issue_grant(db, context(), grant_request())
            view = await read_patient_charges(db, issued.value.secret)
            self.assertIsInstance(view, Ok)
            self.assertEqual(view.value["total"], 1)
            item = view.value["items"][0]
            self.assertEqual(item.charge_id, CHARGE_ID)
            self.assertEqual(item.outstanding, Decimal("100.00"))
            self.assertEqual(item.balance_state, "unpaid")

            # The draft of the same appointment never appears through the link.
            appointment_grant = await issue_grant(
                db, context(),
                grant_request(chargeId=None, appointmentId=str(APPOINTMENT_ID)),
            )
            listed = await read_patient_charges(db, appointment_grant.value.secret)
            ids = [item.charge_id for item in listed.value["items"]]
            self.assertEqual(ids, [CHARGE_ID])

    async def test_expired_revoked_foreign_or_actionless_links_are_absent(self):
        async with self.sessions() as db, db.begin():
            issued = await issue_grant(db, context(), grant_request())
            secret = issued.value.secret

            wrong_action = await usable_grant(db, secret, "read_receipt")
            self.assertIsInstance(wrong_action.error, GrantNotUsable)

            missing = await usable_grant(db, "0" * 64, "read_charge")
            self.assertIsInstance(missing.error, GrantNotUsable)

            self.assertIsInstance(
                (await usable_grant(db, None, "read_charge")).error, GrantNotUsable
            )

            revoked = await revoke_grant(db, context(), issued.value.grant_id)
            self.assertEqual(revoked.value.status, "revoked")
            after = await read_patient_charges(db, secret)
            self.assertIsInstance(after.error, GrantNotUsable)
            # The row and its history remain after revocation.
            kept = await db.scalar(
                text("SELECT count(*) FROM nightingale.patient_billing_grants "
                     "WHERE id=:id AND revoked_at IS NOT NULL"),
                {"id": issued.value.grant_id},
            )
            self.assertEqual(kept, 1)

            await self.admin.execute(
                "UPDATE nightingale.patient_billing_grants "
                "SET expires_at='2026-01-01T00:00:00Z' "
                f"WHERE id='{issued.value.grant_id}'"
            )
            expired = await usable_grant(db, secret, "read_charge")
            self.assertIsInstance(expired.error, GrantNotUsable)

    async def test_cancelling_the_appointment_revokes_its_grants(self):
        from src.api.billing.application.grant_cases import revoke_appointment_grants

        async with self.sessions() as db, db.begin():
            anchored = await issue_grant(
                db, context(),
                grant_request(chargeId=None, appointmentId=str(APPOINTMENT_ID)),
            )
            loose = await issue_grant(db, context(), grant_request())
            revoked = await revoke_appointment_grants(
                db, ACCOUNT_ID, APPOINTMENT_ID, datetime.now(timezone.utc)
            )
            self.assertEqual(revoked, 1)
            # Only the anchored grant is revoked; the charge grant survives (D28).
            self.assertIsInstance(
                (await usable_grant(db, anchored.value.secret, "read_charge")).error,
                GrantNotUsable,
            )
            self.assertIsInstance(
                await usable_grant(db, loose.value.secret, "read_charge"), Ok
            )

    async def test_grant_needs_a_coherent_object_of_the_account(self):
        async with self.sessions() as db, db.begin():
            with self.assertRaises(Exception):
                grant_request(chargeId=None)
            crossed = await issue_grant(
                db, context(), grant_request(patientId=str(OTHER_PATIENT_ID))
            )
            self.assertIsInstance(crossed.error, AccountObjectNotFound)
            unknown = await issue_grant(
                db, context(), grant_request(chargeId=str(uuid7()))
            )
            self.assertIsInstance(unknown.error, AccountObjectNotFound)


if __name__ == "__main__":
    unittest.main()
