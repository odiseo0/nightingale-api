import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.conditions import (
    CreatePatientConditionPayload,
    SetPatientClinicalSectionReviewPayload,
    ClinicalDateValue,
    UpdatePatientConditionPayload,
)


class ConditionSchemaTests(unittest.TestCase):
    def test_partial_dates_keep_precision_and_validate_calendar(self):
        for value in ("2024", "2024-02", "2024-02-29"):
            self.assertEqual(ClinicalDateValue.validate(value), value)
        for value in ("2023-02-29", "2024-02-30", "2024-13", "2024-02-29T00:00:00Z", "24-02"):
            with self.assertRaises(ValueError):
                ClinicalDateValue.validate(value)

    def test_create_uses_domain_defaults_and_free_text(self):
        payload = CreatePatientConditionPayload.model_validate({"patientId": str(uuid7()), "name": "CND-A"})
        self.assertEqual(payload.clinical_status, "active")
        self.assertEqual(payload.verification_status, "unconfirmed")
        self.assertEqual(payload.source_type, "unknown")

    def test_patch_preserves_absence_and_allows_nullable_dates(self):
        patch = UpdatePatientConditionPayload.model_validate({"onsetDate": None})
        self.assertEqual(patch.model_fields_set, {"onset_date"})
        with self.assertRaises(ValidationError):
            UpdatePatientConditionPayload.model_validate({"verificationStatus": "entered-in-error"})
        with self.assertRaises(ValidationError):
            UpdatePatientConditionPayload.model_validate({"name": None})

    def test_review_does_not_accept_not_recorded(self):
        payload = SetPatientClinicalSectionReviewPayload.model_validate({"section": "conditions", "informationStatus": "none_known"})
        self.assertEqual(payload.source_type, "unknown")
        with self.assertRaises(ValidationError):
            SetPatientClinicalSectionReviewPayload.model_validate({"section": "conditions", "informationStatus": "not_recorded"})


if __name__ == "__main__":
    unittest.main()
