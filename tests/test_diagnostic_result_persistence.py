import unittest
from pathlib import Path

from src.api.diagnostic_results.repository.models import (
    DiagnosticReport,
    DiagnosticReportHistory,
    DiagnosticReportResult,
    DiagnosticReportResultHistory,
    ReportAttachment,
    ReportAttachmentHistory,
)

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticResultPersistenceModelTests(unittest.TestCase):
    def test_models_map_diagnostic_tables(self):
        self.assertEqual(DiagnosticReport.__tablename__, "diagnostic_reports")
        self.assertEqual(
            DiagnosticReportHistory.__tablename__, "diagnostic_report_histories"
        )
        self.assertEqual(
            DiagnosticReportResult.__tablename__, "diagnostic_report_results"
        )
        self.assertEqual(ReportAttachment.__tablename__, "report_attachments")
        self.assertEqual(
            ReportAttachmentHistory.__tablename__, "report_attachment_histories"
        )
        for model in (
            DiagnosticReportHistory,
            DiagnosticReportResultHistory,
            ReportAttachmentHistory,
        ):
            self.assertEqual(
                set(model.__table__.primary_key.columns.keys()),
                {"account_id", "id", "version"},
            )

    def test_result_and_attachment_columns(self):
        results = DiagnosticReportResult.__table__.columns
        self.assertFalse(results["analyte_name"].nullable)
        self.assertTrue(results["unit"].nullable)
        attachments = ReportAttachment.__table__.columns
        self.assertFalse(attachments["sha256"].nullable)
        self.assertFalse(attachments["storage_key"].nullable)

    def test_migration_declares_section_and_grants(self):
        path = ROOT / "migrations/versions/20261117_03_diagnostic_results.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_03"', source)
        self.assertIn('down_revision = "20261117_02"', source)
        self.assertIn("diagnostic_reports_access", source)
        self.assertIn("REFERENCES nightingale.diagnostic_reports", source)
        self.assertIn("guard_clinical_identity", source)


if __name__ == "__main__":
    unittest.main()
