import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.notes import (
    CreatePatientNotePayload,
    UpdatePatientNotePayload,
)
from src.api.sync.application.capabilities_cases import get_capabilities


class NoteSchemaTests(unittest.TestCase):
    def test_note_can_be_independent_and_keeps_author_out_of_payload(self):
        note = CreatePatientNotePayload.model_validate({
            "patientId": str(uuid7()), "body": "PRIV-E07-NOTA",
        })
        self.assertIsNone(note.encounter_id)
        self.assertNotIn("actorUserId", type(note).model_fields)

    def test_patch_distinguishes_absence_and_null(self):
        patch = UpdatePatientNotePayload.model_validate({"capturedAtLocal": None})
        self.assertEqual(
            patch.model_dump(exclude_unset=True), {"captured_at_local": None}
        )
        for value in ({}, {"body": None}):
            with self.assertRaises(ValidationError):
                UpdatePatientNotePayload.model_validate(value)

    def test_note_actions_are_available_offline(self):
        catalog = get_capabilities().value.operation_catalog
        self.assertTrue({
            "CreatePatientNote", "UpdatePatientNote", "InvalidatePatientNote"
        }.issubset(catalog))


if __name__ == "__main__":
    unittest.main()
