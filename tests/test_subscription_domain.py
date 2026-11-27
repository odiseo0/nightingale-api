import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pydantic import ValidationError

from src.api.subscriptions.domain.plans import (
    INITIAL_PLAN_VERSIONS,
    Plan,
    PlanVersion,
    price_for,
)
from src.api.subscriptions.domain.subscriptions import (
    GRACE_DAYS,
    SeatUsage,
    commercial_availability,
)


class PlanTests(unittest.TestCase):
    def test_initial_catalog_matches_d21(self):
        expected = {
            "independent": (2, "18.00", "100.00"),
            "small_practice": (5, "24.00", "240.00"),
            "medical_center": (20, "75.00", "500.00"),
        }
        self.assertEqual(set(INITIAL_PLAN_VERSIONS), set(expected))
        for code, (seats, p30, pyear) in expected.items():
            version = INITIAL_PLAN_VERSIONS[code]
            self.assertEqual(version.seat_limit, seats)
            self.assertEqual(version.price_30d_usd, Decimal(p30))
            self.assertEqual(version.price_year_usd, Decimal(pyear))
            self.assertEqual(version.currency, "USD")

    def test_plans_share_capabilities_and_differ_only_in_price_and_seats(self):
        # PlanVersion has no feature matrix: seats and prices are its only variables.
        self.assertEqual(
            set(PlanVersion.model_fields),
            {"version", "seat_limit", "price_30d_usd", "price_year_usd", "currency"},
        )

    def test_price_for_selects_the_periodicity(self):
        version = INITIAL_PLAN_VERSIONS["small_practice"]
        self.assertEqual(price_for(version, "days_30"), Decimal("24.00"))
        self.assertEqual(price_for(version, "year_1"), Decimal("240.00"))

    def test_plan_version_rejects_invalid_values(self):
        with self.assertRaises(ValidationError):
            PlanVersion(version=1, seat_limit=0, price_30d_usd=Decimal("18.00"), price_year_usd=Decimal("100.00"))
        with self.assertRaises(ValidationError):
            PlanVersion(version=1, seat_limit=2, price_30d_usd=Decimal("-1"), price_year_usd=Decimal("100.00"))
        with self.assertRaises(ValidationError):
            PlanVersion(version=1, seat_limit=2, price_30d_usd=Decimal("18.001"), price_year_usd=Decimal("100.00"))
        with self.assertRaises(ValidationError):
            PlanVersion(version=0, seat_limit=2, price_30d_usd=Decimal("18.00"), price_year_usd=Decimal("100.00"))

    def test_plan_rejects_codes_outside_the_closed_set(self):
        with self.assertRaises(ValidationError):
            Plan(code="enterprise", name="X", description="Y")
        with self.assertRaises(ValidationError):
            Plan(code="independent", name="", description="Y")


class SeatTests(unittest.TestCase):
    def test_last_seat_has_a_single_winner(self):
        usage = SeatUsage(used=1, limit=2)
        self.assertTrue(usage.can_add())
        full = SeatUsage(used=2, limit=2)
        self.assertFalse(full.can_add())
        self.assertEqual(full.available, 0)

    def test_over_limit_blocks_additions_without_removing_anyone(self):
        over = SeatUsage(used=5, limit=2)
        self.assertTrue(over.over_limit)
        self.assertFalse(over.can_add())
        self.assertEqual(over.available, 0)
        self.assertEqual(over.used, 5)

    def test_seat_usage_rejects_invalid_numbers(self):
        with self.assertRaises(ValidationError):
            SeatUsage(used=-1, limit=2)
        with self.assertRaises(ValidationError):
            SeatUsage(used=0, limit=0)


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.ends = datetime(2027, 6, 15, 12, 0, tzinfo=timezone.utc)

    def test_active_until_the_exclusive_end(self):
        self.assertEqual(commercial_availability("active", self.ends, self.ends - timedelta(seconds=1)), "active")
        # [starts, ends): at ends_at the period is already over.
        self.assertEqual(commercial_availability("active", self.ends, self.ends), "grace")

    def test_grace_lasts_seven_days_then_suspends(self):
        last_grace = self.ends + timedelta(days=GRACE_DAYS) - timedelta(seconds=1)
        self.assertEqual(commercial_availability("active", self.ends, last_grace), "grace")
        self.assertEqual(
            commercial_availability("active", self.ends, self.ends + timedelta(days=GRACE_DAYS)),
            "suspended",
        )

    def test_pending_and_cancelled_do_not_depend_on_dates(self):
        now = datetime(2027, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(commercial_availability("pending_activation", None, now), "pending_activation")
        self.assertEqual(commercial_availability("cancelled", None, now), "cancelled")

    def test_cancellation_keeps_the_paid_time_until_the_period_ends(self):
        before = datetime(2027, 6, 1, tzinfo=timezone.utc)
        self.assertEqual(commercial_availability("cancelled", self.ends, before), "active")
        after = self.ends + timedelta(days=GRACE_DAYS)
        self.assertEqual(commercial_availability("cancelled", self.ends, after), "cancelled")

    def test_naive_now_is_rejected(self):
        with self.assertRaises(ValueError):
            commercial_availability("active", self.ends, datetime(2027, 6, 1))


if __name__ == "__main__":
    unittest.main()
