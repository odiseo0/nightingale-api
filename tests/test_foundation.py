import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from src.application import create_app
from src.core.db.session import create_db_engine
from src.settings.api_settings import APISettings
from src.settings.db_settings import DBSettings


class FoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        # Never use a developer's database or dotenv file in these process tests.
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.upper().startswith(("API_", "DB_", "POOL_"))
            and key.upper() != "SQLALCHEMY_DATABASE_URI"
        }
        self.enterContext(patch.dict(os.environ, environment, clear=True))
        self.enterContext(patch.dict(APISettings.model_config, {"env_file": None}))
        self.enterContext(patch.dict(DBSettings.model_config, {"env_file": None}))

    def test_process_starts_without_database_but_is_not_ready(self) -> None:
        app = create_app()

        with TestClient(app) as client:
            self.assertEqual(client.get("/health/live").json(), {"status": "alive"})
            response = client.get("/health/ready")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["database"], "not_configured")

        self.assertIsNone(app.state.engine)
        self.assertIsNone(app.state.session_factory)

    def test_invalid_environment_stops_startup(self) -> None:
        with patch.dict(os.environ, {"API_ENVIRONMENT": "invalid"}):
            with self.assertRaises(ValidationError):
                with TestClient(create_app()):
                    self.fail("Invalid configuration must stop startup")

    def test_invalid_or_partial_database_settings_are_rejected(self) -> None:
        invalid_settings = (
            {"DB_HOST": "localhost"},
            {"DB_HOST": ""},
            {"SQLALCHEMY_DATABASE_URI": "not-a-url-secret"},
            {"SQLALCHEMY_DATABASE_URI": "sqlite:///test.db"},
            {"pool_timeout": 0},
        )

        for values in invalid_settings:
            with self.subTest(fields=tuple(values)):
                with self.assertRaises(ValidationError) as caught:
                    DBSettings(**values)

                self.assertNotIn("not-a-url-secret", str(caught.exception))

    def test_password_is_preserved_without_being_exposed(self) -> None:
        settings = DBSettings(
            DB_HOST="localhost",
            DB_NAME="test",
            DB_USERNAME="test",
            DB_PASSWORD="secret@:/#value",
        )
        self.assertEqual(settings.url.password, "secret@:/#value")
        self.assertNotIn("secret@:/#value", repr(settings))
        self.assertNotIn("secret@:/#value", str(settings.url))

    def test_uri_takes_priority_over_separate_fields(self) -> None:
        settings = DBSettings(
            SQLALCHEMY_DATABASE_URI="postgresql+asyncpg://test:secret@localhost/uri_db",
            DB_NAME="ignored",
        )
        self.assertEqual(settings.url.database, "uri_db")
        self.assertNotIn("secret", repr(settings))

    def test_environment_takes_priority_over_dotenv(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            dotenv = Path(directory) / ".env"
            dotenv.write_text("API_ENVIRONMENT=production\n", encoding="utf-8")

            with patch.dict(os.environ, {"API_ENVIRONMENT": "test"}):
                self.assertEqual(APISettings(_env_file=dotenv).environment, "test")

    def test_creating_an_app_does_not_create_an_engine(self) -> None:
        with patch("src.application.create_db_engine") as create_engine:
            create_app()
            create_engine.assert_not_called()

    def test_unconfigured_database_does_not_create_a_pool(self) -> None:
        with patch("src.core.db.session.create_async_engine") as create_engine:
            self.assertIsNone(create_db_engine(DBSettings()))
            create_engine.assert_not_called()

    def test_readiness_and_pool_shutdown(self) -> None:
        engine = MagicMock(spec=AsyncEngine)
        engine.dispose = AsyncMock()
        connection = engine.connect.return_value.__aenter__.return_value
        connection.execute = AsyncMock()
        app = create_app()

        with patch("src.application.create_db_engine", return_value=engine):
            with TestClient(app) as client:
                response = client.get("/health/ready")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["database"], "available")
                self.assertEqual(str(connection.execute.await_args.args[0]), "SELECT 1")
                engine.dispose.assert_not_awaited()

        engine.dispose.assert_awaited_once()
        self.assertIsNone(app.state.engine)
        self.assertIsNone(app.state.session_factory)

    def test_database_failure_does_not_expose_details_or_stop_liveness(self) -> None:
        for error in (SQLAlchemyError, OSError, TimeoutError):
            with self.subTest(error=error.__name__):
                engine = MagicMock(spec=AsyncEngine)
                engine.dispose = AsyncMock()
                connection = engine.connect.return_value.__aenter__.return_value
                connection.execute = AsyncMock(side_effect=error("private-secret"))

                with patch("src.application.create_db_engine", return_value=engine):
                    with TestClient(create_app()) as client:
                        response = client.get("/health/ready")
                        self.assertEqual(response.status_code, 503)
                        self.assertEqual(response.json()["database"], "unavailable")
                        self.assertNotIn("private-secret", response.text)
                        self.assertEqual(client.get("/health/live").status_code, 200)

                engine.dispose.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
