import asyncio
import json
import math
import os
import runpy
import secrets
import time
import platform
from importlib.metadata import version
from contextlib import AsyncExitStack, suppress
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
events = runpy.run_path(str(ROOT / "test-support/events/check.py"))
support = events["support"]
access = events["access"]
postgres = events["postgres"]
envelope = events["envelope"]
submit = events["submit"]
snapshot = events["snapshot"]


class Consumer:
    def __init__(self, response):
        self.pending = asyncio.Queue()
        self.task = asyncio.create_task(self.read(response))

    async def read(self, response):
        fields = {}
        try:
            async for line in response.aiter_lines():
                if not line:
                    if fields:
                        fields["receivedAt"] = time.perf_counter()
                        if "data" in fields:
                            fields["data"] = json.loads(fields["data"])
                        self.pending.put_nowait(fields)
                    fields = {}
                elif not line.startswith(":"):
                    key, _, value = line.partition(":")
                    fields[key] = value.lstrip(" ")
        finally:
            self.pending.put_nowait(None)

    async def next(self, kind, *, sequence=0, after=0, timeout=22):
        async with asyncio.timeout(timeout):
            while True:
                notice = await self.pending.get()
                assert notice is not None, "SSE ended before the expected event"
                if notice.get("event") == kind and int(notice.get("id", sequence)) >= sequence and notice["receivedAt"] >= after:
                    return notice

    async def close(self):
        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task


