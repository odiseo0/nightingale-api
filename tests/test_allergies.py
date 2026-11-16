import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.allergies import (
    CreatePatientAllergyIntolerancePayload,
    UpdatePatientAllergyIntolerancePayload,
)


class AllergySchemaTests(unittest.TestCase):
    def test_unknown_type_and_optional_reaction_are_allowed(self):
        payload = CreatePatientAllergyIntolerancePayload.model_validate({"patientId": str(uuid7()), "substance": "ALG-A"})
        self.assertEqual(payload.type, "unknown")
        self.assertIsNone(payload.reaction_description)
        self.assertEqual(payload.clinical_status, "active")
        self.assertEqual(payload.verification_status, "unconfirmed")
        with self.assertRaises(ValidationError):
            CreatePatientAllergyIntolerancePayload.model_validate({
                "patientId": str(uuid7()), "substance": "ALG-A",
                "verificationStatus": "entered-in-error",
            })

    def test_intolerance_is_not_reclassified(self):
        payload = CreatePatientAllergyIntolerancePayload.model_validate({
            "patientId": str(uuid7()), "substance": "Sustancia Ficticia B", "type": "intolerance"
        })
        self.assertEqual(payload.type, "intolerance")

    def test_patch_preserves_absence_and_allows_optional_nulls(self):
        patch = UpdatePatientAllergyIntolerancePayload.model_validate({"reactionDescription": None, "onsetDate": None})
        self.assertEqual(patch.model_fields_set, {"reaction_description", "onset_date"})
        with self.assertRaises(ValidationError):
            UpdatePatientAllergyIntolerancePayload.model_validate({})
        with self.assertRaises(ValidationError):
            UpdatePatientAllergyIntolerancePayload.model_validate({"verificationStatus": "entered-in-error"})
        with self.assertRaises(ValidationError):
            UpdatePatientAllergyIntolerancePayload.model_validate({"substance": None})


if __name__ == "__main__":
    unittest.main()
