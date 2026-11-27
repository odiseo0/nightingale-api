import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from src.api.subscriptions.domain.money import BcvRate, Money
from src.api.subscriptions.domain.reports import (
    DeclaredPayment,
    EvidenceMetadata,
    PaymentReport,
    ReportNotPendingError,
    decide,
    resubmission,
)
from src.api.subscriptions.domain.reviews import (
    PaymentMismatchError,
    SubscriptionReview,
    VerifiedPayment,
    apply_review,
    ensure_full_payment,
)


def declared(**overrides) -> DeclaredPayment:
    values = {
        "paid_on": date(2026, 11, 20),
        "amount": Money(amount=Decimal("18.00"), currency="USD"),
        "method": "transferencia ficticia",
    }
    values.update(overrides)
    return DeclaredPayment(**values)


def report(**overrides) -> PaymentReport:
    values = {
        "report_id": uuid4(),
        "account_id": uuid4(),
        "plan_code": "independent",
        "periodicity": "days_30",
        "declared": declared(),
    }
    values.update(overrides)
    return PaymentReport(**values)


def rate(value: str = "400.25") -> BcvRate:
    return BcvRate(rate_ves_per_usd=Decimal(value), rate_date=date(2026, 11, 20), source="bcv-ficticio")


class ReportTests(unittest.TestCase):
    def test_submission_starts_pending_and_changes_nothing(self):
        created = report()
        self.assertEqual(created.status, "pending")
        self.assertEqual(created.version, 1)
        self.assertIsNone(created.previous_report_id)

    def test_reference_last4_keeps_leading_zeros_and_is_not_unique(self):
        first = report(declared=declared(reference_last4="0071"))
        second = report(declared=declared(reference_last4="0071"))
        self.assertEqual(first.declared.reference_last4, "0071")
        self.assertNotEqual(first.report_id, second.report_id)
        for invalid in ("71", "00712", "00a1"):
            with self.assertRaises(ValidationError, msg=invalid):
                declared(reference_last4=invalid)

    def test_evidence_limits_follow_d24(self):
        EvidenceMetadata(content_type="image/png", size_bytes=5 * 1024 * 1024, sha256="a" * 64)
        for invalid in (
            {"content_type": "image/gif", "size_bytes": 100, "sha256": "a" * 64},
            {"content_type": "image/png", "size_bytes": 5 * 1024 * 1024 + 1, "sha256": "a" * 64},
            {"content_type": "image/png", "size_bytes": 0, "sha256": "a" * 64},
            {"content_type": "image/png", "size_bytes": 100, "sha256": "xyz"},
        ):
            with self.assertRaises(ValidationError, msg=str(invalid)):
                EvidenceMetadata(**invalid)

    def test_decided_reports_are_never_reopened(self):
        approved = decide(report(), "approved")
        self.assertEqual(approved.status, "approved")
        with self.assertRaises(ReportNotPendingError):
            decide(approved, "rejected")

    def test_resubmission_links_history_and_returns_to_pending(self):
        rejected = decide(report(), "rejected")
        new_id = uuid4()
        again = resubmission(rejected, new_id)
        self.assertEqual(again.status, "pending")
        self.assertEqual(again.previous_report_id, rejected.report_id)
        self.assertEqual(again.account_id, rejected.account_id)
        self.assertEqual(rejected.status, "rejected")
        with self.assertRaises(ReportNotPendingError):
            resubmission(report(), uuid4())


