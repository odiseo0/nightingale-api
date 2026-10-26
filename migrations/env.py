import asyncio
import os

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


def run_migrations(connection: Connection):
    context.configure(connection=connection, version_table_schema="public")

    with context.begin_transaction():
        context.run_migrations()


async def run_online():
    uri = os.environ.get("ALEMBIC_DATABASE_URI")
    if not uri:
        raise RuntimeError("Set ALEMBIC_DATABASE_URI with the migration identity")

    try:
        url = make_url(uri)
    except (ArgumentError, ValueError):
        raise RuntimeError("Invalid migration database URI") from None
    if url.drivername != "postgresql+asyncpg":
        raise RuntimeError("Migrations require postgresql+asyncpg")

    # Migrations use their own identity, not the shared runtime engine.
    # https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    context.configure(
        dialect_name="postgresql", literal_binds=True, version_table_schema="public"
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_online())
