import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import asyncpg
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError, IntegrityError

ROOT = Path(__file__).resolve().parents[2]
DATABASE = f"nightingale_test_{uuid4().hex}"
MIGRATOR_PASSWORD = "Fixture-migrator-2026!"
APP_PASSWORD = "Fixture-app-2026!"


def database_url(username, password):
    return URL.create(
        "postgresql+asyncpg",
        username=username,
        password=password,
        host="127.0.0.1",
        port=55433,
        database=DATABASE,
    ).render_as_string(hide_password=False)


async def connect_admin():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=55433,
        user="nightingale_fixture",
        password="Fixture-postgres-only-2026!",
        database="postgres",
        timeout=10,
    )
    directory = await connection.fetchval("SHOW data_directory")
    expected = ROOT / ".tmp/test-services/postgres-test/data"

    if Path(directory).resolve() != expected.resolve():
        await connection.close()

        raise RuntimeError(
            "Refusing to use a PostgreSQL cluster outside the test folder"
        )

    return connection


async def prepare_database():
    admin = await connect_admin()

    try:
        roles = {
            "nightingale_runtime": "NOLOGIN",
            "nightingale_migrator": f"LOGIN PASSWORD '{MIGRATOR_PASSWORD}'",
            "nightingale_app": f"LOGIN PASSWORD '{APP_PASSWORD}' IN ROLE nightingale_runtime",
        }

        for name, options in roles.items():
            exists = await admin.fetchval(
                "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname=$1)", name
            )

            if not exists:
                await admin.execute(
                    f"CREATE ROLE {name} {options} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"
                )

        for name in roles:
            privileges = await admin.fetchrow(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=$1",
                name,
            )

            assert not any(privileges.values()), (
                "Fixture role has unexpected privileges"
            )

        assert await admin.fetchval(
            "SELECT pg_has_role('nightingale_app', 'nightingale_runtime', 'MEMBER')"
        )
        assert not await admin.fetchval(
            "SELECT pg_has_role('nightingale_app', 'nightingale_migrator', 'MEMBER')"
        )
        assert not await admin.fetchval(
            "SELECT pg_has_role('nightingale_migrator', 'nightingale_runtime', 'MEMBER')"
        )
        await admin.execute(f'CREATE DATABASE "{DATABASE}" OWNER nightingale_migrator')
        await admin.execute(f'REVOKE ALL ON DATABASE "{DATABASE}" FROM PUBLIC')
        await admin.execute(
            f'GRANT CONNECT ON DATABASE "{DATABASE}" TO nightingale_runtime'
        )
        await admin.execute(
            f'ALTER DATABASE "{DATABASE}" SET search_path=nightingale,public'
        )
    finally:
        await admin.close()


def migrate(
    *arguments, config=None, username="nightingale_migrator", password=MIGRATOR_PASSWORD
):
    environment = dict(os.environ)
    environment["ALEMBIC_DATABASE_URI"] = database_url(username, password)

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(config or ROOT / "alembic.ini"),
            *arguments,
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


async def check_migrations(directory):
    result = migrate("upgrade", "head")

    assert result.returncode == 0, result.stderr

    migrator = await asyncpg.connect(
        database_url("nightingale_migrator", MIGRATOR_PASSWORD).replace(
            "postgresql+asyncpg", "postgresql", 1
        )
    )

    try:
        assert (
            await migrator.fetchval("SELECT version_num FROM public.alembic_version")
            == "20261025_02"
        )
        assert (
            await migrator.fetchval(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='nightingale'"
            )
            == 9
        )

        # A failing revision must roll back both its DDL and its version update.
        shutil.copytree(ROOT / "migrations", directory / "migrations")
        (directory / "alembic.ini").write_text(
            f"[alembic]\nscript_location = {directory / 'migrations'}\n",
            encoding="utf-8",
        )
        (directory / "migrations/versions/failed_probe.py").write_text(
            'from alembic import op\nrevision="failed_probe"\ndown_revision="20261025_02"\n'
            'def upgrade():\n    op.execute("CREATE TABLE nightingale.failed_probe (id integer)")\n'
            '    op.execute("SELECT 1/0")\n',
            encoding="utf-8",
        )
        result = migrate("upgrade", "head", config=directory / "alembic.ini")
        assert result.returncode != 0, "Broken revision unexpectedly succeeded"
        assert (
            await migrator.fetchval("SELECT to_regclass('nightingale.failed_probe')")
            is None
        )
        assert (
            await migrator.fetchval("SELECT version_num FROM public.alembic_version")
            == "20261025_02"
        )

        result = migrate("downgrade", "base")
        assert result.returncode == 0, result.stderr
        assert await migrator.fetchval("SELECT to_regnamespace('nightingale')") is None
        result = migrate("upgrade", "head")
        assert result.returncode == 0, result.stderr
        await migrator.execute(
            "CREATE TABLE nightingale.transaction_probe (id integer PRIMARY KEY, value integer NOT NULL CHECK(value>=0))"
        )
        await migrator.execute(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON nightingale.transaction_probe TO nightingale_runtime"
        )
        await migrator.execute("INSERT INTO nightingale.transaction_probe VALUES (1,0)")
    finally:
        await migrator.close()


