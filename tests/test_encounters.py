import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.encounters.domain.encounters import (
    CreatePatientEncounterPayload,
    EncounterQuery,
    UpdatePatientEncounterPayload,
)
from src.api.sync.application.capabilities_cases import get_capabilities


class EncounterSchemaTests(unittest.TestCase):
    def test_reason_does_not_require_appointment_or_service(self):
        payload = CreatePatientEncounterPayload.model_validate({
            "patientId": str(uuid7()),
            "attendingProfessionalId": str(uuid7()),
            "reason": "PRIV-E06-MOTIVO",
        })
        self.assertIsNone(payload.appointment_id)
        self.assertIsNone(payload.occurred_at)
        self.assertNotIn("serviceId", type(payload).model_fields)

    def test_patch_preserves_absence_and_rejects_empty_or_null_time(self):
        patch = UpdatePatientEncounterPayload.model_validate({"reason": "Corrected"})
        self.assertEqual(patch.model_dump(exclude_unset=True), {"reason": "Corrected"})
        for payload in ({}, {"occurredAt": None}):
            with self.assertRaises(ValidationError):
                UpdatePatientEncounterPayload.model_validate(payload)

    def test_query_uses_camel_case_and_ordered_range(self):
        query = EncounterQuery.model_validate({
            "from": "2026-11-01T04:00:00Z",
            "until": "2026-11-02T04:00:00Z",
        })
        self.assertIsNotNone(query.from_)
        with self.assertRaises(ValidationError):
            EncounterQuery.model_validate({
                "from": "2026-11-02T04:00:00Z",
                "until": "2026-11-01T04:00:00Z",
            })

    def test_encounter_actions_are_offline_capabilities(self):
        capabilities = get_capabilities().value
        for action in (
            "CreatePatientEncounter",
            "UpdatePatientEncounter",
            "InvalidatePatientEncounter",
        ):
            self.assertIn(action, capabilities.operation_catalog)
            self.assertNotIn(action, capabilities.online_only_actions)


if __name__ == "__main__":
    unittest.main()
