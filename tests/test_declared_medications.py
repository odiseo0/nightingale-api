import unittest
from datetime import UTC, datetime
from uuid import uuid7

from pydantic import ValidationError

from src.api.medications.domain.medications import (
    DeclarePatientMedicationPayload,
    DeclaredMedicationResponse,
    InvalidatePatientDeclaredMedicationPayload,
    UpdatePatientDeclaredMedicationPayload,
)
from src.api.medications.domain.reviews import ReviewPatientDeclaredMedicationPayload


class DeclaredMedicationSchemaTests(unittest.TestCase):
    def test_declared_medication_from_other_profician_preserves_incomplete_data(self):
        for day in ("2021", "2021-03", "2021-03-10"):
            with self.subTest(day=day):
                result = DeclarePatientMedicationPayload.model_validate({
                    "patientId": str(uuid7()),
                    "medicationName": "PRIV-E15-METFORMINA",
                    "sourceType": "other_professional",
                    "startDate": day,
                })
                self.assertEqual(result.start_date, day)
                self.assertIsNone(result.dose_description)
                self.assertIsNone(result.prescriber_name)

    def test_unknown_source_and_bad_calendar_date_fail(self):
        with self.assertRaises(ValidationError):
            DeclarePatientMedicationPayload.model_validate({
                "patientId": str(uuid7()), "medicationName": "Fixture",
                "sourceType": "prescription",
            })
        with self.assertRaises(ValidationError):
            DeclarePatientMedicationPayload.model_validate({
                "patientId": str(uuid7()), "medicationName": "Fixture",
                "sourceType": "patient", "startDate": "2021-02-29",
            })

    def test_known_period_end_before_start_fails(self):
        with self.assertRaises(ValidationError):
            DeclarePatientMedicationPayload.model_validate({
                "patientId": str(uuid7()), "medicationName": "Fixture",
                "sourceType": "patient", "startDate": "2021-05",
                "endDate": "2021-04",
            })

    def test_empty_patch_and_null_on_present_field_fail(self):
        with self.assertRaises(ValidationError):
            UpdatePatientDeclaredMedicationPayload.model_validate({})
        with self.assertRaises(ValidationError):
            UpdatePatientDeclaredMedicationPayload.model_validate({
                "medicationName": None,
            })

    def test_review_and_invalidate_payloads_are_shaped(self):
        ReviewPatientDeclaredMedicationPayload.model_validate({})
        InvalidatePatientDeclaredMedicationPayload.model_validate({})
        with self.assertRaises(ValidationError):
            ReviewPatientDeclaredMedicationPayload.model_validate({"note": "x"})

    def test_response_serializes_camel_case(self):
        now = datetime(2026, 11, 17, tzinfo=UTC)
        result = DeclaredMedicationResponse.model_validate({
            "medicationId": str(uuid7()), "patientId": str(uuid7()),
            "medicationName": "Fixture", "sourceType": "document",
            "encounterId": None, "reviewStatus": "declared",
            "reviewedAt": None, "reviewedByUserId": None,
            "recordStatus": "valid",
            "correctionReason": None, "createdAt": now, "updatedAt": now,
            "version": 1,
        })
        payload = result.model_dump(by_alias=True)
        self.assertIn("medicationId", payload)
        self.assertIn("reviewStatus", payload)
        self.assertEqual(payload["createdAt"], "2026-11-17T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
