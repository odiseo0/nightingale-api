import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


class CreatePracticeScriptTests(unittest.TestCase):
    def run_script(self, content=None, settings=None, arguments=None):
        environment = {
            key: value for key, value in os.environ.items()
            if not key.upper().startswith(("API_", "OIDC_", "DB_", "POOL_", "BOOTSTRAP_"))
            and key.upper() != "SQLALCHEMY_DATABASE_URI"
        }
        environment["PYTHONPATH"] = str(ROOT)
        environment.update(settings or {})

        with TemporaryDirectory(prefix="script-", dir=ROOT / ".tmp") as directory:
            source = Path(directory) / "practice.json"
            if content is not None:
                source.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
            return subprocess.run(
                [sys.executable, "-m", "scripts.create_practice", *(arguments or ["--file", str(source)])],
                cwd=directory, env=environment, capture_output=True, text=True, timeout=20,
            )

    def data(self):
        return json.dumps({
            "ownerIssuer": "https://issuer.example.invalid/realm",
            "ownerSubject": "fixture-subject",
            "ownerName": "Fixture Owner",
            "professionalName": "Fixture Professional",
            "displayName": "Fixture Practice",
            "timeZone": "America/Caracas",
            "locationName": "Fixture Office",
            "locationAddress": "Fictional address",
            "locationState": "Fixture State",
            "locationCity": "Fixture City",
        })

    def test_help_needs_no_database_or_oidc_configuration(self):
        result = self.run_script(arguments=["--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--file", result.stdout)
        self.assertNotIn("bootstrap-practice", result.stdout)

    def test_missing_malformed_and_invalid_files_have_no_private_details(self):
        for content in (None, b"\xff", "{", '{"fixture-private-input":"fixture-private-value"}'):
            with self.subTest(kind=type(content).__name__):
                result = self.run_script(content)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("fixture-private", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_administrative_uri_is_required_even_when_runtime_uri_exists(self):
        result = self.run_script(self.data(), {
            "SQLALCHEMY_DATABASE_URI": "postgresql+asyncpg://fixture:fixture-private-password@127.0.0.1:1/fixture",
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("BOOTSTRAP_DATABASE_URI", result.stderr)
        self.assertNotIn("fixture-private-password", result.stderr)

    def test_invalid_administrative_urls_do_not_expose_credentials(self):
        for uri in (
            "not-a-url-fixture-private-password",
            "sqlite:///fixture-private-password.db",
            "postgresql+asyncpg://fixture:fixture-private-password@localhost:bad/fixture",
            "postgresql+asyncpg://fixture:fixture-private-password@localhost:65536/fixture",
        ):
            with self.subTest(kind=uri.split(":")[0]):
                result = self.run_script(self.data(), {"BOOTSTRAP_DATABASE_URI": uri})
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("fixture-private-password", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_issuer_must_match_before_connecting(self):
        result = self.run_script(self.data(), {
            "BOOTSTRAP_DATABASE_URI": "postgresql+asyncpg://fixture:fixture-private-password@127.0.0.1:1/fixture",
            "OIDC_ISSUER": "https://other.example.invalid/realm",
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("OIDC_ISSUER", result.stderr)
        self.assertNotIn("fixture-private-password", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
