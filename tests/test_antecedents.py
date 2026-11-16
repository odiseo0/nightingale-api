import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.antecedents import (
    CreatePatientAntecedentPayload,
    UpdatePatientAntecedentPayload,
)
from src.api.sync.application.capabilities_cases import get_capabilities


class AntecedentSchemaTests(unittest.TestCase):
    def test_categories_and_uncertain_dates(self):
        for category in ("personal", "family", "other"):
            with self.subTest(category=category):
                result = CreatePatientAntecedentPayload.model_validate({
                    "patientId": str(uuid7()), "category": category,
                    "content": "PRIV-ANTECEDENT", "occurrenceDate": "2020-05",
                    "relatedPersonDescription": "Fixture relative" if category == "family" else None,
                })
                self.assertEqual(result.occurrence_date, "2020-05")

    def test_family_requires_related_person(self):
        with self.assertRaises(ValidationError):
            CreatePatientAntecedentPayload.model_validate({
                "patientId": str(uuid7()), "category": "family", "content": "Fixture",
            })

    def test_patch_requires_fields_and_preserves_absence(self):
        patch = UpdatePatientAntecedentPayload.model_validate({"content": "Corrected"})
        self.assertEqual(patch.model_dump(exclude_unset=True), {"content": "Corrected"})
        with self.assertRaises(ValidationError):
            UpdatePatientAntecedentPayload.model_validate({})

    def test_antecedent_actions_are_offline(self):
        catalog = get_capabilities().value.operation_catalog
        self.assertTrue({"CreatePatientAntecedent", "UpdatePatientAntecedent", "InvalidatePatientAntecedent"}.issubset(catalog))


if __name__ == "__main__":
    unittest.main()
