import asyncio
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


ROOT = Path(__file__).resolve().parents[2]
access = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/access/check.py")))
postgres = access.postgres


async def call(factory, case, *args, **kwargs):
    async with factory() as db:
        return await case(db, *args, **kwargs)


async def check_script(directory, runtime):
    from src.api.accounts.repository.models import Account

    source = Path(directory) / "script-practice.json"
    data = {
        "ownerIssuer": access.oidc.ISSUER,
        "ownerSubject": "fixture-script-owner",
        "ownerName": "Fixture Script Owner",
        "professionalName": "Fixture Script Professional",
        "displayName": "Fixture Script Practice",
        "timeZone": "America/Caracas",
        "locationName": "Fixture Office",
        "locationAddress": "Fictional address",
        "locationState": "Fixture State",
        "locationCity": "Fixture City",
    }
    source.write_text(json.dumps(data), encoding="utf-8")
    original_runtime_uri = os.environ["SQLALCHEMY_DATABASE_URI"]

    async def run(uri):
        environment = dict(os.environ)
        environment.update({
            "PYTHONPATH": str(ROOT),
            "BOOTSTRAP_DATABASE_URI": uri,
            "SQLALCHEMY_DATABASE_URI": "postgresql+asyncpg://fixture:fixture-private-runtime@127.0.0.1:1/ignored",
        })
        return await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "scripts.create_practice", "--file", str(source)],
            cwd=directory, env=environment, capture_output=True, text=True, timeout=20,
        )

    async with runtime() as db:
        before = await db.scalar(select(func.count()).select_from(Account))
    administrative_uri = postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD)
    created = await run(administrative_uri)
    assert created.returncode == 0, created.stderr
    output = json.loads(created.stdout)
    assert set(output) == {"userId", "accountId", "professionalId"}
    assert all(UUID(value).version == 7 for value in output.values())
    duplicate = await run(administrative_uri)
    assert duplicate.returncode == 2 and duplicate.stderr.strip() == "INDEPENDENT_PRACTICE_EXISTS"

    data["ownerSubject"] = "fixture-script-denied"
    source.write_text(json.dumps(data), encoding="utf-8")
    denied = await run(postgres.database_url("nightingale_app", postgres.APP_PASSWORD))
    assert denied.returncode == 2 and denied.stderr.strip() == "PERMISSION_DENIED"
    data["timeZone"] = "Fixture/Unknown"
    source.write_text(json.dumps(data), encoding="utf-8")
    invalid = await run(administrative_uri)
    assert invalid.returncode == 2 and invalid.stderr.strip() == "VALIDATION_ERROR"

    bad_password = await run(postgres.database_url("nightingale_migrator", "fixture-private-bad-password"))
    unavailable = await run("postgresql+asyncpg://fixture:fixture-private-network@127.0.0.1:1/fixture")
    for result in (bad_password, unavailable):
        assert result.returncode == 2 and result.stdout == ""
        assert "Traceback" not in result.stderr and "fixture-private" not in result.stderr
    assert os.environ["SQLALCHEMY_DATABASE_URI"] == original_runtime_uri
    async with runtime() as db:
        assert await db.scalar(select(func.count()).select_from(Account)) == before + 1
        assert await db.get(Account, UUID(output["accountId"])) is not None


