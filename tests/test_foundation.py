import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class FoundationTests(unittest.TestCase):
    def run_python(self, code: str, settings: dict[str, str] | None = None) -> dict:
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.upper().startswith(("API_", "DB_", "POOL_", "OIDC_"))
            and key.upper() != "SQLALCHEMY_DATABASE_URI"
        }
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        environment.update(settings or {})

        # Each process reads only the settings of this test, never a local .env.
        with TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", "import json\n" + textwrap.dedent(code)],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def database_settings(self) -> dict[str, str]:
        return {
            "SQLALCHEMY_DATABASE_URI": (
                "postgresql+asyncpg://fixture:fictional-password@127.0.0.1:1/fixture"
            )
        }

    def test_current_engine_requires_a_database_uri_before_importing_the_app(self):
        result = self.run_python("""
            from sqlalchemy.exc import ArgumentError

            try:
                import src.application
            except ArgumentError:
                print(json.dumps({"requires_uri": True}))
            else:
                print(json.dumps({"requires_uri": False}))
        """)

        self.assertTrue(result["requires_uri"])

    def test_invalid_environment_stops_startup(self):
        result = self.run_python("""
            from pydantic import ValidationError

            try:
                import src.application
            except ValidationError:
                print(json.dumps({"failed": True}))
            else:
                print(json.dumps({"failed": False}))
        """, {**self.database_settings(), "API_ENVIRONMENT": "invalid"})

        self.assertTrue(result["failed"])

    def test_invalid_or_partial_database_settings_are_rejected(self):
        result = self.run_python("""
            from pydantic import ValidationError
            from src.settings.db_settings import DBSettings

            values = [
                {"DB_HOST": "localhost"},
                {"DB_HOST": ""},
                {"SQLALCHEMY_DATABASE_URI": "not-a-url-fixture-secret"},
                {"SQLALCHEMY_DATABASE_URI": "sqlite:///fixture.db"},
                {"pool_timeout": 0},
                {"pool_overflow": -1},
                {"DB_PORT": 65536},
            ]
            errors = []
            for value in values:
                try:
                    DBSettings(**value)
                except ValidationError as error:
                    errors.append(str(error))
            print(json.dumps({"errors": errors}))
        """)

        self.assertEqual(len(result["errors"]), 7)
        self.assertNotIn("not-a-url-fixture-secret", json.dumps(result))

    def test_signing_key_errors_and_settings_repr_do_not_expose_values(self):
        result = self.run_python("""
            from pydantic import ValidationError
            from src.settings.api_settings import APISettings

            short_key = "FICTIVE-SHORT-ONLY"
            valid_key = "fictional-signing-key-for-tests-only-long-enough"
            try:
                APISettings(_env_file=None, sync_signing_key=short_key)
            except ValidationError as error:
                hidden = short_key not in str(error)
            else:
                raise AssertionError("A short key was accepted")
            settings = APISettings(_env_file=None, sync_signing_key=valid_key)
            print(json.dumps({"short_key_error_hides_value": hidden,
                              "repr_hides_value": valid_key not in repr(settings),
                              "value_preserved": settings.sync_signing_key.get_secret_value() == valid_key,
                              "missing_key_is_none": APISettings(_env_file=None).sync_signing_key is None}))
        """)
        self.assertTrue(all(result.values()))

    def test_password_is_preserved_without_being_exposed(self):
        result = self.run_python("""
            from sqlalchemy.engine import make_url
            from src.settings.db_settings import DBSettings

            password = "fixture@:/#value"
            settings = DBSettings(
                DB_HOST="localhost",
                DB_NAME="fixture",
                DB_USERNAME="fixture",
                DB_PASSWORD=password,
            )
            url = make_url(settings.SQLALCHEMY_DATABASE_URI)
            print(json.dumps({
                "password_preserved": url.password == password,
                "password_hidden": password not in repr(settings),
                "uri_hidden": settings.SQLALCHEMY_DATABASE_URI not in repr(settings),
                "default_port": url.port,
            }))
        """)

        self.assertTrue(result["password_preserved"])
        self.assertTrue(result["password_hidden"])
        self.assertTrue(result["uri_hidden"])
        self.assertEqual(result["default_port"], 5432)

    def test_uri_takes_priority_over_separate_fields(self):
        result = self.run_python("""
            from sqlalchemy.engine import make_url
            from src.settings.db_settings import DBSettings

            settings = DBSettings(
                SQLALCHEMY_DATABASE_URI=(
                    "postgresql+asyncpg://fixture:fictional@localhost/from_uri"
                ),
                DB_NAME="ignored",
            )
            print(json.dumps({
                "database": make_url(settings.SQLALCHEMY_DATABASE_URI).database
            }))
        """)

        self.assertEqual(result["database"], "from_uri")

    def test_environment_takes_priority_over_dotenv(self):
        result = self.run_python("""
            from pathlib import Path

            Path(".env").write_text("API_ENVIRONMENT=production\\n", encoding="utf-8")
            from src.settings.api_settings import api_settings
            print(json.dumps({"environment": api_settings.environment}))
        """, {"API_ENVIRONMENT": "test"})

        self.assertEqual(result["environment"], "test")

    def test_import_does_not_connect_and_startup_only_starts_the_listener(self):
        result = self.run_python("""
            from unittest.mock import AsyncMock, patch

            connect = AsyncMock(side_effect=AssertionError("Unexpected connection"))
            with patch("asyncpg.connect", connect):
                from fastapi.testclient import TestClient
                from src.application import app
                from src.core.db.session import engine
                from src.core.services.pg_notifications import notifications

                with patch.object(type(notifications), "start", AsyncMock()) as start:
                    with TestClient(app) as client:
                        status = client.get("/health/live").status_code
                    start.assert_awaited_once()
                connect.assert_not_awaited()
            print(json.dumps({"status": status, "connections": connect.await_count}))
        """, self.database_settings())

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["connections"], 0)

    def test_readiness_closes_its_session_without_committing(self):
        result = self.run_python("""
            from unittest.mock import AsyncMock, MagicMock, patch
            from fastapi.testclient import TestClient
            from src.application import app


            factory = MagicMock()
            database = factory.return_value.__aenter__.return_value
            database.execute = AsyncMock()
            database.close = AsyncMock()
            database.commit = AsyncMock()

            with patch("src.core.db.deps.async_session_factory", factory):
                with TestClient(app) as client:
                    with patch("src.api.health.notifications") as listener:
                        listener.ready = True
                        response = client.get("/health/ready")
            print(json.dumps({
                "status": response.status_code,
                "body": response.json(),
                "statement": str(database.execute.await_args.args[0]),
                "closed": database.close.await_count,
                "commits": database.commit.await_count,
            }))
        """, self.database_settings())

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["body"]["database"], "available")
        self.assertEqual(result["statement"], "SELECT 1")
        self.assertEqual(result["closed"], 1)
        self.assertEqual(result["commits"], 0)

    def test_database_failure_does_not_expose_details_or_stop_liveness(self):
        result = self.run_python("""
            from unittest.mock import AsyncMock, MagicMock, patch
            from fastapi.testclient import TestClient
            from sqlalchemy.exc import SQLAlchemyError
            from src.application import app


            responses = []
            for error in (SQLAlchemyError, OSError, TimeoutError):
                factory = MagicMock()
                database = factory.return_value.__aenter__.return_value
                database.execute = AsyncMock(side_effect=error("fixture-private-details"))
                database.close = AsyncMock()
                with patch("src.core.db.deps.async_session_factory", factory):
                    with TestClient(app) as client:
                        response = client.get("/health/ready")
                        responses.append({
                            "status": response.status_code,
                            "body": response.json(),
                            "live": client.get("/health/live").status_code,
                            "closed": database.close.await_count,
                        })
            print(json.dumps({"responses": responses}))
        """, self.database_settings())

        for response in result["responses"]:
            self.assertEqual(response["status"], 503)
            self.assertEqual(response["body"]["database"], "unavailable")
            self.assertEqual(response["live"], 200)
            self.assertEqual(response["closed"], 1)
        self.assertNotIn("fixture-private-details", json.dumps(result))

    def test_readiness_timeout_is_controlled(self):
        result = self.run_python("""
            import asyncio
            from unittest.mock import AsyncMock, MagicMock, patch
            from fastapi.testclient import TestClient
            from src.application import app
            from src.api.health import db_settings


            async def slow_query(statement):
                await asyncio.sleep(1)

            factory = MagicMock()
            database = factory.return_value.__aenter__.return_value
            database.execute = AsyncMock(side_effect=slow_query)
            database.close = AsyncMock()
            with patch("src.core.db.deps.async_session_factory", factory):
                with patch.object(db_settings, "pool_timeout", 0.01):
                    with TestClient(app) as client:
                        response = client.get("/health/ready")
            print(json.dumps({"status": response.status_code, "body": response.json()}))
        """, self.database_settings())

        self.assertEqual(result["status"], 503)
        self.assertEqual(result["body"]["database"], "unavailable")

    def test_existing_session_dependency_closes_without_committing(self):
        result = self.run_python("""
            from typing import Annotated
            from unittest.mock import AsyncMock, MagicMock, patch
            from fastapi import Depends
            from fastapi.testclient import TestClient
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.application import app
            from src.core.db import get_db


            factory = MagicMock()
            database = factory.return_value.__aenter__.return_value
            database.close = AsyncMock()
            database.commit = AsyncMock()

            @app.get("/test-session")
            async def use_session(db: Annotated[AsyncSession, Depends(get_db)]):
                return {"open": db is database}

            with patch("src.core.db.deps.async_session_factory", factory):
                with TestClient(app) as client:
                    responses = [client.get("/test-session").json() for _ in range(2)]
            print(json.dumps({
                "responses": responses,
                "sessions": factory.call_count,
                "closed": database.close.await_count,
                "commits": database.commit.await_count,
            }))
        """, self.database_settings())

        self.assertEqual(result["responses"], [{"open": True}, {"open": True}])
        self.assertEqual(result["sessions"], 2)
        self.assertEqual(result["closed"], 2)
        self.assertEqual(result["commits"], 0)

    def test_production_has_no_docs_or_openapi_http_routes(self):
        result = self.run_python("""
            from src.application import app
            print(json.dumps({"openapi": app.openapi_url, "docs": app.docs_url, "redoc": app.redoc_url}))
        """, {**self.database_settings(), "API_ENVIRONMENT": "production"})
        self.assertEqual(result, {"openapi": None, "docs": None, "redoc": None})

    def test_uvicorn_loads_the_module_app_without_a_custom_entrypoint(self):
        result = self.run_python("""
            from pathlib import Path
            import tomllib
            import uvicorn
            from src.application import app
            import src.application as application

            config = uvicorn.Config("src.application:app", proxy_headers=False, log_config=None)
            config.load()
            project = tomllib.loads(
                (Path(application.__file__).resolve().parents[1] / "pyproject.toml").read_text()
            )["project"]
            print(json.dumps({
                "same_app": config.loaded_app is app,
                "custom_command": "nightingale-api" in project.get("scripts", {}),
            }))
        """, self.database_settings())

        self.assertTrue(result["same_app"])
        self.assertFalse(result["custom_command"])


if __name__ == "__main__":
    unittest.main()
