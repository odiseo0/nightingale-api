import unittest
from pathlib import Path

from src.api.specialties.repository.models import (
    SpecialtyRecord,
    SpecialtyRecordHistory,
    SpecialtyRecordValueRow,
    SpecialtyTemplate,
    SpecialtyTemplateFieldRow,
    SpecialtyTemplateHistory,
)

ROOT = Path(__file__).resolve().parents[1]


class TemplatePersistenceModelTests(unittest.TestCase):
    def test_models_map_specialty_tables(self):
        self.assertEqual(SpecialtyTemplate.__tablename__, "specialty_templates")
        self.assertEqual(
            SpecialtyTemplateHistory.__tablename__, "specialty_template_histories"
        )
        self.assertEqual(
            SpecialtyTemplateFieldRow.__tablename__, "specialty_template_fields"
        )
        self.assertEqual(SpecialtyRecord.__tablename__, "specialty_records")
        self.assertEqual(
            SpecialtyRecordHistory.__tablename__, "specialty_record_histories"
        )
        self.assertEqual(
            SpecialtyRecordValueRow.__tablename__, "specialty_record_values"
        )
        for model in (SpecialtyTemplateHistory, SpecialtyRecordHistory):
            self.assertEqual(
                set(model.__table__.primary_key.columns.keys()),
                {"account_id", "id", "version"},
            )

    def test_template_columns(self):
        columns = SpecialtyTemplate.__table__.columns
        self.assertFalse(columns["name"].nullable)
        self.assertTrue(columns["change_note"].nullable)
        fields = SpecialtyTemplateFieldRow.__table__.columns
        self.assertFalse(fields["field_key"].nullable)
        self.assertFalse(fields["template_version"].nullable)

    def test_migration_declares_section_and_grants(self):
        path = ROOT / "migrations/versions/20261117_04_specialty_templates.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_04"', source)
        self.assertIn('down_revision = "20261117_03"', source)
        self.assertIn("specialty_templates_access", source)
        self.assertIn("REFERENCES nightingale.specialty_templates", source)
        self.assertIn("value_date IS NOT NULL)::integer = 1", source)


if __name__ == "__main__":
    unittest.main()
