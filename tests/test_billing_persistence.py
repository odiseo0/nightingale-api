import asyncio
import runpy
import unittest
from datetime import date
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = "019c0000-0000-7000-8000-0000000000a1"
ACCOUNT_ID = "019c0000-0000-7000-8000-0000000000a2"
OTHER_ACCOUNT_ID = "019c0000-0000-7000-8000-0000000000a3"
PROFESSIONAL_ID = "019c0000-0000-7000-8000-0000000000b1"
PATIENT_ID = "019c0000-0000-7000-8000-0000000000c1"
OTHER_PATIENT_ID = "019c0000-0000-7000-8000-0000000000c2"
SERVICE_ID = "019c0000-0000-7000-8000-0000000000d1"
APPOINTMENT_ID = "019c0000-0000-7000-8000-0000000000e1"
CHARGE_ID = "019c0000-0000-7000-8000-0000000000f1"
GRANT_ID = "019c0000-0000-7000-8000-0000000000f2"
REPORT_ID = "019c0000-0000-7000-8000-0000000000f3"
REVIEW_ID = "019c0000-0000-7000-8000-0000000000f4"
PAYMENT_ID = "019c0000-0000-7000-8000-0000000000f5"
RATE_ID = "019c0000-0000-7000-8000-0000000000f0"


class BillingPersistenceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # One random database for the whole class; the probe helper fixes its
        # name at load time, so per-test creation would collide.
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
        self.app = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_app",
            password=support["APP_PASSWORD"], database=support["DATABASE"], timeout=10,
        )
        await self.admin.execute("""
            TRUNCATE nightingale.payment_receipts, nightingale.patient_payments,
                     nightingale.billing_reviews, nightingale.patient_payment_evidence,
                     nightingale.patient_payment_reports, nightingale.patient_billing_grants,
                     nightingale.billing_exchange_rates,
                     nightingale.charge_histories, nightingale.patient_charges,
                     nightingale.service_offer_prices, nightingale.service_prices,
                     nightingale.appointment_histories, nightingale.appointments,
                     nightingale.professional_services, nightingale.services,
                     nightingale.account_patients, nightingale.patients,
                     nightingale.account_professionals, nightingale.professionals,
                     nightingale.accounts, nightingale.app_users CASCADE;
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','billing-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES
                ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                 'Fixture','Fixture','VE','Fixture','Fixture'),
                ('{OTHER_ACCOUNT_ID}','clinic','{USER_ID}','Otra','America/Caracas',
                 'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}'),('{OTHER_ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0),('{OTHER_ACCOUNT_ID}',0);
            INSERT INTO nightingale.professionals (id,user_id,public_name)
            VALUES ('{PROFESSIONAL_ID}','{USER_ID}','Profesional ficticio');
            INSERT INTO nightingale.account_professionals (account_id,professional_id,user_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{USER_ID}');
            INSERT INTO nightingale.patients (id) VALUES ('{PATIENT_ID}'),('{OTHER_PATIENT_ID}');
            INSERT INTO nightingale.account_patients
                (account_id,patient_id,full_name)
            VALUES
                ('{ACCOUNT_ID}','{PATIENT_ID}','Paciente ficticio'),
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
        """)

    async def asyncTearDown(self):
        await self.app.close()
        await self.admin.close()

    async def insert_charge(self, charge_id=CHARGE_ID, account_id=ACCOUNT_ID,
                            patient_id=PATIENT_ID, appointment="NULL", status="draft",
                            extra=""):
        await self.app.execute(f"""
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,appointment_id,description,amount,currency,
                 price_source,status,created_by{extra and ',' + extra[0]})
            VALUES ('{charge_id}','{account_id}','{patient_id}',{appointment},
                    'Consulta ficticia',18.00,'USD','base','{status}','{USER_ID}'
                    {extra and ',' + extra[1]})
        """)

    async def test_runtime_role_writes_through_grants_but_never_deletes_history(self):
        await self.app.execute(f"""
            INSERT INTO nightingale.service_prices (professional_id,service_id,amount,currency)
            VALUES ('{PROFESSIONAL_ID}','{SERVICE_ID}',18.00,'USD')
        """)
        await self.app.execute(f"""
            INSERT INTO nightingale.service_offer_prices
                (account_id,professional_id,service_id,amount,currency)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}',15.00,'USD')
        """)
        # Removing the offer override is allowed; it returns resolution to base (D25).
        await self.app.execute("DELETE FROM nightingale.service_offer_prices")
        await self.insert_charge()
        for statement in (
            "DELETE FROM nightingale.patient_charges",
            "DELETE FROM nightingale.charge_histories",
            "DROP TABLE nightingale.patient_charges",
        ):
            with self.assertRaises(asyncpg.InsufficientPrivilegeError, msg=statement):
                await self.app.execute(statement)

    async def test_prices_admit_zero_and_reject_negative_or_foreign_currency(self):
        insert = """
            INSERT INTO nightingale.service_prices (professional_id,service_id,amount,currency)
            VALUES ($1,$2,$3,$4)
        """
        # Zero is a valid free price (D25); absence of the row means «no price».
        await self.app.execute(insert, PROFESSIONAL_ID, SERVICE_ID, 0, "USD")
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(insert, PROFESSIONAL_ID, SERVICE_ID, -1, "USD")
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(
                insert, PROFESSIONAL_ID, "019c0000-0000-7000-8000-0000000000d2", 1, "EUR"
            )
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(insert, PROFESSIONAL_ID, SERVICE_ID, 20, "USD")
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            await self.app.execute(
                insert, PROFESSIONAL_ID, "019c0000-0000-7000-8000-0000000000d3", 1, "USD"
            )

    async def test_offer_price_requires_the_offer_row(self):
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            await self.app.execute(f"""
                INSERT INTO nightingale.service_offer_prices
                    (account_id,professional_id,service_id,amount,currency)
                VALUES ('{OTHER_ACCOUNT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}',15.00,'USD')
            """)

    async def test_charge_links_never_cross_account_or_patient(self):
        # PATIENT belongs to ACCOUNT_ID only; a charge in another account cannot claim it.
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            await self.insert_charge(
                "019c0000-0000-7000-8000-0000000000f2", account_id=OTHER_ACCOUNT_ID
            )
        # The appointment belongs to PATIENT_ID; another patient cannot reuse it.
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            await self.insert_charge(
                "019c0000-0000-7000-8000-0000000000f3",
                patient_id=OTHER_PATIENT_ID, appointment=f"'{APPOINTMENT_ID}'",
            )
        await self.insert_charge(appointment=f"'{APPOINTMENT_ID}'")

    async def test_charge_status_coherence_is_enforced(self):
        with self.assertRaises(asyncpg.CheckViolationError):
            # Issued without issued_at.
            await self.insert_charge("019c0000-0000-7000-8000-0000000000f4", status="issued")
        with self.assertRaises(asyncpg.CheckViolationError):
            # Cancelled without reason.
            await self.insert_charge(
                "019c0000-0000-7000-8000-0000000000f5", status="cancelled",
                extra=("issued_at,cancelled_at", "'2026-11-27T15:00:00Z','2026-11-27T16:00:00Z'"),
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.insert_charge(
                "019c0000-0000-7000-8000-0000000000f6",
                extra=("issued_at", "'2026-11-27T15:00:00Z'"),
            )

    async def test_catalog_change_never_rewrites_an_issued_charge(self):
        await self.app.execute(f"""
            INSERT INTO nightingale.service_prices (professional_id,service_id,amount,currency)
            VALUES ('{PROFESSIONAL_ID}','{SERVICE_ID}',18.00,'USD')
        """)
        await self.insert_charge(
            status="issued", extra=("issued_at", "'2026-11-27T15:00:00Z'")
        )
        await self.app.execute(f"""
            UPDATE nightingale.service_prices SET amount=20.00, version=version+1,
                updated_at=CURRENT_TIMESTAMP
            WHERE professional_id='{PROFESSIONAL_ID}' AND service_id='{SERVICE_ID}'
        """)
        amount = await self.app.fetchval(
            "SELECT amount FROM nightingale.patient_charges WHERE id=$1", CHARGE_ID
        )
        self.assertEqual(amount, 18)

    async def test_history_never_crosses_accounts_and_keeps_its_actions(self):
        await self.insert_charge()
        insert = """
            INSERT INTO nightingale.charge_histories
                (id,charge_id,account_id,action,charge_version,actor_id)
            VALUES ($1,$2,$3,$4,$5,$6)
        """
        await self.app.execute(
            insert, "019c0000-0000-7000-8000-0000000000f7", CHARGE_ID,
            ACCOUNT_ID, "created", 1, USER_ID,
        )
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000f8", CHARGE_ID,
                OTHER_ACCOUNT_ID, "created", 1, USER_ID,
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000f9", CHARGE_ID,
                ACCOUNT_ID, "deleted", 2, USER_ID,
            )

    async def issued_charge(self, charge_id=CHARGE_ID, amount="100.00"):
        await self.app.execute(f"""
            INSERT INTO nightingale.patient_charges
                (id,account_id,patient_id,description,amount,currency,price_source,
                 status,issued_at,created_by)
            VALUES ('{charge_id}','{ACCOUNT_ID}','{PATIENT_ID}','Consulta ficticia',
                    {amount},'USD','base','issued','2026-11-27T15:00:00Z','{USER_ID}')
        """)

    async def insert_grant(self, grant_id=GRANT_ID, charge_id=CHARGE_ID,
                           actions="ARRAY['read_charge','submit_report','read_result']",
                           token="a"):
        await self.app.execute(f"""
            INSERT INTO nightingale.patient_billing_grants
                (id,account_id,patient_id,charge_id,token_hash,actions,expires_at,created_by)
            VALUES ('{grant_id}','{ACCOUNT_ID}','{PATIENT_ID}','{charge_id}',
                    '{token * 64}',{actions},'2026-12-27T15:00:00Z','{USER_ID}')
        """)

    async def insert_report(self, report_id=REPORT_ID, charge_id=CHARGE_ID,
                            account_id=ACCOUNT_ID, grant_id=GRANT_ID,
                            previous="NULL", last4="'0071'"):
        await self.app.execute(f"""
            INSERT INTO nightingale.patient_payment_reports
                (id,account_id,charge_id,patient_id,grant_id,declared_paid_on,
                 declared_amount,declared_currency,declared_method,
                 declared_reference_last4,previous_report_id)
            VALUES ('{report_id}','{account_id}','{charge_id}','{PATIENT_ID}','{grant_id}',
                    '2026-11-26',40.00,'USD','transferencia ficticia',{last4},{previous})
        """)

    async def insert_review(self, review_id=REVIEW_ID, report_id=REPORT_ID,
                            decision="approved", verified="'2026-11-26',40.00,'USD'",
                            reason="NULL"):
        await self.app.execute(f"""
            INSERT INTO nightingale.billing_reviews
                (id,report_id,account_id,reviewer_id,decision,verified_paid_on,
                 verified_amount,verified_currency,reason)
            VALUES ('{review_id}','{report_id}','{ACCOUNT_ID}','{USER_ID}','{decision}',
                    {verified},{reason})
        """)

    async def insert_payment(self, payment_id=PAYMENT_ID, charge_id=CHARGE_ID,
                             origin="patient_report", origin_report=f"'{REPORT_ID}'",
                             amount="40.00", extra="", extra_values=""):
        await self.app.execute(f"""
            INSERT INTO nightingale.patient_payments
                (id,account_id,charge_id,patient_id,origin,origin_report_id,amount,
                 currency,paid_on,method,registered_by{extra})
            VALUES ('{payment_id}','{ACCOUNT_ID}','{charge_id}','{PATIENT_ID}','{origin}',
                    {origin_report},{amount},'USD','2026-11-26','transferencia ficticia',
                    '{USER_ID}'{extra_values})
        """)

    async def approved_report_chain(self):
        await self.issued_charge()
        await self.insert_grant()
        await self.insert_report()
        await self.insert_review()

    async def test_rates_are_unique_per_account_date_and_selectable(self):
        insert = """
            INSERT INTO nightingale.billing_exchange_rates
                (id,account_id,rate_date,rate_ves_per_usd,source,registered_by)
            VALUES ($1,$2,$3,$4,'bcv-ficticio',$5)
        """
        await self.app.execute(insert, RATE_ID, ACCOUNT_ID, date(2026, 11, 20), 400.25, USER_ID)
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(
                insert, "019c0000-0000-7000-8000-0000000000f6", ACCOUNT_ID,
                date(2026, 11, 20), 401.00, USER_ID,
            )
        # Another account keeps its own configuration and history (D25).
        await self.app.execute(
            insert, "019c0000-0000-7000-8000-0000000000f7", OTHER_ACCOUNT_ID,
            date(2026, 11, 20), 399.00, USER_ID,
        )

    async def test_grants_need_hash_object_and_closed_actions(self):
        await self.issued_charge()
        await self.insert_grant()
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.insert_grant("019c0000-0000-7000-8000-0000000000f8", token="not-hex-")
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.insert_grant(
                "019c0000-0000-7000-8000-0000000000f9",
                actions="ARRAY['approve_payment']", token="b",
            )
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(f"""
                INSERT INTO nightingale.patient_billing_grants
                    (id,account_id,patient_id,token_hash,actions,expires_at,created_by)
                VALUES ('019c0000-0000-7000-8000-0000000000fa','{ACCOUNT_ID}','{PATIENT_ID}',
                        '{"c" * 64}',ARRAY['read_charge'],'2026-12-27T15:00:00Z','{USER_ID}')
            """)
        # Revocation is an UPDATE; the row and its history remain.
        await self.app.execute(
            f"UPDATE nightingale.patient_billing_grants "
            f"SET revoked_at='2026-11-28T15:00:00Z' WHERE id='{GRANT_ID}'"
        )

    async def test_reports_never_cross_accounts_and_chain_after_rejection(self):
        await self.issued_charge()
        await self.insert_grant()
        await self.insert_report()
        with self.assertRaises(asyncpg.ForeignKeyViolationError):
            # The charge belongs to ACCOUNT_ID; the report cannot claim another account.
            await self.insert_report("019c0000-0000-7000-8000-0000000000fb",
                                     account_id=OTHER_ACCOUNT_ID)
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.insert_report("019c0000-0000-7000-8000-0000000000fc", last4="'071'")
        # Rejection keeps the original; the new presentation links to it (§10.4).
        await self.insert_review(decision="rejected", verified="NULL,NULL,NULL",
                                 reason="'captura ilegible ficticia'")
        await self.app.execute(
            f"UPDATE nightingale.patient_payment_reports SET status='rejected', version=2 "
            f"WHERE id='{REPORT_ID}'"
        )
        await self.insert_report("019c0000-0000-7000-8000-0000000000fd",
                                 previous=f"'{REPORT_ID}'")

    async def test_evidence_is_single_and_validated_per_report(self):
        await self.issued_charge()
        await self.insert_grant()
        await self.insert_report()
        insert = """
            INSERT INTO nightingale.patient_payment_evidence
                (id,report_id,storage_key,content_type,size_bytes,sha256)
            VALUES ($1,$2,$3,$4,$5,$6)
        """
        await self.app.execute(insert, "019c0000-0000-7000-8000-0000000000fe", REPORT_ID,
                               "billing-evidence/fixture-1", "image/png", 1024, "a" * 64)
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(insert, "019c0000-0000-7000-8000-0000000000ff", REPORT_ID,
                                   "billing-evidence/fixture-2", "image/png", 1024, "b" * 64)
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(insert, "019c0000-0000-7000-8000-000000000100",
                                   "019c0000-0000-7000-8000-0000000000fd", "k", "image/gif",
                                   1024, "c" * 64)

    async def test_one_decision_and_one_payment_per_report(self):
        await self.approved_report_chain()
        with self.assertRaises(asyncpg.UniqueViolationError):
            # The same report cannot be decided twice (two reviewers lose here).
            await self.insert_review("019c0000-0000-7000-8000-000000000101")
        with self.assertRaises(asyncpg.CheckViolationError):
            # Approved without verified data.
            await self.insert_review("019c0000-0000-7000-8000-000000000102",
                                     report_id="019c0000-0000-7000-8000-0000000000fd",
                                     verified="NULL,NULL,NULL")
        await self.insert_payment()
        with self.assertRaises(asyncpg.UniqueViolationError):
            # One approval produces at most one ordinary payment (§13.1).
            await self.insert_payment("019c0000-0000-7000-8000-000000000103")

    async def test_payment_coherence_conversion_origin_and_annulment(self):
        await self.approved_report_chain()
        with self.assertRaises(asyncpg.CheckViolationError):
            # staff_entry never carries an origin report (D26).
            await self.insert_payment("019c0000-0000-7000-8000-000000000104",
                                      origin="staff_entry")
        with self.assertRaises(asyncpg.CheckViolationError):
            # A partial conversion snapshot is rejected; it is all or nothing (D25).
            await self.insert_payment("019c0000-0000-7000-8000-000000000105",
                                      extra=",exchange_rate", extra_values=",400.25")
        with self.assertRaises(asyncpg.CheckViolationError):
            # Annulled without actor/reason.
            await self.insert_payment("019c0000-0000-7000-8000-000000000106",
                                      origin="staff_entry", origin_report="NULL",
                                      extra=",status", extra_values=",'annulled'")
        await self.insert_payment()
        await self.app.execute(f"""
            UPDATE nightingale.patient_payments
            SET status='annulled', annulled_at='2026-11-28T15:00:00Z',
                annulled_by='{USER_ID}', annulment_reason='duplicado ficticio', version=2
            WHERE id='{PAYMENT_ID}'
        """)
        active = await self.app.fetchval(
            "SELECT count(*) FROM nightingale.patient_payments "
            f"WHERE charge_id='{CHARGE_ID}' AND status='active'"
        )
        self.assertEqual(active, 0)

    async def test_two_reviewers_on_the_last_balance_serialize_on_the_charge(self):
        await self.approved_report_chain()
        first = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_app",
            password=support["APP_PASSWORD"], database=support["DATABASE"], timeout=10,
        )
        second = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_app",
            password=support["APP_PASSWORD"], database=support["DATABASE"], timeout=10,
        )
        try:
            tx_first = first.transaction()
            await tx_first.start()
            # Both approvals coordinate on the charge row lock (§19.6): the second
            # waits and, after the first commits 60.00, sees the remaining balance.
            await first.fetchrow(
                "SELECT id FROM nightingale.patient_charges "
                f"WHERE id='{CHARGE_ID}' FOR UPDATE"
            )
            await first.execute(f"""
                INSERT INTO nightingale.patient_payments
                    (id,account_id,charge_id,patient_id,origin,origin_report_id,amount,
                     currency,paid_on,method,registered_by)
                VALUES ('019c0000-0000-7000-8000-000000000107','{ACCOUNT_ID}','{CHARGE_ID}',
                        '{PATIENT_ID}','patient_report','{REPORT_ID}',60.00,'USD',
                        '2026-11-26','transferencia ficticia','{USER_ID}')
            """)

            async def contender():
                tx = second.transaction()
                await tx.start()
                try:
                    await second.fetchrow(
                        "SELECT id FROM nightingale.patient_charges "
                        f"WHERE id='{CHARGE_ID}' FOR UPDATE"
                    )
                    paid = await second.fetchval(
                        "SELECT coalesce(sum(amount),0) FROM nightingale.patient_payments "
                        f"WHERE charge_id='{CHARGE_ID}' AND status='active'"
                    )
                    return paid
                finally:
                    await tx.rollback()

            task = asyncio.create_task(contender())
            await asyncio.sleep(0.2)
            self.assertFalse(task.done())
            await tx_first.commit()
            paid_seen = await asyncio.wait_for(task, timeout=5)
            # After the wait the contender sees 60.00 of 100.00: a 50.00 approval
            # would exceed the balance and must be rejected by the use case (D26).
            self.assertEqual(paid_seen, 60)
        finally:
            await first.close()
            await second.close()

    async def test_receipts_are_single_pdf_per_payment(self):
        await self.approved_report_chain()
        await self.insert_payment()
        insert = """
            INSERT INTO nightingale.payment_receipts
                (id,account_id,payment_id,storage_key,size_bytes,sha256)
            VALUES ($1,$2,$3,$4,$5,$6)
        """
        await self.app.execute(insert, "019c0000-0000-7000-8000-000000000108", ACCOUNT_ID,
                               PAYMENT_ID, "billing-receipts/fixture-1", 2048, "d" * 64)
        with self.assertRaises(asyncpg.UniqueViolationError):
            await self.app.execute(insert, "019c0000-0000-7000-8000-000000000109", ACCOUNT_ID,
                                   PAYMENT_ID, "billing-receipts/fixture-2", 2048, "e" * 64)
        with self.assertRaises(asyncpg.CheckViolationError):
            await self.app.execute(f"""
                INSERT INTO nightingale.payment_receipts
                    (id,account_id,payment_id,storage_key,content_type,size_bytes,sha256)
                VALUES ('019c0000-0000-7000-8000-00000000010a','{ACCOUNT_ID}','{PAYMENT_ID}',
                        'billing-receipts/fixture-3','image/png',2048,'{'f' * 64}')
            """)

    async def test_downgrade_and_reapply(self):
        result = support["migrate"]("downgrade", "20261127_02")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        for table in ("patient_payments", "billing_reviews", "patient_payment_reports",
                      "patient_billing_grants", "billing_exchange_rates", "payment_receipts",
                      "patient_payment_evidence"):
            exists = await self.admin.fetchval(
                f"SELECT to_regclass('nightingale.{table}') IS NOT NULL"
            )
            self.assertFalse(exists, table)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.patient_charges') IS NOT NULL"
        )
        self.assertTrue(exists)
        result = support["migrate"]("downgrade", "20261127_01")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.patient_charges') IS NOT NULL"
        )
        self.assertFalse(exists)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.service_prices') IS NOT NULL"
        )
        self.assertFalse(exists)
        result = support["migrate"]("upgrade", "head")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        exists = await self.admin.fetchval(
            "SELECT to_regclass('nightingale.charge_histories') IS NOT NULL"
        )
        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
