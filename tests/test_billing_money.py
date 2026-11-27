import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from src.api.billing.domain.money import (
    BcvRate,
    Money,
    charge_balance,
    usd_to_ves,
    ves_to_usd,
)
from src.api.billing.domain.pricing import resolve_price


def rate(value: str, day: date = date(2026, 11, 27)) -> BcvRate:
    return BcvRate(rate_ves_per_usd=Decimal(value), rate_date=day, source="bcv-ficticio")


class ConversionTests(unittest.TestCase):
    def test_usd_to_ves_matches_the_fictitious_examples(self):
        self.assertEqual(usd_to_ves(Decimal("18.00"), rate("400.25")), Decimal("7204.50"))
        self.assertEqual(usd_to_ves(Decimal("100.00"), rate("400.25")), Decimal("40025.00"))
        self.assertEqual(usd_to_ves(Decimal("15.00"), rate("123.456")), Decimal("1851.84"))

    def test_ves_to_usd_converts_before_applying_to_a_usd_charge(self):
        # Cargo USD 100.00 pagado en VES con tasa 400.25 (D25).
        self.assertEqual(ves_to_usd(Decimal("40025.00"), rate("400.25")), Decimal("100.00"))
        self.assertEqual(ves_to_usd(Decimal("1000.00"), rate("400.25")), Decimal("2.50"))

    def test_rounding_is_half_up_and_applied_once(self):
        # 2.675 would become 2.67 with binary floats; exact decimal gives 2.68.
        self.assertEqual(usd_to_ves(Decimal("1.00"), rate("2.675")), Decimal("2.68"))
        # 10.005 / 2 = 5.0025 -> 5.00 with half-up at two places.
        self.assertEqual(ves_to_usd(Decimal("10.01"), rate("2.000000")), Decimal("5.01"))

    def test_conversion_rejects_non_positive_or_non_finite_amounts(self):
        for invalid in (Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-3")):
            with self.assertRaises(ValueError, msg=str(invalid)):
                usd_to_ves(invalid, rate("400.25"))
            with self.assertRaises(ValueError, msg=str(invalid)):
                ves_to_usd(invalid, rate("400.25"))

    def test_rate_rejects_non_positive_or_overprecise_values(self):
        with self.assertRaises(ValidationError):
            rate("0")
        with self.assertRaises(ValidationError):
            rate("400.1234567")
        with self.assertRaises(ValidationError):
            BcvRate(rate_ves_per_usd=Decimal("NaN"), rate_date=date(2026, 11, 27), source="x")


class MoneyTests(unittest.TestCase):
    def test_zero_is_a_valid_free_price_and_null_is_absence(self):
        free = Money(amount=Decimal("0.00"), currency="USD")
        self.assertEqual(free.amount, Decimal("0.00"))
        self.assertIsNone(resolve_price(None, None))

    def test_money_rejects_negative_non_finite_or_ambiguous_amounts(self):
        for invalid in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValidationError, msg=invalid):
                Money(amount=Decimal(invalid), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("-0.01"), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("1.001"), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("1.00"), currency="EUR")


class PriceResolutionTests(unittest.TestCase):
    def test_offer_replaces_base(self):
        base = Money(amount=Decimal("18.00"), currency="USD")
        offer = Money(amount=Decimal("15.00"), currency="USD")
        resolved = resolve_price(offer, base)
        self.assertEqual((resolved.amount, resolved.source), (Decimal("15.00"), "offer"))

    def test_base_applies_without_offer(self):
        base = Money(amount=Decimal("18.00"), currency="USD")
        resolved = resolve_price(None, base)
        self.assertEqual((resolved.amount, resolved.source), (Decimal("18.00"), "base"))

    def test_free_offer_overrides_a_paid_base(self):
        base = Money(amount=Decimal("18.00"), currency="USD")
        offer = Money(amount=Decimal("0.00"), currency="USD")
        resolved = resolve_price(offer, base)
        self.assertEqual((resolved.amount, resolved.source), (Decimal("0.00"), "offer"))


class BalanceTests(unittest.TestCase):
    def test_two_partial_payments_reach_paid(self):
        first = charge_balance(Decimal("100.00"), [Decimal("40.00")])
        self.assertEqual((first.paid, first.outstanding, first.state), (Decimal("40.00"), Decimal("60.00"), "partially_paid"))
        second = charge_balance(Decimal("100.00"), [Decimal("40.00"), Decimal("60.00")])
        self.assertEqual((second.paid, second.outstanding, second.state), (Decimal("100.00"), Decimal("0.00"), "paid"))

    def test_no_payments_is_unpaid(self):
        balance = charge_balance(Decimal("100.00"), [])
        self.assertEqual(balance.state, "unpaid")
        self.assertEqual(balance.outstanding, Decimal("100.00"))

    def test_annulled_payments_are_excluded_by_the_caller(self):
        # Pago de 40.00 anulado: solo suma el vigente de 25.00 (§13.5).
        balance = charge_balance(Decimal("100.00"), [Decimal("25.00")])
        self.assertEqual(balance.outstanding, Decimal("75.00"))

    def test_excess_is_an_error_never_a_credit(self):
        with self.assertRaises(ValueError):
            charge_balance(Decimal("100.00"), [Decimal("60.00"), Decimal("50.00")])

    def test_free_charge_is_paid_with_no_payments(self):
        balance = charge_balance(Decimal("0.00"), [])
        self.assertEqual((balance.outstanding, balance.state), (Decimal("0.00"), "paid"))

    def test_invalid_payment_amounts_are_rejected(self):
        for invalid in (Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("1.001")):
            with self.assertRaises(ValueError, msg=str(invalid)):
                charge_balance(Decimal("100.00"), [invalid])
        with self.assertRaises(ValueError):
            charge_balance(Decimal("-1.00"), [])
        with self.assertRaises(ValueError):
            charge_balance(Decimal("1.001"), [])


if __name__ == "__main__":
    unittest.main()
