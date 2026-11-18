import unittest
from pathlib import Path

from src.api.analytics.application.etl_cases import rebuild_analytics, run_etl
from src.api.analytics.repository.models import (
    AnalyticEtlState,
    AnalyticMeasurementPoint,
)

ROOT = Path(__file__).resolve().parents[1]


class ClinicalAnalyticsEtlModelTests(unittest.TestCase):
    def test_models_map_analytics_schema(self):
        self.assertEqual(
            AnalyticMeasurementPoint.__table__.schema, "analytics"
        )
        self.assertEqual(AnalyticEtlState.__table__.schema, "analytics")
        primary = set(AnalyticMeasurementPoint.__table__.primary_key.columns.keys())
        self.assertEqual(
            primary,
            {
                "account_id",
                "patient_id",
                "measurement_kind",
                "measured_at",
                "source_measurement_id",
            },
        )

    def test_migration_declares_schema_and_grants(self):
        path = ROOT / "migrations/versions/20261117_06_analytics.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_06"', source)
        self.assertIn('down_revision = "20261117_05"', source)
        self.assertIn("CREATE SCHEMA analytics", source)
        self.assertIn("GRANT SELECT,INSERT,UPDATE,DELETE ON analytics.measurement_points", source)

    def test_etl_entry_points_are_async_functions(self):
        import inspect

        self.assertTrue(inspect.iscoroutinefunction(run_etl))
        self.assertTrue(inspect.iscoroutinefunction(rebuild_analytics))


if __name__ == "__main__":
    unittest.main()