async def check_accounts(runtime, administrative, client, tokens):
    from src.api.accounts.application import accounts_cases as cases
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.accounts.domain.errors import (
        AccountNotFound, PracticeAlreadyExists, ProfessionalNotFound, UnknownTimeZone,
    )
    from src.api.accounts.repository.models import Account, AccountMembership, AccountProfessional, Professional
    from src.api.authorization.application.authorization_cases import get_devices
    from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
    from src.api.authorization.repository.models import AppUser
    from src.api.sync.repository.dao import dao_heads
    from src.api.sync.repository.models import AccountSyncHead
    from src.api.sync.application.sync_cases import get_permission_epoch
    from src.core import Err, Ok
    from src.core.db import DAOIntegrityError
    from src.core.services.oidc import verify_identity

    identities = []
    installations = []
    for token in tokens:
        result = await verify_identity(token["access_token"])
        assert isinstance(result, Ok)
        identities.append(result.value)
        installations.append(await access.issue(client, token["access_token"]))

    owner, assistant, outsider = installations
    secrets = [installation["accessToken"] for installation in installations]

    def data(index=0, subject=None, zone="America/Caracas"):
        identity = identities[index]
        return BootstrapPracticeInput(
            owner_issuer=identity["issuer"],
            owner_subject=subject or identity["subject"],
            owner_name="Fixture Owner",
            professional_name="Fixture Professional",
            display_name="Fixture Practice",
            time_zone=zone,
            location_name="Fixture Office",
            location_address="Fictional address",
            location_country="VE",
            location_state="Fixture State",
            location_city="Fixture City",
        )

    async def counts():
        async with administrative() as db:
            return [await db.scalar(select(func.count()).select_from(model)) for model in (
                AppUser, Account, AccountMembership, Professional, AccountProfessional, AccountSyncHead,
            )]

    for credential in secrets:
        result = await call(runtime, cases.get_accounts, credential)
        assert isinstance(result, Ok) and result.value.total == 0
    before = await counts()
    denied = await call(runtime, cases.bootstrap_practice, data())
    assert isinstance(denied, Err) and isinstance(denied.error, AccessDenied)
    invalid = await call(administrative, cases.bootstrap_practice, data(zone="Fixture/Unknown"))
    assert isinstance(invalid, Err) and isinstance(invalid.error, UnknownTimeZone)
    assert await counts() == before

    result = await call(administrative, cases.bootstrap_practice, data())
    assert isinstance(result, Ok)
    practice = result.value
    assert str(practice.user_id) == owner["userId"]
    assert await counts() == [3, 1, 1, 1, 1, 1]
    duplicate = await call(administrative, cases.bootstrap_practice, data())
    assert isinstance(duplicate, Err) and isinstance(duplicate.error, PracticeAlreadyExists)
    assert await counts() == [3, 1, 1, 1, 1, 1]

    missing_registration = await call(runtime, cases.get_account, secrets[0], practice.account_id)
    assert isinstance(missing_registration, Err) and isinstance(missing_registration.error, AccessDenied)
    own_access = await call(runtime, cases.get_access, secrets[0], practice.account_id)
    assert isinstance(own_access, Ok)
    assert own_access.value.role == "owner" and own_access.value.status == "registration_required"
    assert own_access.value.permission_epoch == 1 and own_access.value.allowed_actions == []
    hidden = await call(runtime, cases.get_account, secrets[2], practice.account_id)
    assert isinstance(hidden, Err) and isinstance(hidden.error, AccountNotFound)
    professional = await call(runtime, cases.get_professional, secrets[0])
    assert isinstance(professional, Ok) and professional.value.id == practice.professional_id
    missing_professional = await call(runtime, cases.get_professional, secrets[1])
    assert isinstance(missing_professional, Err) and isinstance(missing_professional.error, ProfessionalNotFound)

    second = await call(administrative, cases.bootstrap_practice, data(2))
    assert isinstance(second, Ok)
    other_account = second.value.account_id
    # These grants are test fixtures, not implemented invitations or device operations.
    async with administrative() as db:
        async with db.begin():
            await db.execute(text(
                "INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at) "
                "VALUES (:account,:user,clock_timestamp(),clock_timestamp())"
            ), [{"account": practice.account_id, "user": UUID(assistant["userId"])},
                {"account": other_account, "user": UUID(owner["userId"])}])
            await db.execute(text(
                "INSERT INTO nightingale.account_device_accesses "
                "(account_id,device_id,user_id,created_by_user_id,changed_by_user_id,created_at,updated_at) "
                "VALUES (:account,:device,:user,:creator,:creator,clock_timestamp(),clock_timestamp())"
            ), [
                {"account": practice.account_id, "device": UUID(row["deviceId"]),
                 "user": UUID(row["userId"]), "creator": practice.user_id}
                for row in (owner, assistant)
            ] + [
                {"account": other_account, "device": UUID(outsider["deviceId"]),
                 "user": UUID(outsider["userId"]), "creator": second.value.user_id}
            ])

    first_page = await call(runtime, cases.get_accounts, secrets[0], page=1, shows=1)
    second_page = await call(runtime, cases.get_accounts, secrets[0], page=2, shows=1)
    empty_page = await call(runtime, cases.get_accounts, secrets[0], page=3, shows=1)
    assert all(isinstance(result, Ok) and result.value.total == 2 for result in (first_page, second_page, empty_page))
    assert [first_page.value.items[0].id, second_page.value.items[0].id] == sorted([practice.account_id, other_account])
    assert empty_page.value.items == []
    assistant_page = await call(runtime, cases.get_accounts, secrets[1])
    assert isinstance(assistant_page, Ok) and assistant_page.value.total == 1
    assert assistant_page.value.items[0].role == "assistant"
    own = await call(runtime, cases.get_account, secrets[0], practice.account_id)
    shared = await call(runtime, cases.get_account, secrets[1], practice.account_id)
    assert isinstance(own, Ok) and isinstance(shared, Ok)
    assert own.value.id == shared.value.id == practice.account_id
    me = await call(runtime, cases.get_me, secrets[0])
    assert isinstance(me, Ok) and me.value.accounts.total == 2
    assert me.value.oidc_subject == identities[0]["subject"]
    assert set(me.value.model_dump(by_alias=True)["accounts"]) == {"items", "total"}

    await access.issue(client, tokens[0]["access_token"])
    devices = await call(runtime, get_devices, secrets[0], page=1, shows=1)
    next_devices = await call(runtime, get_devices, secrets[0], page=2, shows=1)
    assert isinstance(devices, Ok) and isinstance(next_devices, Ok)
    assert devices.value.total == next_devices.value.total == 2
    assert devices.value.items[0].id != next_devices.value.items[0].id
    assert all(str(row.user_id) == owner["userId"] for row in devices.value.items + next_devices.value.items)

    async with administrative() as db:
        async with db.begin():
            await db.execute(text(
                "UPDATE nightingale.accounts SET status='inactive',version=version+1,updated_at=clock_timestamp() WHERE id=:id"
            ), {"id": other_account})
            await db.execute(text(
                "UPDATE nightingale.account_device_accesses SET status='revoked',version=version+1,updated_at=clock_timestamp() "
                "WHERE account_id=:account AND device_id=:device"
            ), {"account": practice.account_id, "device": UUID(assistant["deviceId"])})
            await db.execute(text(
                "UPDATE nightingale.account_sync_heads SET permission_epoch=permission_epoch+1,updated_at=clock_timestamp() WHERE account_id=:id"
            ), {"id": practice.account_id})
    owner_page = await call(runtime, cases.get_accounts, secrets[0])
    outsider_page = await call(runtime, cases.get_accounts, secrets[2])
    assert owner_page.value.total == outsider_page.value.total == 1
    assert owner_page.value.items[0].id == practice.account_id
    assert outsider_page.value.items[0].status == "inactive"
    revoked = await call(runtime, cases.get_account, secrets[1], practice.account_id)
    assert isinstance(revoked, Err) and isinstance(revoked.error, AccessDenied)
    state = await call(runtime, cases.get_access, secrets[1], practice.account_id)
    assert isinstance(state, Ok) and state.value.status == "revoked" and state.value.permission_epoch == 2
    inactive = await call(runtime, cases.get_access, secrets[2], other_account)
    assert isinstance(inactive, Ok) and inactive.value.status == "inactive"

    async with runtime() as db:
        cached_head = await db.get(AccountSyncHead, practice.account_id)
        assert cached_head.permission_epoch == 2
        async with administrative() as writer:
            async with writer.begin():
                await writer.execute(text(
                    "UPDATE nightingale.account_sync_heads SET permission_epoch=permission_epoch+1,updated_at=clock_timestamp() WHERE account_id=:id"
                ), {"id": practice.account_id})
        refreshed = await get_permission_epoch(db, practice.account_id)
        assert refreshed.value == cached_head.permission_epoch == 3

    before = await counts()
    original_add = dao_heads.add

    async def invalid_head(db, head, **kwargs):
        head.permission_epoch = 0
        return await original_add(db, head, **kwargs)

    with patch.object(dao_heads, "add", side_effect=invalid_head):
        try:
            await call(administrative, cases.bootstrap_practice, data(subject="fixture-rollback-owner"))
        except DAOIntegrityError as error:
            assert error.__cause__.orig.sqlstate == "23514"
        else:
            raise AssertionError("Invalid sync head was committed")
    assert await counts() == before
    retry = await call(administrative, cases.bootstrap_practice, data(subject="fixture-rollback-owner"))
    assert isinstance(retry, Ok)
    results = await asyncio.gather(*(
        call(administrative, cases.bootstrap_practice, data(subject="fixture-race-owner")) for _ in range(2)
    ))
    assert sum(isinstance(result, Ok) for result in results) == 1
    assert sum(isinstance(result, Err) and isinstance(result.error, PracticeAlreadyExists) for result in results) == 1

    response = await client.post(
        f"/v1/me/devices/{owner['deviceId']}/revoke", headers=access.authorization(owner),
    )
    access.expect(response, 204)
    invalid = await call(runtime, cases.get_accounts, secrets[0])
    assert isinstance(invalid, Err) and isinstance(invalid.error, InvalidCredential)


