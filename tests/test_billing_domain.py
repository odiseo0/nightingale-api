import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from src.api.billing.domain.charges import (
    Charge,
    ChargeHasActivePaymentsError,
    ChargeNotDraftError,
    cancel,
    issue,
    update_draft,
    visible_to_patient,
)
from src.api.billing.domain.money import BcvRate, Money
from src.api.billing.domain.payments import (
    CurrencyMismatchError,
    DeclaredPayment,
    GrantObjectRequiredError,
    PatientBillingGrant,
    PatientPaymentReport,
    ReportNotPendingError,
    VerifiedPayment,
    annul,
    convert_verified,
    decide,
    ensure_grant_object,
    new_payment,
    resubmission,
)

NOW = datetime(2026, 11, 27, 15, 0, tzinfo=timezone.utc)


def draft(amount: str = "18.00", source: str = "base") -> Charge:
    return Charge(
        charge_id=uuid4(),
        account_id=uuid4(),
        patient_id=uuid4(),
        description="Consulta ficticia",
        amount=Money(amount=Decimal(amount), currency="USD"),
        price_source=source,
        created_by=uuid4(),
    )


def declared(amount: str = "18.00", currency: str = "USD") -> DeclaredPayment:
    return DeclaredPayment(
        paid_on=date(2026, 11, 26),
        amount=Decimal(amount),
        currency=currency,
        method="transferencia ficticia",
    )


def report(decl: DeclaredPayment | None = None) -> PatientPaymentReport:
    return PatientPaymentReport(
        report_id=uuid4(),
        account_id=uuid4(),
        charge_id=uuid4(),
        patient_id=uuid4(),
        grant_id=uuid4(),
        declared=decl or declared(),
    )


def rate(value: str = "400.25") -> BcvRate:
    return BcvRate(rate_ves_per_usd=Decimal(value), rate_date=date(2026, 11, 26), source="bcv-ficticio")


class ChargeTransitionTests(unittest.TestCase):
    def test_draft_issue_cancel_happy_path(self):
        charge = draft()
        self.assertFalse(visible_to_patient(charge))
        issued = issue(charge, NOW)
        self.assertEqual((issued.status, issued.version), ("issued", 2))
        self.assertTrue(visible_to_patient(issued))
        cancelled = cancel(issued, NOW, "cobro duplicado ficticio", has_active_payments=False)
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(cancelled.cancellation_reason, "cobro duplicado ficticio")

    def test_issued_charge_is_not_editable(self):
        issued = issue(draft(), NOW)
        with self.assertRaises(ChargeNotDraftError):
            update_draft(issued, description="otra")
        with self.assertRaises(ChargeNotDraftError):
            issue(issued, NOW)

    def test_manual_adjustment_requires_reason_and_marks_source(self):
        with self.assertRaises(ValueError):
            update_draft(draft(), amount=Money(amount=Decimal("15.00"), currency="USD"))
        adjusted = update_draft(
            draft(),
            amount=Money(amount=Decimal("15.00"), currency="USD"),
            adjust_reason="descuento autorizado ficticio",
        )
        self.assertEqual(adjusted.price_source, "manual")
        self.assertEqual(adjusted.amount.amount, Decimal("15.00"))

    def test_cancel_with_active_payments_is_rejected(self):
        with self.assertRaises(ChargeHasActivePaymentsError):
            cancel(issue(draft(), NOW), NOW, "error", has_active_payments=True)

    def test_naive_instants_are_rejected(self):
        with self.assertRaises(ValueError):
            issue(draft(), datetime(2026, 11, 27))


