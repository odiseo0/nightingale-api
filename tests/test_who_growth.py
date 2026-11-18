import unittest
from decimal import Decimal

from src.api.analytics.domain.growth import GrowthInput, compute_growth, z_score_from_lms
from src.api.analytics.domain.references import FIXTURE_LMS_ROWS


class WhoGrowthTests(unittest.TestCase):
    def test_birth_weight_matches_official_median(self):
        row = FIXTURE_LMS_ROWS[0]
        self.assertEqual(row.mu, Decimal("3.3464"))
        result = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=0, value=Decimal("3.3464"),
        ))
        self.assertAlmostEqual(float(result.z_score), 0.0, places=6)

    def test_known_deviation_gives_expected_sign_and_magnitude(self):
        row = FIXTURE_LMS_ROWS[0]
        low = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=0, value=Decimal("2.5"),
        ))
        self.assertLess(float(low.z_score), 0)
        high = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=0, value=Decimal("4.5"),
        ))
        self.assertGreater(float(high.z_score), 0)

    def test_out_of_range_returns_limit_without_curve(self):
        result = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=61, value=Decimal("20"),
        ))
        from src.api.analytics.domain.growth import GrowthLimit

        self.assertIsInstance(result, GrowthLimit)
        self.assertIn("no se extrapola", result.limit_explanation)

    def test_unverified_indicator_returns_limit(self):
        result = compute_growth(GrowthInput(
            reference_code="who2006", indicator="bmi_for_age", sex="male",
            age_months=12, value=Decimal("17"),
        ))
        from src.api.analytics.domain.growth import GrowthLimit

        self.assertIsInstance(result, GrowthLimit)

    def test_unverified_month_returns_limit_instead_of_approximation(self):
        result = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=1, value=Decimal("4.5"),
        ))
        from src.api.analytics.domain.growth import GrowthLimit

        self.assertIsInstance(result, GrowthLimit)

    def test_month_five_fixture_matches_official_median(self):
        result = compute_growth(GrowthInput(
            reference_code="who2006", indicator="weight_for_age", sex="male",
            age_months=5, value=Decimal("7.5105"),
        ))
        self.assertAlmostEqual(float(result.z_score), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
