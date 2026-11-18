import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.specialties.domain.records import (
    CaptureSpecialtyRecordPayload,
    SpecialtyRecordValue,
    UpdateSpecialtyRecordPayload,
)
from src.api.specialties.domain.templates import (
    CreateSpecialtyTemplatePayload,
    SpecialtyTemplateField,
    UpdateSpecialtyTemplatePayload,
)

FIELD = {"fieldKey": "motivo", "label": "Motivo", "fieldKind": "text", "displayOrder": 1}


class SpecialtyTemplateSchemaTests(unittest.TestCase):
    def test_template_with_unique_typed_fields(self):
        result = CreateSpecialtyTemplatePayload.model_validate({
            "name": "PRIV-E19-ODONTO-CONSULTA",
            "fields": [
                FIELD,
                {"fieldKey": "dolor", "label": "Dolor", "fieldKind": "boolean",
                 "displayOrder": 2},
            ],
        })
        self.assertEqual(result.specialty, "dentistry")
        self.assertFalse(result.fields[1].required)

    def test_duplicate_keys_and_bad_options_fail(self):
        with self.assertRaises(ValidationError):
            CreateSpecialtyTemplatePayload.model_validate({
                "name": "X", "fields": [FIELD, dict(FIELD, label="Otro")],
            })
        with self.assertRaises(ValidationError):
            SpecialtyTemplateField.model_validate({
                "fieldKey": "a", "label": "A", "fieldKind": "text",
                "options": "solo", "displayOrder": 1,
            })

    def test_empty_patch_fails(self):
        with self.assertRaises(ValidationError):
            UpdateSpecialtyTemplatePayload.model_validate({})

    def test_record_value_is_single_typed_and_absent_fields_stay_absent(self):
        with self.assertRaises(ValidationError):
            SpecialtyRecordValue.model_validate({"fieldKey": "a"})
        with self.assertRaises(ValidationError):
            SpecialtyRecordValue.model_validate({
                "fieldKey": "a", "valueText": "x", "valueBoolean": True,
            })
        record = CaptureSpecialtyRecordPayload.model_validate({
            "patientId": str(uuid7()), "templateId": str(uuid7()),
            "values": [{"fieldKey": "motivo", "valueText": "Revisión"}],
        })
        self.assertEqual(len(record.values), 1)

    def test_record_patch_requires_a_field(self):
        with self.assertRaises(ValidationError):
            UpdateSpecialtyRecordPayload.model_validate({})


if __name__ == "__main__":
    unittest.main()
