import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.immunizations import (
    RecordPatientImmunizationPayload,
    UpdatePatientImmunizationPayload,
)
from src.api.sync.application.capabilities_cases import get_capabilities


class ImmunizationSchemaTests(unittest.TestCase):
    def test_reported_history_preserves_precision_and_optional_details(self):
        for day in ("2020", "2020-05", "2020-05-15"):
            with self.subTest(day=day):
                result = RecordPatientImmunizationPayload.model_validate({
                    "patientId": str(uuid7()), "vaccineName": "PRIV-E13-VACUNA",
                    "occurrenceDate": day, "recordKind": "reported",
                    "sourceType": "patient",
                })
                self.assertEqual(result.occurrence_date, day)
                self.assertIsNone(result.lot_number)

    def test_administered_here_requires_encounter(self):
        with self.assertRaises(ValidationError):
            RecordPatientImmunizationPayload.model_validate({
                "patientId": str(uuid7()), "vaccineName": "Fixture",
                "occurrenceDate": "2026-11-01", "recordKind": "administered_here",
            })

    def test_invalid_partial_date_and_empty_patch_fail(self):
        with self.assertRaises(ValidationError):
            RecordPatientImmunizationPayload.model_validate({
                "patientId": str(uuid7()), "vaccineName": "Fixture",
                "occurrenceDate": "2021-02-29",
            })
        with self.assertRaises(ValidationError):
            UpdatePatientImmunizationPayload.model_validate({})

    def test_immunization_actions_are_offline(self):
        catalog = get_capabilities().value.operation_catalog
        self.assertTrue({"RecordPatientImmunization", "UpdatePatientImmunization", "InvalidatePatientImmunization"}.issubset(catalog))


if __name__ == "__main__":
    unittest.main()
