import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.diagnostic_results.domain.reports import (
    CreateDiagnosticReportPayload,
    UpdateDiagnosticReportPayload,
)
from src.api.diagnostic_results.domain.results import (
    AddDiagnosticReportResultPayload,
    UpdateDiagnosticReportResultPayload,
)


class DiagnosticResultSchemaTests(unittest.TestCase):
    def test_report_partial_dates_and_status(self):
        result = CreateDiagnosticReportPayload.model_validate({
            "patientId": str(uuid7()), "sourceName": "PRIV-E18-LAB",
            "sampleDate": "2026-11-01", "reportKind": "laboratory",
            "reportStatus": "preliminary",
        })
        self.assertEqual(result.sample_date, "2026-11-01")
        self.assertEqual(result.source_type, "unknown")

    def test_numeric_result_requires_unit_and_text_result_shape(self):
        with self.assertRaises(ValidationError):
            AddDiagnosticReportResultPayload.model_validate({
                "reportId": str(uuid7()), "patientId": str(uuid7()),
                "analyteName": "Glucosa", "resultKind": "numeric",
                "value": "95",
            })
        text = AddDiagnosticReportResultPayload.model_validate({
            "reportId": str(uuid7()), "patientId": str(uuid7()),
            "analyteName": "Microscopía", "resultKind": "text",
            "textValue": "Sin observaciones",
        })
        self.assertIsNone(text.unit)

    def test_reference_interval_order_and_single_reference(self):
        with self.assertRaises(ValidationError):
            AddDiagnosticReportResultPayload.model_validate({
                "reportId": str(uuid7()), "patientId": str(uuid7()),
                "analyteName": "Hb", "resultKind": "numeric", "value": "14",
                "unit": "g/dL", "referenceLow": "20", "referenceHigh": "10",
            })
        with self.assertRaises(ValidationError):
            AddDiagnosticReportResultPayload.model_validate({
                "reportId": str(uuid7()), "patientId": str(uuid7()),
                "analyteName": "Hb", "resultKind": "numeric", "value": "14",
                "unit": "g/dL", "referenceLow": "10", "referenceText": "12-16",
            })

    def test_empty_patch_fails(self):
        with self.assertRaises(ValidationError):
            UpdateDiagnosticReportPayload.model_validate({})
        with self.assertRaises(ValidationError):
            UpdateDiagnosticReportResultPayload.model_validate({})


if __name__ == "__main__":
    unittest.main()
