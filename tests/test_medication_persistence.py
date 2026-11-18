import unittest
from pathlib import Path

from src.api.medications.repository.models import (
    DeclaredMedication,
    DeclaredMedicationHistory,
)

ROOT = Path(__file__).resolve().parents[1]


class MedicationPersistenceModelTests(unittest.TestCase):
    def test_current_model_maps_declared_medications(self):
        self.assertEqual(DeclaredMedication.__tablename__, "declared_medications")
        columns = DeclaredMedication.__table__.columns
        expected = {
            "id", "account_id", "patient_id", "encounter_id", "medication_name",
            "source_type", "start_date", "end_date", "dose_description",
            "frequency_description", "prescriber_name", "route_description",
            "review_status", "reviewed_at", "reviewed_by_user_id",
            "captured_at_local", "record_status", "correction_reason",
            "created_by_user_id", "updated_by_user_id", "created_at",
            "updated_at", "version",
        }
        self.assertEqual(set(columns.keys()), expected)
        for name in ("medication_name", "source_type", "record_status", "version"):
            self.assertFalse(columns[name].nullable, name)
        for name in (
            "encounter_id", "start_date", "end_date", "dose_description",
            "frequency_description", "prescriber_name", "route_description",
            "reviewed_at", "reviewed_by_user_id", "captured_at_local",
            "correction_reason",
        ):
            self.assertTrue(columns[name].nullable, name)

    def test_history_model_maps_declared_medication_histories(self):
        self.assertEqual(
            DeclaredMedicationHistory.__tablename__, "declared_medication_histories"
        )
        table = DeclaredMedicationHistory.__table__
        self.assertEqual(
            set(table.primary_key.columns.keys()), {"account_id", "id", "version"}
        )

    def test_migration_declares_section_and_grants(self):
        path = ROOT / "migrations/versions/20261117_01_declared_medications.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_01"', source)
        self.assertIn('down_revision = "20261116_10"', source)
        self.assertIn("declared_medications_access", source)
        self.assertIn("'declared_medications'", source)
        self.assertIn("guard_clinical_identity", source)
        self.assertIn("GRANT SELECT,INSERT ON nightingale.declared_medication_histories", source)
        self.assertIn("DEFERRABLE INITIALLY DEFERRED", source)


if __name__ == "__main__":
    unittest.main()