async def check_transactions():
    from sqlalchemy.orm import Mapped, mapped_column

    from src.api.health import ready
    from src.core.db import DAO
    from src.core.db.model import Base
    from src.core.db.session import async_session_factory, engine

    class TransactionProbe(Base):
        __tablename__ = "transaction_probe"
        __table_args__ = {"schema": "nightingale"}

        id: Mapped[int] = mapped_column(primary_key=True)
        value: Mapped[int]

    dao = DAO(TransactionProbe)

    try:
        async with async_session_factory() as db:
            assert await ready(db) == {"status": "ready", "database": "available"}

        async with async_session_factory() as db:
            try:
                async with db.begin():
                    await dao.create(db, obj_in={"id": 2, "value": 0}, commit=False)
                    await db.execute(
                        text(
                            "UPDATE nightingale.transaction_probe SET value=-1 WHERE id=1"
                        )
                    )
            except IntegrityError:
                pass
            else:
                raise AssertionError("Invalid write unexpectedly succeeded")

        async with async_session_factory() as db:
            assert (
                await db.scalar(
                    text("SELECT count(*) FROM nightingale.transaction_probe")
                )
                == 1
            )
            assert (
                await db.scalar(
                    text("SELECT value FROM nightingale.transaction_probe WHERE id=1")
                )
                == 0
            )
            assert (
                await db.scalar(text("SELECT current_setting('TimeZone')"))
                == "America/Caracas"
            )
            assert (await db.scalar(text("SELECT now()"))).utcoffset() is not None

        first_locked = asyncio.Event()
        second_started = asyncio.Event()
        release_first = asyncio.Event()
        writer_pids = {}

        async def first_writer():
            async with async_session_factory() as db:
                async with db.begin():
                    writer_pids["first"] = await db.scalar(
                        text("SELECT pg_backend_pid()")
                    )
                    await db.execute(
                        text(
                            "SELECT value FROM nightingale.transaction_probe WHERE id=1 FOR UPDATE"
                        )
                    )
                    await db.execute(
                        text(
                            "UPDATE nightingale.transaction_probe SET value=value+1 WHERE id=1"
                        )
                    )
                    first_locked.set()
                    await release_first.wait()

        async def second_writer():
            await first_locked.wait()

            async with async_session_factory() as db:
                async with db.begin():
                    await db.execute(text("SET LOCAL lock_timeout='5s'"))
                    writer_pids["second"] = await db.scalar(
                        text("SELECT pg_backend_pid()")
                    )
                    second_started.set()
                    value = await db.scalar(
                        text(
                            "SELECT value FROM nightingale.transaction_probe WHERE id=1 FOR UPDATE"
                        )
                    )
                    assert value == 1, "Writer did not observe the prior commit"
                    await db.execute(
                        text(
                            "UPDATE nightingale.transaction_probe SET value=value+1 WHERE id=1"
                        )
                    )

        async with asyncio.timeout(10), asyncio.TaskGroup() as writers:
            writers.create_task(first_writer())
            writers.create_task(second_writer())

            try:
                await second_started.wait()
                observer = await connect_admin()

                try:
                    assert writer_pids["first"] != writer_pids["second"]

                    async with asyncio.timeout(3):
                        while not await observer.fetchval(
                            "SELECT $1::integer = ANY(pg_blocking_pids($2::integer))",
                            writer_pids["first"],
                            writer_pids["second"],
                        ):
                            await asyncio.sleep(0.01)
                finally:
                    await observer.close()
            finally:
                release_first.set()

        async with async_session_factory() as db:
            assert (
                await db.scalar(
                    text("SELECT value FROM nightingale.transaction_probe WHERE id=1")
                )
                == 2
            )

            for statement in (
                "CREATE TABLE nightingale.forbidden (id integer)",
                "CREATE TABLE public.forbidden (id integer)",
                "SET LOCAL ROLE nightingale_migrator",
            ):
                try:
                    async with db.begin_nested():
                        await db.execute(text(statement))
                except DBAPIError as error:
                    assert error.orig.sqlstate == "42501", (
                        "Expected insufficient privilege"
                    )
                else:
                    raise AssertionError("Runtime identity has migration privileges")
    finally:
        await engine.dispose()


async def main():
    try:
        await prepare_database()

        with TemporaryDirectory(prefix="persistence-", dir=ROOT / ".tmp") as temporary:
            directory = Path(temporary).resolve()
            assert directory.is_relative_to(ROOT / ".tmp")
            await check_migrations(directory)

            for name in list(os.environ):
                if (
                    name.upper().startswith(("API_", "DB_", "POOL_"))
                    or name.upper() == "SQLALCHEMY_DATABASE_URI"
                ):
                    del os.environ[name]
            os.environ["SQLALCHEMY_DATABASE_URI"] = database_url(
                "nightingale_app", APP_PASSWORD
            )
            sys.path.insert(0, str(ROOT))
            previous_directory = Path.cwd()
            os.chdir(directory)

            try:
                await check_transactions()
            finally:
                os.chdir(previous_directory)
    finally:
        admin = await connect_admin()

        try:
            # The name is generated here; never accept an external database name.
            assert DATABASE.startswith("nightingale_test_") and len(DATABASE) == 49
            exists = await admin.fetchval(
                "SELECT EXISTS(SELECT FROM pg_database WHERE datname=$1)", DATABASE
            )

            if exists:
                await admin.execute(f'DROP DATABASE "{DATABASE}" WITH (FORCE)')
        finally:
            await admin.close()

    print(
        "PostgreSQL checks passed: migrations up/down, failed revision rollback, runtime DDL denied, write rollback and two coordinated writers."
    )


if __name__ == "__main__":
    asyncio.run(main())
