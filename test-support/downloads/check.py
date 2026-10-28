import asyncio
import runpy
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from pydantic import SecretStr
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_downloads(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.domain.downloads import SyncPosition, SyncWindow
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok
    from src.core.services.sync_signatures import sign_position, verify_position
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fictional-sync-signing-key-for-probes-only")
    key = api_settings.sync_signing_key.get_secret_value().encode()
    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        identity = (await identified_users(db, [UUID(owner["userId"])]))[UUID(owner["userId"])]
    async with administrative() as db:
        created = await bootstrap_practice(db, BootstrapPracticeInput(
            owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
            owner_name="Fixture Owner", professional_name="Fixture Professional",
            display_name="Fixture Practice", time_zone="America/Caracas", location_name="Fixture Office",
            location_address="Fictional address", location_country="VE", location_state="Fixture State", location_city="Fixture City",
        ))
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    professional = created.value.professional_id
    base = f"/v1/accounts/{account_id}"

    def envelope(action, entity, payload, version=0):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": entity if isinstance(entity, dict) else str(entity), "expectedVersion": version, "payload": payload}

    async def submit(operation, actor=owner):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [operation]})
        access.expect(response, 200)
        result = response.json()["results"][0]
        assert result["status"] == "accepted", result
        return result

    async def cursor(actor=owner, sequence=0, **updates):
        async with administrative() as db:
            epoch, now = (await db.execute(text("SELECT permission_epoch,clock_timestamp() FROM nightingale.account_sync_heads WHERE account_id=:id"), {"id": account_id})).one()
        position = SyncPosition(
            account_id=account_id, user_id=actor["userId"], device_id=actor["deviceId"],
            audience="owner" if actor is owner else "members", sequence=sequence, permission_epoch=epoch,
            issued_at=now, expires_at=now + timedelta(days=90),
            window=SyncWindow(appointments_from="2026-11-02", appointments_until="2026-11-03", time_zone="America/Caracas",
                              starts_at="2026-11-02T04:00:00Z", ends_at="2026-11-03T04:00:00Z"),
        ).model_copy(update=updates)
        return sign_position(position.model_dump_json(by_alias=True).encode(), key)

    async def get_changes(value, actor=owner, status=200):
        response = await client.get(base + "/sync/changes", headers=access.authorization(actor), params={"cursor": value})
        access.expect(response, status)
        assert response.headers["Cache-Control"] == "no-store"
        return response.json()

    await submit(envelope("RegisterAccountDevice", owner["deviceId"], {}))
    invitation = uuid7()
    await submit(envelope("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    await submit(envelope("RegisterAccountDevice", assistant["deviceId"], {}), assistant)
    patient, service, appointment = uuid7(), uuid7(), uuid7()
    registration = envelope("RegisterPatient", patient, {
        "fullName": "Fixture Patient", "phoneCode": "+58", "phone": "4125550101", "identificationBasis": "own_document",
        "identifiers": [{"id": str(uuid7()), "documentType": "national_id", "documentNumber": "FIXTURE-DOWNLOAD-001"}],
    })
    await submit(registration)
    await submit(envelope("SetPatientCompletion", patient, {"completionStatus": "complete"}, 1))
    await submit(envelope("CreateService", service, {"professionalId": str(professional), "name": "Fixture private service", "defaultDurationMinutes": 30}))
    await submit(envelope("OfferService", {"professionalId": str(professional), "serviceId": str(service)}, {}))
    await submit(envelope("CreateService", uuid7(), {"professionalId": str(professional), "name": "Fixture secret catalog", "defaultDurationMinutes": 30}))
    await submit(envelope("CreateScheduleRule", uuid7(), {"professionalId": str(professional), "isoWeekday": 1, "localStartMinute": 480, "localEndMinute": 1020, "validFrom": "2026-10-26"}))
    payload = {"patientId": str(patient), "professionalId": str(professional), "serviceId": str(service),
               "startsAt": "2026-11-02T13:00:00Z", "endsAt": "2026-11-02T13:30:00Z", "responsibleContactId": None}
    await submit(envelope("CreateAppointment", appointment, payload))
    before_move = await cursor()
    async def snapshot(actor=owner, payload=None):
        response = await client.post(base + "/sync/snapshots", headers=access.authorization(actor), json=payload if payload is not None else {
            "appointmentsFrom": "2026-11-02", "appointmentsUntil": "2026-11-03",
        })
        access.expect(response, 201)
        return response.json()

    async def snapshot_get(snapshot_id, suffix="", actor=owner, status=200):
        response = await client.get(base + f"/sync/snapshots/{snapshot_id}" + suffix, headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    captured = await snapshot()
    owner_items = await snapshot_get(captured["snapshotId"], "/items?shows=500")
    assert owner_items["total"] == captured["itemCount"] == len(owner_items["items"])
    assert "Fixture secret catalog" in str(owner_items)
    history = next(item for item in owner_items["items"] if item["entityType"] == "appointment_history")
    assert len(history["state"]["items"]) == history["entityVersion"] == 1
    assert await snapshot_get(captured["snapshotId"]) == captured
    assert not (await get_changes(captured["baseCursor"]))["groups"]
    async with administrative() as db:
        snapshots_before = await db.scalar(text("SELECT count(*) FROM nightingale.sync_snapshots"))
    with patch.object(api_settings, "sync_signing_key", None):
        assert (await get_changes(captured["baseCursor"], status=503))["code"] == "DEPENDENCY_UNAVAILABLE"
        assert (await snapshot_get(captured["snapshotId"], status=503))["code"] == "DEPENDENCY_UNAVAILABLE"
        response = await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json={})
        access.expect(response, 503)
        assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_snapshots")) == snapshots_before
    assistant_snapshot = await snapshot(assistant)
    assistant_items = await snapshot_get(assistant_snapshot["snapshotId"], "/items?shows=500", assistant)
    assert "Fixture secret catalog" not in str(assistant_items)
    assert all(item["entityType"] not in {"membership", "invitation", "account_device", "service"} for item in assistant_items["items"])
    await snapshot_get(captured["snapshotId"], actor=assistant, status=404)
    await snapshot_get(captured["snapshotId"], actor=outsider, status=404)
    await snapshot_get(str(uuid7()), status=404)
    paged = []
    for number in range(1, (captured["itemCount"] + 1) // 2 + 1):
        page = await snapshot_get(captured["snapshotId"], f"/items?page={number}&shows=2")
        assert page["total"] == captured["itemCount"]
        assert page == await snapshot_get(captured["snapshotId"], f"/items?page={number}&shows=2")
        paged.extend(page["items"])
    assert paged == owner_items["items"]
    assert not (await snapshot_get(captured["snapshotId"], "/items?page=10000"))["items"]
    for invalid in ({"appointmentsFrom": None}, {"appointmentsFrom": "2027-12-01", "appointmentsUntil": "2026-11-01"}, {"appointmentsFrom": "2026-01-01", "appointmentsUntil": "2028-01-01"}):
        access.expect(await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json=invalid), 422)
    default_snapshot = await snapshot(payload={})
    assert default_snapshot["window"]["timeZone"] == "America/Caracas"
    from datetime import date
    assert (date.fromisoformat(default_snapshot["window"]["appointmentsUntil"]) - date.fromisoformat(default_snapshot["window"]["appointmentsFrom"])).days == 211

    full = await get_changes(before_move)
    assert not full["hasMore"]
    patient_group = next(group for group in full["groups"] if group["operationId"] == registration["operationId"])
    assert len(patient_group["changes"]) == 2
    move_cursor = full["nextCursor"]
    await submit(envelope("RescheduleAppointment", appointment, {"startsAt": "2026-11-09T13:00:00Z", "endsAt": "2026-11-09T13:30:00Z"}, 1))
    moved = await get_changes(move_cursor)
    assert len(moved["groups"]) == 1
    assert moved["groups"][0]["changes"][0]["changeKind"] == "remove"
    assert moved["groups"][0]["changes"][0]["state"] is None
    assert not (await get_changes(moved["nextCursor"]))["groups"]
    assert await snapshot_get(captured["snapshotId"], "/items?shows=500") == owner_items
    assert (await get_changes(captured["baseCursor"]))["groups"][0]["changes"][0]["changeKind"] == "remove"
    async with administrative() as db:
        old_start = await db.scalar(text("SELECT previous_starts_at FROM nightingale.change_log WHERE account_id=:account AND entity_key=to_jsonb(CAST(:id AS text)) AND entity_version=2"), {"account": account_id, "id": str(appointment)})
        assert old_start.isoformat().startswith("2026-11-02T13:00")

    # One group per SQL page: invisible groups still advance and large groups stay whole.
    original_page = dao_changes.groups_after
    async def one_group(db, account, sequence, through):
        return await original_page(db, account, sequence, through, groups=1)
    value = await cursor(assistant)
    visible = []
    invisible = 0
    with patch.object(dao_changes, "groups_after", side_effect=one_group):
        for _ in range(30):
            page = await get_changes(value, assistant)
            invisible += not bool(page["groups"])
            visible.extend(page["groups"])
            assert page["nextCursor"] != value
            value = page["nextCursor"]
            if not page["hasMore"]:
                break
        else:
            raise AssertionError("Download did not reach the committed head")
    assert invisible > 0
    assert len(next(group for group in visible if group["operationId"] == registration["operationId"])["changes"]) == 2
    # Version two already exists; downloading version one must not expose its history.
    appointment_groups = [group for group in visible if any(change["entityType"] == "appointment" for change in group["changes"])]
    assert len(appointment_groups) == 2
    original_history = next(change for change in appointment_groups[0]["changes"] if change["entityType"] == "appointment_history")
    assert original_history["entityVersion"] == original_history["state"]["version"] == 1
    assert [item["version"] for item in original_history["state"]["items"]] == [1]
    assert [(change["entityType"], change["changeKind"], change["state"]) for change in appointment_groups[1]["changes"]] == [
        ("appointment", "remove", None), ("appointment_history", "remove", None),
    ]
    assert "Fixture secret catalog" not in str(visible)
    assert all(change["entityType"] not in {"membership", "invitation", "account_device", "service"} for group in visible for change in group["changes"])
    for invalid in (value + "x", await cursor(assistant, sequence=10**6), await cursor(assistant, permission_epoch=1), await cursor(assistant, account_id=uuid7())):
        assert (await get_changes(invalid, assistant, 410))["code"] == "CURSOR_EXPIRED"
    await get_changes(value, owner, 410)
    await get_changes(value, outsider, 404)
    access.expect(await client.get(base + "/sync/changes", params={"cursor": value, "page": 1}, headers=access.authorization(owner)), 422)

    # Writer two tries to commit before writer one; PostgreSQL must hold it at the account head.
    entered, release = asyncio.Event(), asyncio.Event()
    original_append = dao_changes.append
    first = envelope("UpdateAccountDetails", account_id, {"displayName": "Fixture new name"}, 1)
    second = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture second patient"})
    async def hold_first(db, values, **kwargs):
        await original_append(db, values, **kwargs)
        if values["operation_id"] == UUID(first["operationId"]):
            entered.set()
            await asyncio.wait_for(release.wait(), 20)
    start_cursor = (await get_changes(await cursor()))["nextCursor"]
    with patch.object(dao_changes, "append", side_effect=hold_first):
        writer_one = asyncio.create_task(submit(first))
        await asyncio.wait_for(entered.wait(), 10)
        writer_two = asyncio.create_task(submit(second, assistant))
        try:
            for _ in range(100):
                async with administrative() as db:
                    blocked = await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND cardinality(pg_blocking_pids(pid))>0)"))
                if blocked:
                    break
                await asyncio.sleep(.02)
            else:
                raise AssertionError("Second writer did not wait for the first")
            assert not writer_two.done()
        finally:
            release.set()
            await asyncio.gather(writer_one, writer_two)
    page = await get_changes(start_cursor)
    assert [group["operationId"] for group in page["groups"]] == [first["operationId"], second["operationId"]]
    parsed = SyncPosition.model_validate_json(verify_position(page["nextCursor"], key))
    assert parsed.window.time_zone == "America/Caracas"

    # Capture and a writer overlap. The capture reports the old view and its exact base.
    from src.api.sync.application import snapshot_cases
    from src.api.sync.repository.dao import dao_heads, dao_snapshot_items
    original_accounts = snapshot_cases.snapshot_accounts
    capturing, finish_capture = asyncio.Event(), asyncio.Event()
    async def hold_capture(db, context):
        assert await db.scalar(text("SHOW transaction_isolation")) == "repeatable read"
        capturing.set()
        await asyncio.wait_for(finish_capture.wait(), 20)
        return await original_accounts(db, context)
    new_patient = uuid7()
    concurrent_operation = envelope("RegisterPatient", new_patient, {"fullName": "Fixture after capture"})
    with patch.object(snapshot_cases, "snapshot_accounts", side_effect=hold_capture):
        capture_task = asyncio.create_task(snapshot())
        await asyncio.wait_for(capturing.wait(), 10)
        writer = asyncio.create_task(submit(concurrent_operation, assistant))
        try:
            for _ in range(100):
                async with administrative() as db:
                    blocked = await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND cardinality(pg_blocking_pids(pid))>0)"))
                if blocked:
                    break
                await asyncio.sleep(.02)
            else:
                raise AssertionError("Writer did not coordinate with capture")
        finally:
            finish_capture.set()
            coherent, _ = await asyncio.gather(capture_task, writer)
    coherent_items = await snapshot_get(coherent["snapshotId"], "/items?shows=500")
    assert str(new_patient) not in str(coherent_items)
    delta = await get_changes(coherent["baseCursor"])
    assert [group["operationId"] for group in delta["groups"]] == [concurrent_operation["operationId"]]
    assert str(new_patient) in str(delta)

    from sqlalchemy.exc import DBAPIError
    for statement in (
        "UPDATE nightingale.sync_snapshots SET item_count=item_count+1 WHERE id=:id",
        "UPDATE nightingale.sync_snapshot_items SET entity_version=entity_version+1 WHERE snapshot_id=:id",
        "DELETE FROM nightingale.sync_snapshot_items WHERE snapshot_id=:id",
    ):
        try:
            async with administrative() as db:
                async with db.begin():
                    await db.execute(text(statement), {"id": UUID(captured["snapshotId"])})
        except DBAPIError:
            pass
        else:
            raise AssertionError("Materialized view was changed")
    async with administrative() as db:
        count_before = await db.scalar(text("SELECT count(*) FROM nightingale.sync_snapshots"))
    original_item = dao_snapshot_items.record
    async def incomplete(db, **kwargs):
        kwargs["values"]["ordinal"] += 1
        return await original_item(db, **kwargs)
    with patch.object(dao_snapshot_items, "record", side_effect=incomplete):
        access.expect(await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json={}), 503)
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_snapshots")) == count_before
        assert not await db.scalar(text("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction')"))

    from datetime import datetime
    expiry = datetime.fromisoformat(captured["expiresAt"]) + timedelta(seconds=1)
    original_clock = dao_heads.get_server_time
    async def expired_clock(db):
        return expiry
    with patch.object(dao_heads, "get_server_time", side_effect=expired_clock):
        assert (await snapshot_get(captured["snapshotId"], status=410))["code"] == "SNAPSHOT_EXPIRED"
        assert (await snapshot_get(captured["snapshotId"], "/items", status=410))["code"] == "SNAPSHOT_EXPIRED"
    assert await snapshot_get(captured["snapshotId"], "/items?shows=500") == owner_items
    # A different explicit window has independent data and never removes consumer intentions.
    new_window = await snapshot(payload={"appointmentsFrom": "2026-11-09", "appointmentsUntil": "2026-11-10"})
    assert any(item["entityType"] == "appointment" for item in (await snapshot_get(new_window["snapshotId"], "/items?shows=500"))["items"])
    await submit(envelope("UpdateAccountDetails", account_id, {"timeZone": "UTC"}, 2))
    assert (await snapshot_get(captured["snapshotId"]))["window"]["timeZone"] == "America/Caracas"
    assert SyncPosition.model_validate_json(verify_position((await get_changes(captured["baseCursor"]))["nextCursor"], key)).window.time_zone == "America/Caracas"
    await submit(envelope("UpdateAccountDetails", account_id, {"timeZone": "America/Havana"}, 3))
    folded = await snapshot(payload={"appointmentsFrom": "2026-11-01", "appointmentsUntil": "2026-11-02"})
    assert folded["window"]["startsAt"] == "2026-11-01T05:00:00Z", folded
    extra = await access.issue(client, tokens[0]["access_token"])
    await submit(envelope("RegisterAccountDevice", extra["deviceId"], {}), extra)
    assert (await snapshot_get(captured["snapshotId"], status=410))["code"] == "SNAPSHOT_SCOPE_CHANGED"
    assert (await get_changes(captured["baseCursor"], status=410))["code"] == "CURSOR_EXPIRED"
    access.expect(await client.delete(base + f'/sync/snapshots/{captured["snapshotId"]}', headers=access.authorization(owner)), 204)
    assert (await snapshot_get(captured["snapshotId"], status=404))["code"] == "NOT_FOUND"
    authorized_snapshot = await snapshot()
    await submit(envelope("RevokeAccountDevice", owner["deviceId"], {}, 1), extra)
    await snapshot_get(authorized_snapshot["snapshotId"], status=403)
    await snapshot_get(authorized_snapshot["snapshotId"], "/items", status=403)
    await get_changes(authorized_snapshot["baseCursor"], status=403)
    print("C10 review checks passed: missing signing key returns 503 without a capture, old-version history excludes newer entries, and revoked account devices cannot read captures/pages/deltas.")
    print("Snapshot checks passed: coherent RR capture/base, immutable pages, privacy, UTC window, scoped access, expiry, rollback and release.")
    print("Download checks passed: complete groups, hidden audiences, fixed scope, view removal and commit-order coordination.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_downloads))
