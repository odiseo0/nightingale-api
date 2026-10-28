import asyncio
import json
import os
import runpy
import secrets
import socket
import subprocess
import sys
import time
from contextlib import AsyncExitStack
from pathlib import Path
from uuid import UUID, uuid7

import httpx
import asyncpg
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]
postgres = support["postgres"]


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


async def event(lines, kind, timeout=22):
    async with asyncio.timeout(timeout):
        fields = {}
        async for line in lines:
            if not line:
                if fields.get("event") == kind:
                    fields["receivedAt"] = time.perf_counter()
                    if "data" in fields:
                        fields["data"] = json.loads(fields["data"])
                    return fields
                fields = {}
            elif not line.startswith(":"):
                key, _, value = line.partition(":")
                fields[key] = value.lstrip(" ")
        raise AssertionError("Stream ended before the expected event: " + kind)


async def start_apis(stack, evidence, *, instrumented=False):
    processes = []
    clients = []
    for number in range(2):
        port = free_port()
        log = stack.enter_context((evidence / f"api-{number}.log").open("w", encoding="utf-8"))
        command = ([sys.executable, str(ROOT / "test-support/events/api_process.py"), str(port)] if instrumented else
                   [sys.executable, "-m", "uvicorn", "src.application:app", "--host", "127.0.0.1", "--port", str(port),
                    "--no-access-log", "--log-level", "warning"])
        environment = {**os.environ, "PYTHONPATH": str(ROOT)}
        if instrumented:
            environment["FIXTURE_COMMIT_EVIDENCE"] = str(evidence / f"commits-{number}.jsonl")
        process = subprocess.Popen(
            command, cwd=Path.cwd(), env=environment,
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        processes.append(process)

        def stop(process=process):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

        stack.callback(stop)
        client = await stack.enter_async_context(httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=25, trust_env=False))
        clients.append(client)
        for _ in range(150):
            assert process.poll() is None, "API process stopped; inspect its local test log"
            try:
                ready = await client.get("/health/ready")
                if ready.status_code == 200:
                    break
            except httpx.TransportError:
                pass
            await asyncio.sleep(.1)
        else:
            raise AssertionError("API listener did not become ready")
    return processes, clients


async def fixture(administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok

    owner = await access.issue(client, tokens[0]["access_token"])
    async with administrative() as db:
        identity = (await identified_users(db, [UUID(owner["userId"])]))[UUID(owner["userId"])]
    async with administrative() as db:
        created = await bootstrap_practice(db, BootstrapPracticeInput(
            owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
            owner_name="Fixture Owner", professional_name="Fixture Professional", display_name="Fixture Practice",
            time_zone="America/Caracas", location_name="Fixture Office", location_address="Fictional address",
            location_country="VE", location_state="Fixture State", location_city="Fixture City",
        ))
    assert isinstance(created, Ok)
    return owner, created.value


def envelope(action, entity, payload, version=0):
    return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
            "entityKey": entity if isinstance(entity, dict) else str(entity), "expectedVersion": version, "payload": payload}


async def submit(client, base, owner, operation):
    response = await client.post(base + "/sync/operations", headers=access.authorization(owner), json={"operations": [operation]})
    access.expect(response, 200)
    result = response.json()["results"][0]
    assert result["status"] == "accepted", result
    return result


async def snapshot(client, base, owner):
    response = await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json={})
    access.expect(response, 201)
    return response.json()


