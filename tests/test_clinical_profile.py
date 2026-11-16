import unittest
from datetime import date
from types import SimpleNamespace
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.application.clinical_cases import clinical_profile_response
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery, SetPatientSexAtBirthPayload
from src.api.sync.application.capabilities_cases import get_capabilities


class ClinicalProfileTests(unittest.TestCase):
    def test_payload_requires_explicit_sex_and_uses_unknown_source(self):
        payload = SetPatientSexAtBirthPayload.model_validate({"sexAtBirth": None})
        self.assertIsNone(payload.sex_at_birth)
        self.assertEqual(payload.source_type, "unknown")
        with self.assertRaises(ValidationError):
            SetPatientSexAtBirthPayload.model_validate({"sourceType": "patient"})
        with self.assertRaises(ValidationError):
            SetPatientSexAtBirthPayload.model_validate({"sexAtBirth": "other", "actorUserId": str(uuid7())})

    def test_birth_history_accepts_incremental_version_filter(self):
        self.assertEqual(ClinicalHistoryQuery(afterVersion=2).after_version, 2)
        with self.assertRaises(ValidationError):
            ClinicalHistoryQuery(afterVersion=-1)
        with self.assertRaises(ValidationError):
            ClinicalHistoryQuery(unknown=1)

    def test_action_is_available_offline(self):
        capabilities = get_capabilities().value
        self.assertIn("SetPatientSexAtBirth", capabilities.operation_catalog)
        self.assertNotIn("SetPatientSexAtBirth", capabilities.online_only_actions)

    def test_age_uses_full_years_and_leap_day_rule(self):
        patient = SimpleNamespace(patient_id=uuid7(), birth_date=date(2000, 2, 29), version=3)
        profile = SimpleNamespace(
            sex_at_birth="unknown",
            source_type="patient",
            version=2,
            created_at=None,
            updated_at=None,
        )
        self.assertEqual(clinical_profile_response(profile, patient, date(2026, 2, 28)).age_years, 25)
        response = clinical_profile_response(profile, patient, date(2026, 3, 1))
        self.assertEqual(response.age_years, 26)
        self.assertEqual(response.patient_version, 3)
        self.assertEqual(response.age_as_of, date(2026, 3, 1))

    def test_missing_birth_date_produces_no_age(self):
        patient = SimpleNamespace(patient_id=uuid7(), birth_date=None, version=1)
        profile = SimpleNamespace(sex_at_birth=None, source_type="unknown", version=1, created_at=None, updated_at=None)
        self.assertIsNone(clinical_profile_response(profile, patient, date(2026, 11, 15)).age_years)


if __name__ == "__main__":
    unittest.main()
