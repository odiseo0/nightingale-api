import asyncio
import runpy
import unittest
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from datetime import datetime, timezone

from src.api.accounts.domain.accounts import AccountContext, AccountResponse
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.billing.application.grant_cases import issue_grant
from src.api.billing.application.patient_cases import GrantNotUsable
from src.api.billing.application.report_cases import (
    PatientReportSubmit,
    ReportNotFound,
    ReportRejected,
    list_own_reports,
    read_own_report,
    submit_report,
)
from src.api.billing.domain.payments import GrantCreateRequest
from src.core import Err, Ok
from src.settings.storage_settings import storage_settings

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = UUID("019c6000-0000-7000-8000-000000000001")
ACCOUNT_ID = UUID("019c6000-0000-7000-8000-000000000010")
PATIENT_ID = UUID("019c6000-0000-7000-8000-000000000020")
OTHER_PATIENT_ID = UUID("019c6000-0000-7000-8000-000000000021")
CHARGE_ID = UUID("019c6000-0000-7000-8000-000000000030")
OTHER_CHARGE_ID = UUID("019c6000-0000-7000-8000-000000000031")
DEVICE_ID = UUID("019c6000-0000-7000-8000-000000000060")

PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-capture" * 4


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


def submit_payload(**overrides) -> PatientReportSubmit:
    base = {
        "operationId": str(uuid7()),
        "chargeId": str(CHARGE_ID),
        "paidOn": "2026-11-26",
        "amount": "40.00",
        "currency": "USD",
        "method": "transferencia ficticia",
        "referenceLast4": "0071",
    }
    base.update(overrides)
    return PatientReportSubmit.model_validate(base)


