import argparse
import asyncio
import os
import sys
from pathlib import Path

from asyncpg import PostgresError
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from src.api.accounts.domain.accounts import BootstrapPracticeInput
from src.api.accounts.domain.errors import PracticeAlreadyExists, UnknownTimeZone
from src.api.authorization.domain.errors import AccessDenied
from src.core import Err, Ok


async def create_practice(data: BootstrapPracticeInput):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.core.db.session import async_session_factory, engine

    try:
        async with async_session_factory() as db:
            return await bootstrap_practice(db, obj_in=data)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear una consulta independiente")
    parser.add_argument("--file", type=Path, required=True)
    arguments = parser.parse_args()

    try:
        data = BootstrapPracticeInput.model_validate_json(
            arguments.file.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, ValidationError):
        print("El archivo de alta no contiene una entrada válida", file=sys.stderr)
        return 2

    uri = os.environ.get("BOOTSTRAP_DATABASE_URI")
    if not uri:
        print("Configura BOOTSTRAP_DATABASE_URI con la identidad administrativa", file=sys.stderr)
        return 2

    try:
        url = make_url(uri)
        if (
            url.drivername != "postgresql+asyncpg"
            or not all((url.host, url.database, url.username, url.password))
            or (url.port is not None and not 1 <= url.port <= 65535)
        ):
            raise ValueError()
    except (ValueError, SQLAlchemyError):
        print("La conexión administrativa no es válida", file=sys.stderr)
        return 2

    try:
        from src.settings.oidc_settings import oidc_settings
    except ValidationError:
        print("La configuración OIDC no es válida", file=sys.stderr)
        return 2

    if not oidc_settings.issuer or data.owner_issuer != oidc_settings.issuer:
        print("El emisor debe coincidir exactamente con OIDC_ISSUER", file=sys.stderr)
        return 2

    # This standalone process selects its administrative URI before loading the
    # existing session factory. It never changes the API process or its config files.
    os.environ["SQLALCHEMY_DATABASE_URI"] = uri
    try:
        from src.core.db import DAOError
    except (ValidationError, SQLAlchemyError):
        print("La configuración de la base no es válida", file=sys.stderr)
        return 2

    try:
        result = asyncio.run(create_practice(data))
    except (DAOError, SQLAlchemyError, PostgresError, OSError, TimeoutError):
        print("No se pudo confirmar el alta; consulta el estado antes de repetir", file=sys.stderr)
        return 2

    match result:
        case Ok(practice):
            print(practice.model_dump_json(by_alias=True))
            return 0
        case Err(AccessDenied()):
            print("PERMISSION_DENIED", file=sys.stderr)
        case Err(PracticeAlreadyExists()):
            print("INDEPENDENT_PRACTICE_EXISTS", file=sys.stderr)
        case Err(UnknownTimeZone()):
            print("VALIDATION_ERROR", file=sys.stderr)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
