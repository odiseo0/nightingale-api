import asyncio
import json
import runpy
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_retention(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.accounts.repository.dao import dao_accounts
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.application.sync_cases import purge_expired_results
    from src.api.sync.domain.downloads import SyncPosition
    from src.api.sync.repository.dao import dao_heads
    from src.core import Err, Ok
    from src.core.services.sync_signatures import sign_position, verify_position
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fictional-retention-key-for-tests-only")
    key = api_settings.sync_signing_key.get_secret_value().encode()
    owner = await access.issue(client, tokens[0]["access_token"])
    async with administrative() as db:
        identity = (await identified_users(db, [UUID(owner["userId"])]))[UUID(owner["userId"])]
        now = await dao_heads.get_server_time(db)
    old = now - timedelta(days=91)
    with patch.object(dao_accounts, "get_server_time", return_value=old - timedelta(days=1)):
        async with administrative() as db:
            created = await bootstrap_practice(db, BootstrapPracticeInput(
                owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
                owner_name="Fixture Owner", professional_name="Fixture Professional", display_name="Fixture Practice",
                time_zone="America/Caracas", location_name="Fixture Office", location_address="Fictional address",
                location_country="VE", location_state="Fixture State", location_city="Fixture City",
            ))
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    base = f"/v1/accounts/{account_id}/sync"
    headers = access.authorization(owner)

    def envelope(action, entity, payload):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": str(entity), "expectedVersion": 0, "payload": payload}

    async def submit(items, status=200):
        response = await client.post(base + "/operations", headers=headers, json={"operations": items})
        access.expect(response, status)
        return response.json()["results"] if status == 200 else response.json()

    async def capture():
        response = await client.post(base + "/snapshots", headers=headers, json={})
        access.expect(response, 201)
        return response.json()

    registrations = [envelope("RegisterPatient", uuid7(), {"fullName": "Fixture retained patient"}) for _ in range(102)]
    registrations[0]["payload"]["identifiers"] = [{"id": str(uuid7()), "documentType": "national_id", "documentNumber": "FIXTURE-RETAINED-001"}]
    rejected = [envelope("FutureOperation", uuid7(), {}) for _ in range(502)]
    with patch.object(dao_heads, "get_server_time", return_value=old):
        assert (await submit([envelope("RegisterAccountDevice", owner["deviceId"], {})]))[0]["status"] == "accepted"
        for items, expected in ((registrations, "accepted"), (rejected, "rejected")):
            for offset in range(0, len(items), 100):
                results = await submit(items[offset:offset+100])
                assert all(result["status"] == expected for result in results), results
        expired_snapshot = await capture()
    current = envelope("RegisterPatient", uuid7(), {"fullName": "Fixture recent patient"})
    assert (await submit([current]))[0]["status"] == "accepted"
    fresh_snapshot = await capture()
    position = SyncPosition.model_validate_json(verify_position(fresh_snapshot["baseCursor"], key))
    def cursor(sequence):
        value = position.model_copy(update={"sequence": sequence})
        return sign_position(value.model_dump_json(by_alias=True).encode(), key)

    async def changes(value, status=200):
        response = await client.get(base + "/changes", params={"cursor": value}, headers=headers)
        access.expect(response, status)
        return response.json()

    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.account_patients),
                       (SELECT count(*) FROM nightingale.operation_receipts),
                       (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                       (SELECT count(*) FROM nightingale.appointment_histories),
                       (SELECT count(*) FROM nightingale.operation_receipts WHERE result_json IS NOT NULL),
                       (SELECT count(DISTINCT sequence) FROM nightingale.change_log),
                       retained_from_sequence FROM nightingale.account_sync_heads WHERE account_id=:id
            """), {"id": account_id})).one())
    before = await counts()
    assert before[4:] == (606, 104, 1), before
    assert (await changes(expired_snapshot["baseCursor"], 410))["code"] == "CURSOR_EXPIRED"
    assert (await changes(cursor(0)))["hasMore"]
    try:
        async with administrative() as db:
            async with db.begin():
                await db.execute(text("DELETE FROM nightingale.change_log WHERE account_id=:id AND sequence=104"), {"id": account_id})
    except DBAPIError:
        pass
    else:
        raise AssertionError("A recent committed group was deleted")
    async with runtime() as db:
        assert isinstance(await purge_expired_results(db), Err)
    async with administrative() as db:
        result = await purge_expired_results(db)
    assert isinstance(result, Ok) and result.value == 500
    after = await counts()
    assert after[:4] == before[:4] and after[4:] == (106, 4, 101), after
    assert (await changes(cursor(99), 410))["code"] == "CURSOR_EXPIRED"
    remaining = await changes(cursor(100))
    assert len(remaining["groups"]) == 4 and not remaining["hasMore"]
    for snapshot_id, expected in ((expired_snapshot["snapshotId"], 404), (fresh_snapshot["snapshotId"], 200)):
        access.expect(await client.get(base + f"/snapshots/{snapshot_id}", headers=headers), expected)
    assert (await submit([registrations[0]], 410))["code"] == "RESULT_EXPIRED"
    changed = {**registrations[0], "payload": {"fullName": "Other fixture"}}
    assert (await submit([changed]))[0]["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    async with administrative() as db:
        assert (await purge_expired_results(db)).value == 105
    after_second = await counts()
    assert after_second[:4] == before[:4] and after_second[4:] == (1, 1, 104), after_second
    assert len((await changes(cursor(103)))["groups"]) == 1
    assert (await changes(cursor(102), 410))["code"] == "CURSOR_EXPIRED"
    # Rebuild explicitly after retention. The new view includes all current profiles.
    recovered = await capture()
    response = await client.get(base + f'/snapshots/{recovered["snapshotId"]}/items?shows=500', headers=headers)
    access.expect(response, 200)
    profiles = [item for item in response.json()["items"] if item["entityType"] == "patient_profile"]
    assert len(profiles) == 103 and not (await changes(recovered["baseCursor"]))["groups"]
    assert (await submit([registrations[0]], 410))["code"] == "RESULT_EXPIRED"
    async with administrative() as db:
        assert (await purge_expired_results(db)).value == 0
        receipt = (await db.execute(text("SELECT request_hash,status,entity_key,result_json,purged_at FROM nightingale.operation_receipts WHERE account_id=:account AND operation_id=:operation"),
                                    {"account": account_id, "operation": UUID(registrations[0]["operationId"])})).one()
        assert len(receipt.request_hash) == 32 and receipt.status == "accepted" and receipt.result_json is None and receipt.purged_at is not None
        assert receipt.entity_key == registrations[0]["entityKey"]
    print("Retention checks passed: 90-day SQL guard, batches 500/100, complete groups, boundary-1, expired temporary cleanup, immutable receipt and explicit recovery without repeated effects.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_retention))