def commit_records(evidence):
    records = {}
    for path in evidence.glob("commits-*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            records[row["operationId"]] = row
    return records


async def open_consumers(stack, clients, base, devices):
    captures = [await snapshot(clients[index % 2], base, device) for index, device in enumerate(devices)]
    consumers = []
    for index in range(10):
        client = clients[index % 2]
        device = devices[index // 2]
        response = await stack.enter_async_context(client.stream("GET", base + "/sync/events",
                                                    params={"cursor": captures[index // 2]["baseCursor"]},
                                                    headers=access.authorization(device)))
        access.expect(response, 200)
        consumer = Consumer(response)
        stack.push_async_callback(consumer.close)
        await consumer.next("heartbeat")
        consumers.append(consumer)
    return consumers, captures


async def joint_business(clients, base, owner, tokens, practice, administrative):
    first, second = clients
    assistant = await access.issue(second, tokens[1]["access_token"])
    invitation = uuid7()
    await submit(first, base, owner, envelope("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))
    access.expect(await second.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant),
                                    json={"operationId": str(uuid7())}), 200)
    await submit(second, base, assistant, envelope("RegisterAccountDevice", assistant["deviceId"], {}))
    patient, service = uuid7(), uuid7()
    await submit(first, base, owner, envelope("RegisterPatient", patient, {
        "fullName": "Fixture Concurrent Patient", "phoneCode": "+58", "phone": "4125550101", "identificationBasis": "own_document",
        "identifiers": [{"id": str(uuid7()), "documentType": "national_id", "documentNumber": "FIXTURE-JOINT-001"}],
    }))
    await submit(first, base, owner, envelope("SetPatientCompletion", patient, {"completionStatus": "complete"}, 1))
    await submit(first, base, owner, envelope("CreateService", service, {"professionalId": str(practice.professional_id),
                                                                          "name": "Fixture Joint Service", "defaultDurationMinutes": 30}))
    await submit(first, base, owner, envelope("OfferService", {"professionalId": str(practice.professional_id), "serviceId": str(service)}, {}))
    await submit(first, base, owner, envelope("CreateScheduleRule", uuid7(), {"professionalId": str(practice.professional_id),
                                                                           "isoWeekday": 1, "localStartMinute": 480,
                                                                           "localEndMinute": 1020, "validFrom": "2026-10-26"}))
    payload = {"patientId": str(patient), "professionalId": str(practice.professional_id), "serviceId": str(service),
               "startsAt": "2026-11-02T13:00:00Z", "endsAt": "2026-11-02T13:30:00Z"}
    bookings = [envelope("CreateAppointment", uuid7(), payload) for _ in range(2)]

    async def result(api, actor, operation):
        response = await api.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [operation]})
        access.expect(response, 200)
        return response.json()["results"][0]

    outcomes = await asyncio.gather(result(first, owner, bookings[0]), result(second, assistant, bookings[1]))
    assert sorted(row["status"] for row in outcomes) == ["accepted", "conflict"], outcomes
    winner = next(index for index, row in enumerate(outcomes) if row["status"] == "accepted")
    assert outcomes[1-winner]["error"]["code"] == "SLOT_UNAVAILABLE"
    appointment = bookings[winner]["entityKey"]
    confirm = envelope("ConfirmAppointment", UUID(appointment), {}, 1)
    duplicates = await asyncio.gather(result(first, owner, confirm), result(second, owner, confirm))
    assert sorted(row["status"] for row in duplicates) == ["accepted", "duplicate"]
    stale = await result(second, assistant, envelope("CancelAppointment", UUID(appointment), {"changeReason": "fixture"}, 1))
    assert stale["status"] == "conflict" and stale["error"]["code"] == "VERSION_CONFLICT"
    mismatch = await result(first, owner, {**confirm, "expectedVersion": 2})
    assert mismatch["status"] == "conflict" and mismatch["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    state = await second.get(base + f"/appointments/{appointment}", headers=access.authorization(assistant))
    access.expect(state, 200)
    assert state.json()["version"] == 2 and state.json()["status"] == "confirmed"
    history = await first.get(base + f"/appointments/{appointment}/history", headers=access.authorization(owner))
    access.expect(history, 200)
    assert sorted(row["version"] for row in history.json()["items"]) == [1, 2]
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.appointments")) == 1
        assert await db.scalar(text("SELECT count(*) FROM nightingale.appointment_histories")) == 2
        assert await db.scalar(text("SELECT count(*) FROM nightingale.operation_receipts WHERE operation_id=:id"), {"id": UUID(confirm["operationId"])}) == 1
    return {"reservationOutcomes": [row["status"] for row in outcomes], "duplicates": [row["status"] for row in duplicates],
            "staleVersion": stale["error"]["code"], "changedContent": mismatch["error"]["code"],
            "appointmentCount": 1, "historyVersions": [1, 2]}


async def check_collaboration(runtime, administrative, client, tokens):
    evidence = ROOT / ".tmp/t32"
    evidence.mkdir(exist_ok=True, parents=True)
    for path in evidence.glob("commits-*.jsonl"):
        path.write_text("", encoding="utf-8")
    os.environ["API_SYNC_SIGNING_KEY"] = secrets.token_urlsafe(48)
    owner, practice = await events["fixture"](administrative, client, tokens)
    base = f"/v1/accounts/{practice.account_id}"
    async with AsyncExitStack() as stack:
        processes, clients = await events["start_apis"](stack, evidence, instrumented=True)
        devices = [owner] + [await access.issue(clients[index % 2], tokens[0]["access_token"]) for index in range(4)]
        revoker = await access.issue(clients[1], tokens[0]["access_token"])
        for device in [*devices, revoker]:
            await submit(clients[0], base, device, envelope("RegisterAccountDevice", device["deviceId"], {}))
        business = await joint_business(clients, base, owner, tokens, practice, administrative)
        (evidence / "business.json").write_text(json.dumps(business, indent=2), encoding="utf-8")
        async with AsyncExitStack() as streams:
            consumers, captures = await open_consumers(streams, clients, base, devices)
            async with administrative() as db:
                assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_stream_leases")) == 10
                assert not await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction')"))
            samples = []
            for index in range(20):
                operation = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture Joint Patient"})
                await submit(clients[index % 2], base, owner, operation)
                async with administrative() as db:
                    sequence = await db.scalar(text("SELECT last_sequence FROM nightingale.account_sync_heads WHERE account_id=:id"), {"id": practice.account_id})
                notices = await asyncio.gather(*(consumer.next("changes_available", sequence=sequence) for consumer in consumers))
                commit = commit_records(evidence)[operation["operationId"]]
                assert commit["beforeCommit"] <= commit["afterCommit"]
                assert all(notice["receivedAt"] >= commit["beforeCommit"] for notice in notices)
                samples.extend({"commitIndex": index, "consumerIndex": number, "sequence": sequence,
                                "afterCommitMs": (notice["receivedAt"] - commit["afterCommit"]) * 1000,
                                "commitUpperBoundMs": (notice["receivedAt"] - commit["beforeCommit"]) * 1000}
                               for number, notice in enumerate(notices))

            def p95(field):
                return sorted(sample[field] for sample in samples)[math.ceil(.95 * len(samples)) - 1]

            assert len(samples) == 200 and p95("commitUpperBoundMs") < 2000, "Local commit-to-hint target failed"
            # A signal lost while both listeners are absent must be recovered by
            # the confirmed LISTEN followed by a fresh journal check.
            admin = await postgres.connect_admin()
            try:
                old_pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE datname=$1 AND application_name='nightingale-sync-listener'", postgres.DATABASE)
                assert len(old_pids) == 2
                for row in old_pids:
                    assert await admin.fetchval("SELECT pg_terminate_backend($1)", row["pid"])
                observed_down = [False, False]
                for _ in range(100):
                    degraded = await asyncio.gather(*(api.get("/health/ready") for api in clients))
                    observed_down = [seen or response.status_code == 503 for seen, response in zip(observed_down, degraded)]
                    if all(observed_down):
                        break
                    await asyncio.sleep(.005)
                assert all(observed_down), "The listener loss did not degrade readiness"
                missed = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture Recovery Patient"})
                await submit(clients[1], base, owner, missed)
                async with administrative() as db:
                    recovered_sequence = await db.scalar(text("SELECT last_sequence FROM nightingale.account_sync_heads WHERE account_id=:id"), {"id": practice.account_id})
                await asyncio.gather(*(consumer.next("changes_available", sequence=recovered_sequence) for consumer in consumers))
                for api in clients:
                    assert (await api.get("/health/ready")).status_code == 200
                new_pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE datname=$1 AND application_name='nightingale-sync-listener'", postgres.DATABASE)
                assert len(new_pids) == 2 and not ({row["pid"] for row in old_pids} & {row["pid"] for row in new_pids})
            finally:
                await admin.close()
            recovered = await snapshot(clients[1], base, devices[-1])
            recovered_items = await clients[1].get(base + f'/sync/snapshots/{recovered["snapshotId"]}/items?shows=500', headers=access.authorization(devices[-1]))
            access.expect(recovered_items, 200)
            assert len([item for item in recovered_items.json()["items"] if item["entityType"] == "patient_profile"]) == 22
            delta = await clients[0].get(base + "/sync/changes", params={"cursor": recovered["baseCursor"]}, headers=access.authorization(devices[-1]))
            access.expect(delta, 200)
            assert not delta.json()["groups"]

            # Global revocation sends no account hint: the heartbeat itself must
            # reauthorize, emit no private data and close just these two streams.
            revoked_at = time.perf_counter()
            response = await clients[1].post(f'/v1/me/devices/{owner["deviceId"]}/revoke', headers=access.authorization(revoker))
            access.expect(response, 204)
            revoked = await asyncio.gather(*(consumer.next("access_revoked", after=revoked_at) for consumer in consumers[:2]))
            assert all("data" not in notice for notice in revoked)
            await asyncio.gather(*(asyncio.wait_for(consumer.task, 5) for consumer in consumers[:2]))
            still_live = await consumers[-1].next("heartbeat", after=revoked_at)
            assert still_live["receivedAt"] >= revoked_at
            access.expect(await clients[0].get(base + "/sync/changes", params={"cursor": captures[0]["baseCursor"]}, headers=access.authorization(owner)), 401)
            access.expect(await clients[1].post(base + "/sync/operations", json={"operations": [operation]}, headers=access.authorization(owner)), 401)
            access.expect(await clients[0].get(base + f'/sync/operations/{operation["operationId"]}', headers=access.authorization(owner)), 401)
            access.expect(await clients[1].get(base + f'/sync/operations/{operation["operationId"]}', headers=access.authorization(devices[-1])), 200)
        async with administrative() as db:
            for _ in range(100):
                count = await db.scalar(text("SELECT count(*) FROM nightingale.sync_stream_leases"))
                if count == 0:
                    break
                await asyncio.sleep(.02)
            assert count == 0
        async with administrative() as db:
            final = (await db.execute(text("""SELECT
                (SELECT count(*) FROM nightingale.appointments),
                (SELECT count(*) FROM nightingale.appointment_histories),
                (SELECT count(*) FROM nightingale.operation_receipts),
                (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                (SELECT count(*) FROM nightingale.account_patients)
            """))).one()
            assert final[0:2] == (1, 2) and final[2] == final[3] and final[4] == 22
            assert not await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction')"))
            server_version = await db.scalar(text("SHOW server_version"))
        report = {"processIds": [process.pid for process in processes], "ports": [api.base_url.port for api in clients],
                  "streams": 10, "commits": 20, "samples": len(samples), "python": platform.python_version(),
                  "platform": platform.platform(), "postgresql": server_version,
                  "packages": {name: version(name) for name in ("fastapi", "starlette", "sqlalchemy", "asyncpg", "uvicorn")},
                  "clock": "Windows perf_counter shared by processes; before_commit/after_commit bracket the database commit",
                  "p95AfterCommitMs": p95("afterCommitMs"), "p95CommitUpperBoundMs": p95("commitUpperBoundMs"),
                  "negativeAfterCommitSamples": sum(sample["afterCommitMs"] < 0 for sample in samples),
                  "maxCommitUpperBoundMs": max(sample["commitUpperBoundMs"] for sample in samples),
                  "listenerLossRecoveredAllStreams": True, "globalRevocationClosedStreams": 2,
                  "revocationDelaySeconds": max(notice["receivedAt"] for notice in revoked) - revoked_at,
                  "leasesAfterClose": count, "finalCounts": list(final), "business": business,
                  "limits": "Local isolated API test; no Rust/Hub integration or production guarantee"}
        (evidence / "measurements.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (evidence / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")
        print(f"Joint checks passed: two API processes, ten streams, 20 commits/200 hints, p95 after-commit {report['p95AfterCommitMs']:.1f} ms; conservative commit bound {report['p95CommitUpperBoundMs']:.1f} ms; reservation/version/duplicate/recovery/revocation and final history verified.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_collaboration))
