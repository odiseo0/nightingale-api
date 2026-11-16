import unittest

from pydantic import ValidationError

from src.api.clinical_records.domain.history import ClinicalHistoryQuery


class ClinicalHistorySchemaTests(unittest.TestCase):
    def test_filters_are_typed_and_unique(self):
        query = ClinicalHistoryQuery.model_validate({
            "sections": ["conditions", "notes"],
            "entryTypes": ["condition", "note"],
            "recordStatus": "valid",
        })
        self.assertEqual(query.sections, ["conditions", "notes"])
        with self.assertRaises(ValidationError):
            ClinicalHistoryQuery.model_validate({"sections": ["notes", "notes"]})

    def test_range_is_ordered(self):
        with self.assertRaises(ValidationError):
            ClinicalHistoryQuery.model_validate({
                "from": "2026-11-02T00:00:00Z", "until": "2026-11-01T00:00:00Z",
            })


if __name__ == "__main__":
    unittest.main()
