import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import ValidationError

from src.api.subscriptions.domain.money import BcvRate, Money, usd_to_ves
from src.api.subscriptions.domain.periods import (
    add_civil_year,
    compute_period,
    next_period_start,
    period_end,
)


def rate(value: str, day: date = date(2026, 11, 26)) -> BcvRate:
    return BcvRate(rate_ves_per_usd=Decimal(value), rate_date=day, source="bcv-ficticio")


class MoneyTests(unittest.TestCase):
    def test_quote_matches_the_approved_fictitious_examples(self):
        self.assertEqual(usd_to_ves(Decimal("18.00"), rate("400.25")), Decimal("7204.50"))
        self.assertEqual(usd_to_ves(Decimal("100.00"), rate("400.25")), Decimal("40025.00"))
        self.assertEqual(usd_to_ves(Decimal("24.00"), rate("400.25")), Decimal("9606.00"))
        self.assertEqual(usd_to_ves(Decimal("500.00"), rate("123.456")), Decimal("61728.00"))

    def test_rounding_is_half_up_and_applied_once(self):
        # 2.675 would become 2.67 with binary floats; exact decimal gives 2.68.
        self.assertEqual(usd_to_ves(Decimal("1.00"), rate("2.675")), Decimal("2.68"))
        self.assertEqual(usd_to_ves(Decimal("0.05"), rate("0.10")), Decimal("0.01"))

    def test_money_rejects_non_finite_negative_or_ambiguous_amounts(self):
        for invalid in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValidationError, msg=invalid):
                Money(amount=Decimal(invalid), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("-1.00"), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("0"), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("1.001"), currency="USD")
        with self.assertRaises(ValidationError):
            Money(amount=Decimal("1.00"), currency="EUR")

    def test_rate_rejects_non_positive_or_overprecise_values(self):
        with self.assertRaises(ValidationError):
            rate("0")
        with self.assertRaises(ValidationError):
            rate("-400.25")
        with self.assertRaises(ValidationError):
            rate("400.1234567")
        with self.assertRaises(ValidationError):
            BcvRate(rate_ves_per_usd=Decimal("NaN"), rate_date=date(2026, 11, 26), source="x")

    def test_conversion_rejects_invalid_input_amounts(self):
        for invalid in (Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-3")):
            with self.assertRaises(ValueError, msg=str(invalid)):
                usd_to_ves(invalid, rate("400.25"))


class PeriodTests(unittest.TestCase):
    def test_thirty_days_is_not_a_calendar_month(self):
        start = datetime(2027, 1, 20, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(period_end(start, "days_30"), datetime(2027, 2, 19, 15, 0, tzinfo=timezone.utc))
        january = datetime(2027, 1, 31, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(period_end(january, "days_30"), datetime(2027, 3, 2, 12, 0, tzinfo=timezone.utc))

    def test_annual_period_is_the_civil_year_in_caracas(self):
        start = datetime(2027, 3, 10, 14, 30, tzinfo=timezone.utc)
        self.assertEqual(period_end(start, "year_1"), datetime(2028, 3, 10, 14, 30, tzinfo=timezone.utc))

    def test_leap_day_ends_on_feb_28(self):
        self.assertEqual(add_civil_year(date(2028, 2, 29)), date(2029, 2, 28))
        # 2028-02-29 01:30 UTC is 2028-02-28 21:30 in Caracas: the civil date is Feb 28.
        start = datetime(2028, 2, 29, 1, 30, tzinfo=timezone.utc)
        self.assertEqual(period_end(start, "year_1"), datetime(2029, 3, 1, 1, 30, tzinfo=timezone.utc))
        # 2028-02-29 05:00 UTC is 2028-02-29 01:00 in Caracas: ends 2029-02-28 01:00 local.
        start = datetime(2028, 2, 29, 5, 0, tzinfo=timezone.utc)
        self.assertEqual(period_end(start, "year_1"), datetime(2029, 2, 28, 5, 0, tzinfo=timezone.utc))

    def test_early_renewal_keeps_paid_days(self):
        approval = datetime(2027, 5, 1, 12, 0, tzinfo=timezone.utc)
        last_end = datetime(2027, 6, 15, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(next_period_start(last_end, approval), last_end)
        period = compute_period(last_end, approval, "days_30")
        self.assertEqual(period.starts_at, last_end)
        self.assertEqual(period.ends_at, datetime(2027, 7, 15, 12, 0, tzinfo=timezone.utc))

    def test_late_renewal_starts_at_approval_without_retroactivity(self):
        approval = datetime(2027, 5, 1, 12, 0, tzinfo=timezone.utc)
        expired_end = datetime(2027, 4, 1, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(next_period_start(expired_end, approval), approval)
        self.assertEqual(next_period_start(None, approval), approval)

    def test_naive_instants_are_rejected(self):
        with self.assertRaises(ValueError):
            period_end(datetime(2027, 1, 1), "days_30")
        with self.assertRaises(ValueError):
            next_period_start(None, datetime(2027, 1, 1))


if __name__ == "__main__":
    unittest.main()
