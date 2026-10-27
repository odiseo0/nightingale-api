import argparse
import asyncio
import json
import os
import sys

from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError


async def purge():
    from src.api.sync.application.sync_cases import purge_expired_results
    from src.core.db.session import async_session_factory, engine

    try:
        async with async_session_factory() as db:
            return await purge_expired_results(db)
    finally:
        await engine.dispose()


def main() -> int:
    argparse.ArgumentParser(description="Retirar lotes de resultados, grupos y capturas vencidos; conservar recibos, historia y auditoría").parse_args()
    uri = os.environ.get("MAINTENANCE_DATABASE_URI", "")
    try:
        url = make_url(uri)
        if url.drivername != "postgresql+asyncpg" or not all((url.host, url.database, url.username, url.password)) or (url.port is not None and not 1 <= url.port <= 65535):
            raise ValueError()
    except (ValueError, SQLAlchemyError):
        print("La conexión de mantenimiento no es válida", file=sys.stderr)
        return 2

    os.environ["SQLALCHEMY_DATABASE_URI"] = uri
    try:
        from src.core import Err, Ok
        from src.core.db import DAOError
    except (ValidationError, SQLAlchemyError):
        print("La configuración de la base no es válida", file=sys.stderr)
        return 2
    try:
        result = asyncio.run(purge())
    except (ValidationError, SQLAlchemyError, DAOError, OSError, TimeoutError):
        print("No se pudo confirmar el mantenimiento; comprueba el estado antes de repetir", file=sys.stderr)
        return 2
    match result:
        case Ok(count):
            print(json.dumps({"purgedResults": count}))
            return 0
        case Err():
            print("PERMISSION_DENIED", file=sys.stderr)
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
