import unittest
from decimal import Decimal
from uuid import uuid7

from pydantic import ValidationError

from src.api.clinical_records.domain.measurements import (
    CorrectPatientMeasurementPayload,
    RecordPatientMeasurementPayload,
)
from src.api.sync.application.capabilities_cases import get_capabilities


class MeasurementSchemaTests(unittest.TestCase):
    def payload(self, **changes):
        return {
            "patientId": str(uuid7()), "kind": "weight", "value": 70,
            "unit": "kg", **changes,
        }

    def test_five_kinds_and_fixed_units(self):
        cases = (
            ("weight", 70, "kg"),
            ("temperature", Decimal("36.5"), "Cel"),
            ("oxygen_saturation", 98, "%"),
            ("heart_rate", 72, "/min"),
        )
        for kind, value, unit in cases:
            with self.subTest(kind=kind):
                result = RecordPatientMeasurementPayload.model_validate(
                    self.payload(kind=kind, value=value, unit=unit)
                )
                self.assertEqual(result.value, Decimal(str(value)))
        with self.assertRaises(ValidationError):
            RecordPatientMeasurementPayload.model_validate(self.payload(unit="g"))

    def test_pressure_preserves_unknown_component(self):
        result = RecordPatientMeasurementPayload.model_validate({
            "patientId": str(uuid7()), "kind": "blood_pressure",
            "systolicValue": 120, "diastolicValue": None, "unit": "mm[Hg]",
        })
        self.assertIsNone(result.diastolic_value)
        for values in ({}, {"value": 120}):
            with self.assertRaises(ValidationError):
                RecordPatientMeasurementPayload.model_validate({
                    "patientId": str(uuid7()), "kind": "blood_pressure",
                    "unit": "mm[Hg]", **values,
                })

    def test_ranges_nonfinite_and_wrong_shapes_fail(self):
        for value in (0, 1001, "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RecordPatientMeasurementPayload.model_validate(self.payload(value=value))
        with self.assertRaises(ValidationError):
            RecordPatientMeasurementPayload.model_validate(
                self.payload(systolicValue=120)
            )

    def test_correction_preserves_absence_and_requires_a_field(self):
        correction = CorrectPatientMeasurementPayload.model_validate({"value": 70})
        self.assertEqual(correction.model_dump(exclude_unset=True), {"value": Decimal("70")})
        with self.assertRaises(ValidationError):
            CorrectPatientMeasurementPayload.model_validate({})

    def test_measurement_actions_are_offline(self):
        catalog = get_capabilities().value.operation_catalog
        self.assertTrue({
            "RecordPatientMeasurement", "CorrectPatientMeasurement",
            "InvalidatePatientMeasurement",
        }.issubset(catalog))


if __name__ == "__main__":
    unittest.main()