class ReportTests(unittest.TestCase):
    def test_submission_starts_pending_and_decision_is_unique(self):
        pending = report()
        self.assertEqual(pending.status, "pending")
        approved = decide(pending, "approved")
        self.assertEqual(approved.status, "approved")
        with self.assertRaises(ReportNotPendingError):
            decide(approved, "rejected")

    def test_resubmission_chains_history_and_needs_a_decided_report(self):
        with self.assertRaises(ReportNotPendingError):
            resubmission(report(), uuid4(), declared())
        rejected = decide(report(), "rejected")
        again = resubmission(rejected, uuid4(), declared("18.00"))
        self.assertEqual(again.previous_report_id, rejected.report_id)
        self.assertEqual(again.status, "pending")

    def test_declared_requires_two_places_and_partial_reference(self):
        with self.assertRaises(ValidationError):
            declared("18.001")
        with self.assertRaises(ValidationError):
            DeclaredPayment(
                paid_on=date(2026, 11, 26), amount=Decimal("1.00"),
                currency="USD", method="x", reference_last4="12345",
            )


class PaymentTests(unittest.TestCase):
    def verified(self, amount: str, currency: str) -> VerifiedPayment:
        return VerifiedPayment(
            paid_on=date(2026, 11, 26), amount=Decimal(amount),
            currency=currency, method="transferencia ficticia",
        )

    def test_same_currency_needs_no_rate(self):
        payment = new_payment(
            uuid4(), report(), uuid4(), uuid4(), uuid4(),
            self.verified("18.00", "USD"), "USD", None, uuid4(),
        )
        self.assertEqual((payment.amount, payment.origin, payment.conversion), (Decimal("18.00"), "patient_report", None))

    def test_ves_payment_on_usd_charge_freezes_the_conversion(self):
        payment = new_payment(
            uuid4(), report(declared("40025.00", "VES")), uuid4(), uuid4(), uuid4(),
            self.verified("40025.00", "VES"), "USD", rate(), uuid4(),
        )
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.currency, "USD")
        self.assertEqual(payment.conversion.exchange_rate, Decimal("400.25"))

    def test_conversion_requires_the_rate(self):
        with self.assertRaises(CurrencyMismatchError):
            convert_verified(self.verified("40025.00", "VES"), "USD", None)

    def test_staff_entry_has_no_origin_report(self):
        payment = new_payment(
            uuid4(), None, uuid4(), uuid4(), uuid4(),
            self.verified("25.00", "USD"), "USD", None, uuid4(),
        )
        self.assertEqual((payment.origin, payment.origin_report_id), ("staff_entry", None))

    def test_annulment_keeps_history_and_never_claims_refund(self):
        payment = new_payment(
            uuid4(), report(), uuid4(), uuid4(), uuid4(),
            self.verified("18.00", "USD"), "USD", None, uuid4(),
        )
        actor = uuid4()
        annulled = annul(payment, NOW, actor, "duplicado ficticio")
        self.assertEqual((annulled.status, annulled.annulled_by), ("annulled", actor))
        self.assertEqual(payment.status, "active")
        with self.assertRaises(ValueError):
            annul(annulled, NOW, actor, "otra vez")


class GrantTests(unittest.TestCase):
    def grant(self, **kwargs) -> PatientBillingGrant:
        base = dict(
            grant_id=uuid4(), account_id=uuid4(), patient_id=uuid4(),
            appointment_id=uuid4(), actions=["read_charge", "submit_report"],
            expires_at=NOW + timedelta(days=30),
        )
        base.update(kwargs)
        return PatientBillingGrant(**base)

    def test_validity_window_revocation_and_actions(self):
        grant = self.grant()
        self.assertTrue(grant.usable("read_charge", NOW))
        self.assertFalse(grant.usable("read_receipt", NOW))
        self.assertFalse(grant.usable("read_charge", NOW + timedelta(days=31)))
        revoked = grant.model_copy(update={"revoked_at": NOW})
        self.assertFalse(revoked.usable("read_charge", NOW))

    def test_grant_requires_a_concrete_object(self):
        ensure_grant_object(self.grant())
        loose = self.grant(appointment_id=None)
        with self.assertRaises(GrantObjectRequiredError):
            ensure_grant_object(loose)


if __name__ == "__main__":
    unittest.main()
