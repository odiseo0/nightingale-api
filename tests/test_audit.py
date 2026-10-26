import os
import subprocess
import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

from src.api.audit.domain.audit import AuditQuery


class AuditSchemaTests(unittest.TestCase):
    def test_range_needs_offsets_and_order_and_rejects_extra_fields(self):
        for fields in (
            {"from": "2026-10-26T00:00:00"},
            {"from": "2026-10-27T00:00:00Z", "until": "2026-10-26T00:00:00Z"},
            {"cursor": "fixture"}, {"shows": 501},
        ):
            with self.assertRaises(ValidationError):
                AuditQuery.model_validate(fields)

    def test_maintenance_rejects_missing_or_invalid_uri_without_secrets(self):
        script = Path(__file__).resolve().parents[1] / "scripts/purge_expired_results.py"
        for uri in ("", "fixture-private", "postgresql+asyncpg://fixture:fixture-private@localhost:99999/fixture"):
            environment = dict(os.environ, MAINTENANCE_DATABASE_URI=uri)
            result = subprocess.run([sys.executable, str(script)], env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("fixture-private", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