async def main():
    realm = json.loads((ROOT / "test-support/oidc/realm.json").read_text())
    tokens = [access.provider_tokens(user) for user in realm["users"]]
    admin_engine = None
    engine = None
    try:
        await postgres.prepare_database()
        result = postgres.migrate("upgrade", "20261025_02")
        assert result.returncode == 0, result.stderr
        with TemporaryDirectory(prefix="accounts-", dir=ROOT / ".tmp") as temporary:
            for name in list(os.environ):
                if name.upper().startswith(("API_", "OIDC_", "DB_", "POOL_")) or name.upper() == "SQLALCHEMY_DATABASE_URI":
                    del os.environ[name]
            os.environ.update({
                "API_ENVIRONMENT": "test",
                "SQLALCHEMY_DATABASE_URI": postgres.database_url("nightingale_app", postgres.APP_PASSWORD),
                "OIDC_ISSUER": access.oidc.ISSUER,
                "OIDC_JWKS_URI": f"{access.oidc.ISSUER}/protocol/openid-connect/certs",
                "OIDC_TLS_CA_FILE": str(access.CERTIFICATE),
            })
            sys.path.insert(0, str(ROOT))
            previous_directory = Path.cwd()
            os.chdir(temporary)
            from src.application import app
            from src.core.db.session import async_session_factory, engine

            admin_engine = create_async_engine(postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD))
            administrative = async_sessionmaker(admin_engine, expire_on_commit=False)
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://fixture") as client:
                    await check_accounts(async_session_factory, administrative, client, tokens)
                await check_script(temporary, async_session_factory)
            finally:
                await admin_engine.dispose()
                admin_engine = None
                await engine.dispose()
                engine = None
                os.chdir(previous_directory)
    finally:
        if admin_engine is not None:
            await admin_engine.dispose()
        if engine is not None:
            await engine.dispose()
        admin = await postgres.connect_admin()
        try:
            assert postgres.DATABASE.startswith("nightingale_test_") and len(postgres.DATABASE) == 49
            if await admin.fetchval("SELECT EXISTS(SELECT FROM pg_database WHERE datname=$1)", postgres.DATABASE):
                await admin.execute(f'DROP DATABASE "{postgres.DATABASE}" WITH (FORCE)')
        finally:
            await admin.close()

    print("Account checks passed: real OIDC/PostgreSQL, atomic bootstrap, scoped pages, concurrent duplicate, rollback and administrative script.")


if __name__ == "__main__":
    asyncio.run(main())