class PatientReportTests(unittest.IsolatedAsyncioTestCase):
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
                     nightingale.patient_payments, nightingale.patient_payment_reports,
                     nightingale.patient_billing_grants, nightingale.audit_events,
                     nightingale.devices, nightingale.patient_charges,
                     nightingale.account_patients, nightingale.patients,
                     nightingale.account_sync_heads, nightingale.account_memberships,
                     nightingale.accounts, nightingale.app_users CASCADE;
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','reports-owner','Fixture');
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
            INSERT INTO nightingale.patients (id)
            VALUES ('{PATIENT_ID}'),('{OTHER_PATIENT_ID}');
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio'),
                   ('{ACCOUNT_ID}','{OTHER_PATIENT_ID}','Otro ficticio');
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,description,amount,currency,price_source,
                 status,issued_at,created_by)
            VALUES
                ('{CHARGE_ID}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                 100.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}'),
                ('{OTHER_CHARGE_ID}','{ACCOUNT_ID}','{OTHER_PATIENT_ID}','Ajena ficticia',
                 80.00,'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.sessions() as db, db.begin():
            issued = await issue_grant(
                db, context(),
                GrantCreateRequest.model_validate({
                    "operationId": str(uuid7()), "patientId": str(PATIENT_ID),
                    "chargeId": str(CHARGE_ID),
                    "actions": ["read_charge", "submit_report", "read_result"],
                }),
            )
            self.secret = issued.value.secret

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()
        folder = Path(storage_settings.STORAGE_ROOT) / str(ACCOUNT_ID)
        if folder.is_dir():
            for item in folder.iterdir():
                item.unlink()
            folder.rmdir()

    async def test_submission_is_pending_without_balance_effect_and_idempotent(self):
        data = submit_payload()
        async with self.sessions() as db:
            first = await submit_report(db, self.secret, data, PNG)
            self.assertIsInstance(first, Ok)
            self.assertEqual(first.value.status, "pending")
            self.assertFalse(first.value.duplicate)

            active = await self.admin.fetchval(
                "SELECT count(*) FROM nightingale.patient_payments "
                f"WHERE charge_id='{CHARGE_ID}'"
            )
            self.assertEqual(active, 0)
            evidence = await self.admin.fetchval(
                "SELECT count(*) FROM nightingale.patient_payment_evidence "
                f"WHERE report_id='{data.operation_id}'"
            )
            self.assertEqual(evidence, 1)

            # A lost response retried with the same operation id recovers the
            # same report without duplicating capture or effect.
            retry = await submit_report(db, self.secret, data, PNG)
            self.assertTrue(retry.value.duplicate)
            count = await self.admin.fetchval(
                "SELECT count(*) FROM nightingale.patient_payment_reports "
                f"WHERE charge_id='{CHARGE_ID}'"
            )
            self.assertEqual(count, 1)

    async def test_capture_is_mandatory_and_validated_by_signature(self):
        async with self.sessions() as db:
            for content, reason in ((b"", "invalid_size"),
                                    (b"GIF89a-no", "invalid_type")):
                with self.subTest(reason=reason):
                    result = await submit_report(db, self.secret, submit_payload(), content)
                    self.assertIsInstance(result, Err)
                    self.assertEqual(result.error, ReportRejected(reason))
            count = await self.admin.fetchval(
                "SELECT count(*) FROM nightingale.patient_payment_reports"
            )
            self.assertEqual(count, 0)

    async def test_out_of_scope_charge_or_invalid_link_is_absent(self):
        async with self.sessions() as db:
            foreign = await submit_report(
                db, self.secret, submit_payload(chargeId=str(OTHER_CHARGE_ID)), PNG
            )
            self.assertIsInstance(foreign.error, ReportNotFound)

            bad_link = await submit_report(db, "f" * 64, submit_payload(), PNG)
            self.assertIsInstance(bad_link.error, GrantNotUsable)

    async def test_resubmission_requires_a_rejected_previous_report(self):
        async with self.sessions() as db:
            bad = await submit_report(
                db, self.secret, submit_payload(previousReportId=str(uuid7())), PNG
            )
            self.assertIsInstance(bad.error, ReportRejected)

            first = submit_payload()
            await submit_report(db, self.secret, first, PNG)
            pending_chain = await submit_report(
                db, self.secret,
                submit_payload(previousReportId=str(first.operation_id)), PNG,
            )
            self.assertIsInstance(pending_chain.error, ReportRejected)

            await self.admin.execute(f"""
                INSERT INTO nightingale.billing_reviews
                    (id,report_id,account_id,reviewer_id,decision,reason)
                VALUES ('{uuid7()}','{first.operation_id}','{ACCOUNT_ID}','{USER_ID}',
                        'rejected','captura ilegible ficticia');
                UPDATE nightingale.patient_payment_reports SET status='rejected', version=2
                WHERE id='{first.operation_id}';
            """)
            chained = await submit_report(
                db, self.secret,
                submit_payload(previousReportId=str(first.operation_id)), PNG,
            )
            self.assertIsInstance(chained, Ok)
            self.assertEqual(chained.value.previous_report_id, first.operation_id)

    async def test_own_lists_and_result_never_expose_internal_notes(self):
        async with self.sessions() as db:
            data = submit_payload()
            await submit_report(db, self.secret, data, PNG)
            listed = await list_own_reports(db, self.secret)
            self.assertEqual(listed.value["total"], 1)

            await self.admin.execute(f"""
                INSERT INTO nightingale.billing_reviews
                    (id,report_id,account_id,reviewer_id,decision,verified_paid_on,
                     verified_amount,verified_currency,internal_note)
                VALUES ('{uuid7()}','{data.operation_id}','{ACCOUNT_ID}','{USER_ID}',
                        'approved','2026-11-26',40.00,'USD','nota interna secreta');
                UPDATE nightingale.patient_payment_reports SET status='approved', version=2
                WHERE id='{data.operation_id}';
                INSERT INTO nightingale.patient_payments
                    (id,account_id,charge_id,patient_id,origin,origin_report_id,amount,
                     currency,paid_on,method,registered_by)
                VALUES ('{uuid7()}','{ACCOUNT_ID}','{CHARGE_ID}','{PATIENT_ID}',
                        'patient_report','{data.operation_id}',40.00,'USD','2026-11-26',
                        'transferencia ficticia','{USER_ID}');
            """)
            detail = await read_own_report(db, self.secret, data.operation_id)
            self.assertEqual(detail.value.status, "approved")
            self.assertEqual(detail.value.result.payment_amount, 40)
            self.assertNotIn("nota interna", detail.value.model_dump_json())

            foreign = await read_own_report(db, self.secret, uuid7())
            self.assertIsInstance(foreign.error, ReportNotFound)


if __name__ == "__main__":
    unittest.main()
