import asyncio
import json
import os
import runpy
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid7

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[2]
accounts = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/accounts/check.py")))
access = accounts.access
postgres = accounts.postgres


async def check_sync(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.sync.repository.dao import dao_changes
    from src.api.sync.application import operations_cases
    from src.core import Ok
    from src.core.services.oidc import verify_identity

    installations = [await access.issue(client, token["access_token"]) for token in tokens]
    owner, assistant, outsider = installations
    identity = await verify_identity(tokens[0]["access_token"])
    assert isinstance(identity, Ok)
    result = await accounts.call(administrative, bootstrap_practice, BootstrapPracticeInput(
        owner_issuer=identity.value["issuer"], owner_subject=identity.value["subject"],
        owner_name="Fixture Owner", professional_name="Fixture Professional",
        display_name="Fixture Practice", time_zone="America/Caracas", location_name="Fixture Office",
        location_address="Fictional address", location_country="VE", location_state="Fixture State", location_city="Fixture City",
    ))
    assert isinstance(result, Ok)
    account_id = result.value.account_id
    base = f"/v1/accounts/{account_id}/sync/operations"

    async def counts():
        async with administrative() as db:
            row = (await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.account_device_accesses),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log),
                    last_sequence,permission_epoch FROM nightingale.account_sync_heads WHERE account_id=:id
            """), {"id": account_id})).one()
            return tuple(row)

    def operation(installation=owner, **changes):
        return {
            "operationId": str(uuid7()), "contractVersion": 1,
            "action": "RegisterAccountDevice", "entityKey": installation["deviceId"],
            "expectedVersion": 0, "payload": {}, **changes,
        }

    async def submit(items, installation=owner, status=200):
        response = await client.post(base, json={"operations": items}, headers=access.authorization(installation))
        access.expect(response, status)
        assert response.headers["Cache-Control"] == "no-store"
        if status == 200:
            assert response.json()["correlationId"] == response.headers["X-Correlation-ID"]
            return response.json()["results"]
        return response

    first = operation()
    before = await counts()
    assert before == (0, 0, 0, 0, 0, 1)
    await submit([first], outsider, 404)
    await submit([operation(entityKey=outsider["deviceId"])], owner, 403)
    assert await counts() == before

    # Two separate HTTP requests and database sessions must confirm one effect.
    concurrent = await asyncio.gather(submit([first]), submit([first]))
    assert sorted(item[0]["status"] for item in concurrent) == ["accepted", "duplicate"]
    accepted = next(item[0] for item in concurrent if item[0]["status"] == "accepted")
    assert accepted["state"]["deviceId"] == owner["deviceId"] and accepted["entityVersion"] == 1
    assert "originalResult" not in accepted
    assert await counts() == (1, 1, 1, 1, 1, 2)
    duplicate = (await submit([dict(first, dependsOn=[], occurredAtLocal=None)]))[0]
    assert duplicate["status"] == "duplicate" and duplicate["originalResult"] == accepted
    assert "originalResult" not in duplicate["originalResult"]
    different = (await submit([dict(first, expectedVersion=1)]))[0]
    assert different["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    response = await client.get(base + "/" + first["operationId"], headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json() == accepted
    await submit([operation(expectedVersion=4)])
    conflict = (await submit([operation(expectedVersion=4)]))[0]
    assert conflict["status"] == "conflict" and conflict["entityVersion"] == 1
    no_change = (await submit([operation()]))[0]
    assert no_change["error"]["code"] == "NO_CHANGES"
    # Raw invalid payload is hashed, while the receipt contains only a safe error.
    invalid = operation(payload={"untrusted": "fictional-private-value"})
    rejected = (await submit([invalid]))[0]
    assert rejected["error"]["code"] == "VALIDATION_ERROR"
    assert rejected["error"]["details"] == []
    repeated = (await submit([invalid]))[0]
    assert repeated["status"] == "duplicate" and repeated["originalResult"] == rejected
    assert "fictional-private-value" not in json.dumps(repeated)
    distinct = (await submit([dict(invalid, payload={"untrusted": " fictional-private-value "})]))[0]
    assert distinct["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    unsupported = operation(action="FutureOperation", entityKey=str(account_id), expectedVersion=1, payload={"noShowGraceMinutes": 20})
    results = await submit([unsupported, operation(dependsOn=[unsupported["operationId"]]), operation()])
    assert [item["error"]["code"] for item in results] == ["UNSUPPORTED_OPERATION", "DEPENDENCY_FAILED", "NO_CHANGES"]

    before = await counts()
    forward = operation()
    for items in ([first, first], [operation(dependsOn=[forward["operationId"]]), forward], []):
        await submit(items, status=422)
    await submit([operation() for _ in range(101)], status=422)
    await submit([operation(payload={"value": "x" * 65536})], status=413)
    response = await client.post(base, content=b" " * (1024 * 1024) + b"{}", headers={**access.authorization(owner), "Content-Type": "application/json"})
    access.expect(response, 413)
    assert await counts() == before

    # Add a member as a fixture; invitations remain T10 work.
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at)
                VALUES (:account,:user,clock_timestamp(),clock_timestamp())
            """), {"account": account_id, "user": UUID(assistant["userId"])})
    assistant_op = operation(assistant)
    before = await counts()
    original_append = dao_changes.append

    async def fail_real_constraint(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)

    with patch.object(dao_changes, "append", side_effect=fail_real_constraint):
        failure = (await submit([assistant_op], assistant))[0]
        assert failure["status"] == "retryable_failure"
    assert await counts() == before
    retried = (await submit([assistant_op], assistant))[0]
    assert retried["status"] == "accepted"
    assert await counts() == tuple(value + delta for value, delta in zip(before, (1, 1, 1, 1, 1, 1)))
    response = await client.get(base + "/" + first["operationId"], headers=access.authorization(assistant))
    access.expect(response, 404)

    # A failure at deferred commit also reverts the effect, receipt, audit and head.
    deferred_device = await access.issue(client, tokens[0]["access_token"])
    deferred_op = operation(deferred_device)
    before = await counts()

    async def fail_deferred_constraint(db, values, **kwargs):
        return await original_append(db, {**values, "group_size": 2}, **kwargs)

    with patch.object(dao_changes, "append", side_effect=fail_deferred_constraint):
        failure = (await submit([deferred_op], deferred_device))[0]
        assert failure["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit([deferred_op], deferred_device))[0]["status"] == "accepted"

    independent_device = await access.issue(client, tokens[0]["access_token"])
    transient = operation(independent_device)
    dependent = operation(independent_device, dependsOn=[transient["operationId"]])
    independent = operation(independent_device)
    attempts = 0

    async def fail_once(db, values, **kwargs):
        nonlocal attempts
        attempts += 1
        return await original_append(db, {**values, "ordinal": 0} if attempts == 1 else values, **kwargs)

    before = await counts()
    with patch.object(dao_changes, "append", side_effect=fail_once):
        results = await submit([transient, dependent, independent], independent_device)
    assert [item["status"] for item in results] == ["retryable_failure", "retryable_failure", "accepted"]
    assert await counts() == tuple(value + 1 for value in before)
    assert (await submit([dependent], independent_device))[0]["error"]["code"] == "DEPENDENCY_FAILED"

    # Discard a completed response at the ASGI transport boundary, after commit.
    another = await access.issue(client, tokens[0]["access_token"])
    lost = operation(another)
    # It cannot recover another installation's receipt until registration.
    await submit([first], another, 403)
    original_submit = operations_cases.submit_batch

    async def lose_response(*args, **kwargs):
        await original_submit(*args, **kwargs)
        raise ConnectionResetError("Fixture response dropped after commit")

    from src.api.sync.infrastructure import operations_api
    with patch.object(operations_api, "submit_batch", side_effect=lose_response):
        try:
            await submit([lost], another)
        except ConnectionResetError:
            pass
        else:
            raise AssertionError("Response was not lost")
    recovered = (await submit([lost], another))[0]
    assert recovered["status"] == "duplicate" and recovered["originalResult"]["status"] == "accepted"
    response = await client.get(base + "/" + first["operationId"], headers=access.authorization(another))
    access.expect(response, 200)
    assert response.json() == accepted
    from_new = (await submit([first], another))[0]
    assert from_new["status"] == "duplicate"

    # Wait on a real row lock, then re-read the revocation committed by its owner.
    before = await counts()
    async with administrative() as db:
        async with db.begin():
            blocker = await db.scalar(text("SELECT pg_backend_pid()"))
            await db.execute(text("SELECT account_id FROM nightingale.account_sync_heads WHERE account_id=:id FOR UPDATE"), {"id": account_id})
            pending = asyncio.create_task(submit([first], status=403))
            blocked = False
            for _ in range(100):
                blocked = await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE :pid=ANY(pg_blocking_pids(pid)))"), {"pid": blocker})
                if blocked:
                    break
                await asyncio.sleep(0.02)
            assert blocked, "The retry did not wait on the account control"
            await db.execute(text("""
                UPDATE nightingale.account_device_accesses SET status='revoked',version=version+1,updated_at=clock_timestamp()
                WHERE account_id=:account AND device_id=:device
            """), {"account": account_id, "device": UUID(owner["deviceId"])})
    await asyncio.wait_for(pending, timeout=10)
    await submit([first], status=403)
    response = await client.get(base + "/" + first["operationId"], headers=access.authorization(owner))
    access.expect(response, 403)
    assert await counts() == before

    # Aged receipts are fixtures; runtime has no history-editing grants.
    expired = operation(action="FutureOperation")
    from datetime import timedelta
    from src.api.sync.repository.dao import dao_heads
    async with administrative() as db:
        old = await dao_heads.get_server_time(db) - timedelta(days=91)
    with patch.object(dao_heads, "get_server_time", return_value=old):
        assert (await submit([expired], another))[0]["status"] == "rejected"
    await submit([expired], another, 410)
    assert (await submit([dict(expired, expectedVersion=1)], another))[0]["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    # The same operation key belongs to a separate account namespace.
    outside_identity = await verify_identity(tokens[2]["access_token"])
    other = await accounts.call(administrative, bootstrap_practice, BootstrapPracticeInput(
        owner_issuer=outside_identity.value["issuer"], owner_subject=outside_identity.value["subject"],
        owner_name="Fixture Other Owner", professional_name="Fixture Other Professional",
        display_name="Fixture Other Practice", time_zone="America/Caracas", location_name="Fixture Other Office",
        location_address="Fictional address", location_country="VE", location_state="Fixture State", location_city="Fixture City",
    ))
    assert isinstance(other, Ok)
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at)
                VALUES (:account,:user,clock_timestamp(),clock_timestamp())
            """), {"account": other.value.account_id, "user": UUID(owner["userId"])})
    other_base = f"/v1/accounts/{other.value.account_id}/sync/operations"
    response = await client.post(other_base, json={"operations": [first]}, headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["results"][0]["status"] == "accepted"
    response = await client.get(base + "/" + first["operationId"], headers=access.authorization(outsider))
    access.expect(response, 404)
    response = await client.get(base + "/" + expired["operationId"], headers=access.authorization(another))
    access.expect(response, 410)
    assert response.json()["code"] == "RESULT_EXPIRED"

    async with administrative() as db:
        async with db.begin():
            assert await db.scalar(text("SELECT count(*) FROM nightingale.operation_receipts WHERE operation_id=:id"), {"id": UUID(first["operationId"])}) == 2
            row = (await db.execute(text("SELECT result_json,request_hash FROM nightingale.operation_receipts WHERE account_id=:account AND operation_id=:id"), {"account": account_id, "id": UUID(first["operationId"])})).one()
            assert row.request_hash and len(row.request_hash) == 32
            assert not {"tokenHash", "accessToken", "payload"} & set(row.result_json)
            assert (await db.execute(text("SELECT count(*) FROM nightingale.change_log WHERE audience<>'owner'"))).scalar() == 0

    from sqlalchemy.exc import DBAPIError
    for factory, statement in (
        (runtime, "UPDATE nightingale.operation_receipts SET action='Altered'"),
        (runtime, "DELETE FROM nightingale.audit_events"),
        (runtime, "UPDATE nightingale.change_log SET ordinal=2"),
        (administrative, "UPDATE nightingale.operation_receipts SET action='Altered'"),
        (administrative, "UPDATE nightingale.audit_events SET outcome='rejected'"),
        (administrative, "UPDATE nightingale.operation_receipts SET result_json=NULL,purged_at=clock_timestamp()+interval '100 days'"),
        (administrative, "UPDATE nightingale.account_sync_heads SET last_sequence=last_sequence+1"),
        (administrative, "UPDATE nightingale.account_sync_heads SET permission_epoch=1"),
    ):
        try:
            async with factory() as db:
                async with db.begin():
                    await db.execute(text(statement))
        except DBAPIError:
            pass
        else:
            raise AssertionError("Invalid operation history was committed")
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("UPDATE nightingale.operation_receipts SET result_json=NULL,purged_at=clock_timestamp() WHERE operation_id=:id"), {"id": UUID(expired["operationId"])})
    await submit([expired], another, 410)
    assert (await submit([dict(expired, expectedVersion=1)], another))[0]["error"]["code"] == "IDEMPOTENCY_CONFLICT"


async def main(check=check_sync):
    realm = json.loads((ROOT / "test-support/oidc/realm.json").read_text())
    tokens = [access.provider_tokens(user) for user in realm["users"]]
    engine = None
    admin_engine = None
    try:
        await postgres.prepare_database()
        result = postgres.migrate("upgrade", "head")
        assert result.returncode == 0, result.stderr
        with TemporaryDirectory(prefix="sync-", dir=ROOT / ".tmp") as temporary:
            for name in list(os.environ):
                if name.upper().startswith(("API_", "OIDC_", "DB_", "POOL_")) or name.upper() == "SQLALCHEMY_DATABASE_URI":
                    del os.environ[name]
            os.environ.update({
                "API_ENVIRONMENT": "test", "SQLALCHEMY_DATABASE_URI": postgres.database_url("nightingale_app", postgres.APP_PASSWORD),
                "OIDC_ISSUER": access.oidc.ISSUER, "OIDC_JWKS_URI": f"{access.oidc.ISSUER}/protocol/openid-connect/certs",
                "OIDC_TLS_CA_FILE": str(access.CERTIFICATE),
            })
            sys.path.insert(0, str(ROOT))
            previous = Path.cwd()
            os.chdir(temporary)
            from src.application import app
            from src.core.db.session import async_session_factory, engine
            admin_engine = create_async_engine(postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD))
            administrative = async_sessionmaker(admin_engine, expire_on_commit=False)
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://fixture") as client:
                    await check(async_session_factory, administrative, client, tokens)
            finally:
                await admin_engine.dispose()
                admin_engine = None
                await engine.dispose()
                engine = None
                os.chdir(previous)
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
    if check is check_sync:
        print("Operation checks passed: real PostgreSQL/Keycloak, concurrent duplicate, atomic rollback, lost response, current access and independent batch results.")


if __name__ == "__main__":
    asyncio.run(main())
