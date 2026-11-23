import argparse
import asyncio
import os
import sys
from pathlib import Path

from asyncpg import PostgresError
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from src.api.vademecum.domain.errors import VademecumImportError
from src.core import Err, Ok


async def import_file(content: bytes):
    from src.api.vademecum.application.import_cases import import_vademecum
    from src.core.db.session import async_session_factory, engine

    try:
        async with async_session_factory() as db:
            return await import_vademecum(db, content)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Importar un release del vademecum")
    parser.add_argument("--file", type=Path, required=True)
    arguments = parser.parse_args()

    try:
        content = arguments.file.read_bytes()
    except OSError:
        print("No se pudo leer el archivo del vademecum", file=sys.stderr)
        return 2

    uri = os.environ.get("VADEMECUM_IMPORT_DATABASE_URI")
    if not uri:
        print(
            "Configura VADEMECUM_IMPORT_DATABASE_URI con la identidad administrativa",
            file=sys.stderr,
        )
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

    os.environ["SQLALCHEMY_DATABASE_URI"] = uri
    try:
        from src.core.db import DAOError
    except (ValidationError, SQLAlchemyError):
        print("La configuración de la base no es válida", file=sys.stderr)
        return 2

    try:
        result = asyncio.run(import_file(content))
    except (DAOError, SQLAlchemyError, PostgresError, OSError, TimeoutError):
        print(
            "No se pudo confirmar la importación; consulta el estado antes de repetir",
            file=sys.stderr,
        )
        return 2

    match result:
        case Ok(summary):
            print(summary.model_dump_json(by_alias=True))
            return 0
        case Err(VademecumImportError()):
            print("VALIDATION_ERROR", file=sys.stderr)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
