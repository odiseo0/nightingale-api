import unittest
from pathlib import Path

from src.api.specialties.repository.models import (
    DentalFinding,
    DentalFindingHistory,
    DentalTreatment,
    DentalTreatmentHistory,
)

ROOT = Path(__file__).resolve().parents[1]


class SpecialtyPersistenceModelTests(unittest.TestCase):
    def test_models_map_dental_tables(self):
        self.assertEqual(DentalFinding.__tablename__, "dental_findings")
        self.assertEqual(DentalFindingHistory.__tablename__, "dental_finding_histories")
        self.assertEqual(DentalTreatment.__tablename__, "dental_treatments")
        self.assertEqual(
            DentalTreatmentHistory.__tablename__, "dental_treatment_histories"
        )
        for model in (DentalFindingHistory, DentalTreatmentHistory):
            self.assertEqual(
                set(model.__table__.primary_key.columns.keys()),
                {"account_id", "id", "version"},
            )

    def test_migration_declares_fdi_and_grants(self):
        path = ROOT / "migrations/versions/20261117_05_specialty.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_05"', source)
        self.assertIn('down_revision = "20261117_04"', source)
        self.assertIn("tooth_fdi BETWEEN 11 AND 48", source)
        self.assertIn("uq_dental_findings_active", source)
        self.assertIn("REFERENCES nightingale.dental_findings", source)


if __name__ == "__main__":
    unittest.main()