async def check_events(runtime, administrative, client, tokens):
    from src.api.sync.domain.downloads import SyncPosition
    from src.core.services.sync_signatures import verify_position

    evidence = ROOT / ".tmp/t31"
    evidence.mkdir(exist_ok=True, parents=True)
    signing_key = secrets.token_urlsafe(48)
    os.environ["API_SYNC_SIGNING_KEY"] = signing_key
    owner, practice = await fixture(administrative, client, tokens)
    base = f"/v1/accounts/{practice.account_id}"
    async with AsyncExitStack() as stack:
        processes, clients = await start_apis(stack, evidence)
        first, second = clients
        await submit(first, base, owner, envelope("RegisterAccountDevice", owner["deviceId"], {}))
        extra = await access.issue(second, tokens[0]["access_token"])
        await submit(second, base, extra, envelope("RegisterAccountDevice", extra["deviceId"], {}))
        capture = await snapshot(first, base, owner)
        cursor = capture["baseCursor"]
        url = base + "/sync/events"
        params = {"cursor": cursor}
        original = SyncPosition.model_validate_json(verify_position(cursor, signing_key.encode()))
        raw_listener = await asyncpg.connect(postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD).replace("postgresql+asyncpg", "postgresql", 1))
        stack.push_async_callback(raw_listener.close)
        payloads = []
        await raw_listener.add_listener("nightingale_sync", lambda connection, pid, channel, payload: payloads.append(payload))
        async with administrative() as db:
            await db.execute(text("UPDATE nightingale.account_sync_heads SET last_sequence=last_sequence+1 WHERE account_id=:id"), {"id": practice.account_id})
            await asyncio.sleep(.1)
            assert not payloads, "A hint escaped before commit"
            await db.rollback()
        await asyncio.sleep(.1)
        assert not payloads, "A rolled back head emitted a hint"
        access.expect(await first.get(url, headers=access.authorization(owner)), 422)
        access.expect(await first.get(url, headers=access.authorization(owner), params={"cursor": "invalid"}), 410)
        headers = {**access.authorization(owner), "Last-Event-ID": "999999999999"}
        async with first.stream("GET", url, params=params, headers=headers) as stream_one:
            access.expect(stream_one, 200)
            assert stream_one.headers["content-type"].startswith("text/event-stream")
            lines_one = stream_one.aiter_lines()
            initial = await event(lines_one, "heartbeat")
            assert initial["retry"] == "3000" and set(initial["data"]) == {"serverTime"}
            assert initial["data"]["serverTime"].endswith("Z")
            async with second.stream("GET", url, params=params, headers=access.authorization(owner)) as stream_two:
                access.expect(stream_two, 200)
                lines_two = stream_two.aiter_lines()
                await event(lines_two, "heartbeat")
                access.expect(await first.get(url, params=params, headers=headers), 429)
                async with administrative() as db:
                    assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_stream_leases")) == 2
                    assert not await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction')"))
                operation = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture SSE Patient"})
                await submit(second, base, owner, operation)
                notices = [await event(lines, "changes_available") for lines in (lines_one, lines_two)]
                assert payloads == [f"{practice.account_id}:{notices[0]['id']}"], "NOTIFY must contain only account and confirmed position"
                for notice in notices:
                    assert set(notice["data"]) == {"accountId", "cursor"}
                    hint = SyncPosition.model_validate_json(verify_position(notice["data"]["cursor"], signing_key.encode()))
                    assert hint.sequence == original.sequence
                    downloaded = await first.get(base + "/sync/changes", params={"cursor": notice["data"]["cursor"]}, headers=access.authorization(owner))
                    access.expect(downloaded, 200)
                    assert downloaded.json()["groups"][0]["operationId"] == operation["operationId"]
            for _ in range(100):
                async with administrative() as db:
                    remaining = await db.scalar(text("SELECT count(*) FROM nightingale.sync_stream_leases"))
                if remaining == 1:
                    break
                await asyncio.sleep(.02)
            assert remaining == 1, "Closing a stream did not release its lease"

            # Terminate only the two test API listener connections, never the services.
            admin = await postgres.connect_admin()
            try:
                pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE datname=$1 AND application_name='nightingale-sync-listener'", postgres.DATABASE)
                assert len(pids) == 2
                for row in pids:
                    assert await admin.fetchval("SELECT pg_terminate_backend($1)", row["pid"])
                states = await asyncio.gather(*(api.get("/health/ready") for api in clients))
                assert all(state.status_code == 503 for state in states)
                missed = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture During Listener Loss"})
                await submit(second, base, owner, missed)
                recovered_notice = await event(lines_one, "changes_available")
                assert int(recovered_notice["id"]) > int(notices[0]["id"])
                for api in clients:
                    for _ in range(100):
                        if (await api.get("/health/ready")).status_code == 200:
                            break
                        await asyncio.sleep(.02)
                    else:
                        raise AssertionError("Listener did not recover readiness")
                new_pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE datname=$1 AND application_name='nightingale-sync-listener'", postgres.DATABASE)
                assert len(new_pids) == 2 and not ({row["pid"] for row in pids} & {row["pid"] for row in new_pids})
            finally:
                await admin.close()
            heartbeat = await event(lines_one, "heartbeat")
            assert heartbeat["receivedAt"] - initial["receivedAt"] >= 13
            await submit(second, base, extra, envelope("RevokeAccountDevice", owner["deviceId"], {}, 1))
            revoked = await event(lines_one, "access_revoked")
            assert "data" not in revoked
            async with asyncio.timeout(5):
                assert [line async for line in lines_one] == []
        async with administrative() as db:
            assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_stream_leases")) == 0
        report = {"processIds": [process.pid for process in processes], "processCount": 2, "connectionLimit": 2,
                  "heartbeatSeconds": heartbeat["receivedAt"] - initial["receivedAt"], "retryMs": 3000,
                  "listenerLossReadiness": [state.status_code for state in states], "recovered": True,
                  "revokedStreamClosed": True, "leasesAfterClose": 0}
        (evidence / "events.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SSE checks passed: two API processes, native events, scoped hint without cursor advance, shared limit, no idle transactions, heartbeat, listener loss/recovery and revoked open stream.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_events))