class ReviewTests(unittest.TestCase):
    def test_approval_requires_verified_data_and_rate_for_ves(self):
        with self.assertRaises(ValidationError):
            SubscriptionReview(report_id=uuid4(), operator_id=uuid4(), decision="approved")
        with self.assertRaises(ValidationError):
            SubscriptionReview(
                report_id=uuid4(),
                operator_id=uuid4(),
                decision="approved",
                verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("7204.50"), currency="VES"),
            )
        review = SubscriptionReview(
            report_id=uuid4(),
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("7204.50"), currency="VES"),
            bcv_rate=rate(),
        )
        self.assertEqual(review.decision, "approved")

    def test_rejection_requires_a_reason(self):
        with self.assertRaises(ValidationError):
            SubscriptionReview(report_id=uuid4(), operator_id=uuid4(), decision="rejected")
        review = SubscriptionReview(
            report_id=uuid4(), operator_id=uuid4(), decision="rejected", reason="referencia no verificable"
        )
        self.assertEqual(review.reason, "referencia no verificable")

    def test_apply_review_decides_once_and_checks_ownership(self):
        target = report()
        review = SubscriptionReview(
            report_id=target.report_id,
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("18.00"), currency="USD"),
        )
        decided = apply_review(target, review)
        self.assertEqual(decided.status, "approved")
        with self.assertRaises(ReportNotPendingError):
            apply_review(decided, review)
        with self.assertRaises(ValueError):
            apply_review(report(), review)

    def test_only_full_payment_approves(self):
        target = report()
        due = target.declared.amount

        exact = SubscriptionReview(
            report_id=target.report_id,
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("18.00"), currency="USD"),
        )
        ensure_full_payment(exact, due)

        # VES verified against the USD due amount uses the applied rate: 18 x 400.25 = 7204.50.
        ves_exact = SubscriptionReview(
            report_id=target.report_id,
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("7204.50"), currency="VES"),
            bcv_rate=rate(),
        )
        ensure_full_payment(ves_exact, due)

        insufficient = SubscriptionReview(
            report_id=target.report_id,
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("17.99"), currency="USD"),
        )
        with self.assertRaises(PaymentMismatchError):
            ensure_full_payment(insufficient, due)

        # An excess is also rejected: partial and over payments follow the rejection path (D24).
        excess = SubscriptionReview(
            report_id=target.report_id,
            operator_id=uuid4(),
            decision="approved",
            verified=VerifiedPayment(paid_on=date(2026, 11, 20), amount=Decimal("7205.00"), currency="VES"),
            bcv_rate=rate(),
        )
        with self.assertRaises(PaymentMismatchError):
            ensure_full_payment(excess, due)


if __name__ == "__main__":
    unittest.main()


import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.report_cases import (
    IdempotencyConflict,
    PlanUnavailable,
    report_detail,
    store_report,
)
from src.api.subscriptions.domain.reports import PaymentReportCreateRequest
from src.core import Err, Ok

SUPPORT = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "test-support/persistence/check.py")
)

F_USER = "019c4000-0000-7000-8000-000000000001"
F_ACCOUNT = "019c4000-0000-7000-8000-000000000010"
F_PLAN = "019c4000-0000-7000-8000-000000000020"
F_VERSION = "019c4000-0000-7000-8000-000000000021"

F_SEED = f"""
    INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
    VALUES ('{F_USER}','fixture','report-owner','Fixture');
    INSERT INTO nightingale.accounts
        (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
         location_country,location_state,location_city)
    VALUES ('{F_ACCOUNT}','clinic','{F_USER}','Fixture','America/Caracas',
            'Fixture','Fixture','VE','Fixture','Fixture');
    INSERT INTO nightingale.account_memberships (account_id,user_id)
    VALUES ('{F_ACCOUNT}','{F_USER}');
    INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
    VALUES ('{F_ACCOUNT}',0);
    INSERT INTO nightingale.subscription_plans (id,code,name,description)
    VALUES ('{F_PLAN}','independent','Fixture','Fixture');
    INSERT INTO nightingale.subscription_plan_versions
        (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd)
    VALUES ('{F_VERSION}','{F_PLAN}',1,2,18.00,100.00);
"""


def submission(operation_id=None, **overrides) -> PaymentReportCreateRequest:
    values = {
        "operation_id": operation_id or uuid7(),
        "plan_code": "independent",
        "periodicity": "days_30",
        "declared_paid_on": date(2026, 11, 20),
        "declared_amount": Money(amount=Decimal("18.00"), currency="USD"),
        "declared_method": "transferencia ficticia",
        "declared_reference_last4": "0071",
    }
    values.update(overrides)
    return PaymentReportCreateRequest(**values)


class ReportSubmissionTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._prepare())

    @classmethod
    async def _prepare(cls):
        await SUPPORT["prepare_database"]()
        result = SUPPORT["migrate"]("upgrade", "head")
        assert result.returncode == 0, result.stderr or result.stdout

    @classmethod
    def tearDownClass(cls):
        async def drop():
            admin = await SUPPORT["connect_admin"]()
            try:
                await admin.execute(
                    f'DROP DATABASE IF EXISTS "{SUPPORT["DATABASE"]}" WITH (FORCE)'
                )
            finally:
                await admin.close()

        asyncio.run(drop())

    async def asyncSetUp(self):
        url = SUPPORT["database_url"]("nightingale_app", SUPPORT["APP_PASSWORD"])
        self.engine = create_async_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=SUPPORT["DATABASE"], timeout=10,
        )
        await self.admin.execute(f"""
            TRUNCATE nightingale.subscription_periods, nightingale.subscription_reviews,
                     nightingale.payment_report_evidence, nightingale.payment_reports,
                     nightingale.bcv_exchange_rates, nightingale.platform_operator_credentials,
                     nightingale.platform_operators, nightingale.account_subscriptions,
                     nightingale.subscription_plan_versions, nightingale.subscription_plans,
                     nightingale.accounts, nightingale.app_users CASCADE;
            {F_SEED}
        """)

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    async def test_submission_stays_pending_and_creates_the_relation(self):
        payload = submission()
        async with self.sessions() as db:
            result = await store_report(db, UUID(F_ACCOUNT), F_USER, payload)
            self.assertIsInstance(result, Ok)
            self.assertEqual(result.value.status, "pending")
            self.assertEqual(result.value.declared.reference_last4, "0071")

        subscription = await self.admin.fetchrow(
            f"SELECT status FROM nightingale.account_subscriptions "
            f"WHERE account_id='{F_ACCOUNT}'"
        )
        self.assertEqual(subscription["status"], "pending_activation")
        periods = await self.admin.fetchval(
            "SELECT count(*) FROM nightingale.subscription_periods"
        )
        self.assertEqual(periods, 0)

    async def test_lost_response_recovers_the_same_report(self):
        operation_id = uuid7()
        async with self.sessions() as db:
            first = await store_report(db, UUID(F_ACCOUNT), F_USER, submission(operation_id))
        async with self.sessions() as db:
            again = await store_report(db, UUID(F_ACCOUNT), F_USER, submission(operation_id))

        self.assertEqual(first.value.report_id, again.value.report_id)
        count = await self.admin.fetchval(
            "SELECT count(*) FROM nightingale.payment_reports"
        )
        self.assertEqual(count, 1)

        async with self.sessions() as db:
            conflict = await store_report(
                db, F_ACCOUNT, F_USER,
                submission(operation_id, declared_method="otro método ficticio"),
            )
            self.assertIsInstance(conflict.error, IdempotencyConflict)

    async def test_retired_or_unknown_plan_is_unavailable(self):
        await self.admin.execute(
            f"UPDATE nightingale.subscription_plans SET status='retired' WHERE id='{F_PLAN}'"
        )
        async with self.sessions() as db:
            result = await store_report(db, UUID(F_ACCOUNT), F_USER, submission())
            self.assertIsInstance(result.error, PlanUnavailable)

    async def test_resubmission_links_the_rejected_original(self):
        operation_id = uuid7()
        async with self.sessions() as db:
            first = await store_report(db, UUID(F_ACCOUNT), F_USER, submission(operation_id))

        await self.admin.execute(f"""
            INSERT INTO nightingale.platform_operators
                (id,oidc_issuer,oidc_subject,display_name,actions)
            VALUES ('019c4000-0000-7000-8000-000000000050','fixture','op','op',ARRAY['review']);
            INSERT INTO nightingale.subscription_reviews
                (id,report_id,operator_id,decision,reason)
            VALUES ('019c4000-0000-7000-8000-000000000051','{operation_id}',
                    '019c4000-0000-7000-8000-000000000050','rejected','fixture');
            UPDATE nightingale.payment_reports SET status='rejected' WHERE id='{operation_id}';
        """)
        async with self.sessions() as db:
            again = await store_report(
                db, F_ACCOUNT, F_USER, submission(previous_report_id=operation_id)
            )
            self.assertIsInstance(again, Ok)
            self.assertEqual(again.value.previous_report_id, operation_id)
            self.assertEqual(again.value.status, "pending")

            original = await self.admin.fetchrow(
                f"SELECT status FROM nightingale.payment_reports WHERE id='{operation_id}'"
            )
            self.assertEqual(original["status"], "rejected")
