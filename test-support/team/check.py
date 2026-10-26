import asyncio
import json
import os
import runpy
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_team(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.accounts.repository.dao import dao_accounts
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        users = await identified_users(db, [UUID(owner["userId"])])
    identity = users[UUID(owner["userId"])]
    data = BootstrapPracticeInput(
        owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject, owner_name="Fixture Owner",
        professional_name="Fixture Professional", display_name="Fixture Practice", time_zone="America/Caracas",
        location_name="Fixture Office", location_address="Fictional address", location_country="VE",
        location_state="Fixture State", location_city="Fixture City",
    )
    async with administrative() as db:
        result = await bootstrap_practice(db, data)
    assert isinstance(result, Ok)
    account_id = result.value.account_id
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, status=200, account_base=None):
        response = await client.post((account_base or base) + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1, "action": action,
            "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def invitation(actor=assistant):
        key = uuid7()
        result = await operation("CreateInvitation", key, {"inviteeUserId": actor["userId"]})
        assert result["status"] == "accepted"
        return key, result["state"]

    async def accept(key, actor=assistant, operation_id=None, status=200):
        response = await client.post(f"/v1/me/invitations/{key}/accept", headers=access.authorization(actor), json={"operationId": str(operation_id or uuid7())})
        access.expect(response, status)
        return response.json()

    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.account_memberships),
                    (SELECT count(*) FROM nightingale.account_invitations),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log), last_sequence,permission_epoch
                FROM nightingale.account_sync_heads WHERE account_id=:id
            """), {"id": account_id})).one())

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    key, state = await invitation()
    from datetime import datetime
    assert datetime.fromisoformat(state["expiresAt"]) - datetime.fromisoformat(state["createdAt"]) == timedelta(hours=72)
    assert "acceptedOperationId" not in state
    assert state["createdAt"].endswith("Z") and state["expiresAt"].endswith("Z")
    for actor, expected in ((assistant, 1), (outsider, 0)):
        response = await client.get("/v1/me/invitations?status=pending&shows=1", headers=access.authorization(actor))
        access.expect(response, 200)
        assert response.json()["total"] == expected
    response = await client.get(base + "/invitations?shows=1", headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["items"][0]["id"] == str(key)
    before = await counts()
    await accept(key, outsider, status=404)
    assert await counts() == before
    operation_id = uuid7()
    concurrent = await asyncio.gather(accept(key, operation_id=operation_id), accept(key, operation_id=operation_id))
    assert sorted(item["status"] for item in concurrent) == ["accepted", "duplicate"]
    assert all(item["membershipVersion"] == 1 for item in concurrent)
    after = await counts()
    assert tuple(a - b for a, b in zip(after, before)) == (1, 0, 1, 1, 2, 1, 1)
    response = await client.get(base, headers=access.authorization(assistant))
    access.expect(response, 403)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"
    await operation("CreateInvitation", uuid7(), {"inviteeUserId": outsider["userId"]}, actor=assistant, status=403)
    await operation("SetMembershipStatus", owner["userId"], {"status": "inactive"}, 1, status=403)
    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 1))["entityVersion"] == 2
    await accept(key, operation_id=operation_id, status=403)
    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "active"}, 2))["entityVersion"] == 3
    assert (await accept(key, operation_id=operation_id))["status"] == "duplicate"

    async with administrative() as db:
        old = await dao_accounts.get_server_time(db) - timedelta(hours=73)
    with patch.object(dao_accounts, "get_server_time", return_value=old):
        expired, _ = await invitation(outsider)
    before = await counts()
    assert (await accept(expired, outsider, status=409))["code"] == "INVALID_STATE_TRANSITION"
    assert await counts() == before
    response = await client.get("/v1/me/invitations?status=expired", headers=access.authorization(outsider))
    access.expect(response, 200)
    assert response.json()["items"][0]["id"] == str(expired)

    race, _ = await invitation(outsider)
    async def race_accept():
        response = await client.post(f"/v1/me/invitations/{race}/accept", headers=access.authorization(outsider), json={"operationId": str(uuid7())})
        assert response.status_code in (200, 409)
        return response.status_code == 200
    accepted, revoked = await asyncio.gather(race_accept(), operation("RevokeInvitation", race, {}, 1))
    assert accepted != (revoked["status"] == "accepted")

    # A second invitation cannot add a second active membership.
    duplicate, _ = await invitation()
    assert (await accept(duplicate, status=409))["code"] == "NO_CHANGES"
    await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 3)
    before = await counts()
    original_append = dao_changes.append
    retry_id = uuid7()
    async def fail_group(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_group):
        await accept(duplicate, operation_id=retry_id, status=503)
    assert await counts() == before
    recovered = await accept(duplicate, operation_id=retry_id)
    assert recovered["membershipVersion"] == 5

    from src.api.accounts.infrastructure import invitations_api
    original_accept = invitations_api.accept_invitation
    await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 5)
    lost, _ = await invitation()
    lost_id = uuid7()
    async def lose_response(*args, **kwargs):
        await original_accept(*args, **kwargs)
        raise ConnectionResetError("Fixture response dropped after commit")
    with patch.object(invitations_api, "accept_invitation", side_effect=lose_response):
        try:
            await accept(lost, operation_id=lost_id)
        except ConnectionResetError:
            pass
        else:
            raise AssertionError("Response was not lost")
    assert (await accept(lost, operation_id=lost_id))["status"] == "duplicate"
    for path in ("/members", "/devices"):
        response = await client.get(base + path + "?shows=1", headers=access.authorization(owner))
        access.expect(response, 200)
        assert response.json()["total"] >= 2 and len(response.json()["items"]) == 1
        assert not {"oidcSubject", "secretHash", "accessToken", "acceptedOperationId"} & set(response.json()["items"][0])
        response = await client.get(base + path, headers=access.authorization(assistant))
        access.expect(response, 403)
    response = await client.get(base + "/professionals?status=active", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert response.json()["total"] == 1

    details_id = uuid7()
    changed = await operation("UpdateAccountDetails", account_id, {"displayName": " Changed Fixture "}, 1, operation_id=details_id)
    assert changed["status"] == "accepted" and changed["state"]["displayName"] == "Changed Fixture" and changed["entityVersion"] == 2
    repeated = await operation("UpdateAccountDetails", account_id, {"displayName": "Changed Fixture"}, 1, operation_id=details_id)
    assert repeated["status"] == "duplicate"
    assert (await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": True}, 2))["error"]["code"] == "VALIDATION_ERROR"
    assert (await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": 20}, 2))["entityVersion"] == 3
    assert (await operation("UpdateProfessionalProfile", result.value.professional_id, {"publicName": "Fixture Renamed"}, 1))["entityVersion"] == 2
    await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": 20}, 3, actor=assistant, status=403)
    disabled_id = uuid7()
    assert (await operation("SetAccountStatus", account_id, {"status": "inactive"}, 3, operation_id=disabled_id))["entityVersion"] == 4
    assert (await operation("SetAccountStatus", account_id, {"status": "inactive"}, 3, operation_id=disabled_id))["status"] == "duplicate"
    response = await client.get(base + f"/sync/operations/{disabled_id}", headers=access.authorization(owner))
    access.expect(response, 200)
    await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": 21}, 4, status=403)
    assert (await operation("SetAccountStatus", account_id, {"status": "active"}, 4))["entityVersion"] == 5
    assert (await operation("UpdateAccountDetails", account_id, {"timeZone": "Fixture/Unknown"}, 5))["error"]["code"] == "VALIDATION_ERROR"
    assert (await operation("UpdateAccountDetails", account_id, {"timeZone": None}, 5))["error"]["code"] == "VALIDATION_ERROR"
    assert (await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": 20}, 5))["error"]["code"] == "NO_CHANGES"
    assert (await operation("UpdateAccountPolicy", account_id, {"noShowGraceMinutes": 21}, 1))["error"]["code"] == "VERSION_CONFLICT"

    # The same installation stays active in another account after local revocation.
    async with administrative() as db:
        users = await identified_users(db, [UUID(outsider["userId"])])
        user = users[UUID(outsider["userId"])]
    async with administrative() as db:
        other = await bootstrap_practice(db, data.model_copy(update={"owner_issuer": user.oidc_issuer, "owner_subject": user.oidc_subject}))
    assert isinstance(other, Ok)
    other_base = f"/v1/accounts/{other.value.account_id}"
    assert (await operation("RegisterAccountDevice", outsider["deviceId"], {}, actor=outsider, account_base=other_base))["status"] == "accepted"
    other_invite = uuid7()
    assert (await operation("CreateInvitation", other_invite, {"inviteeUserId": assistant["userId"]}, actor=outsider, account_base=other_base))["status"] == "accepted"
    await accept(other_invite)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant, account_base=other_base))["status"] == "accepted"
    assert (await operation("RevokeAccountDevice", assistant["deviceId"], {}, 1))["entityVersion"] == 2
    response = await client.get(base, headers=access.authorization(assistant))
    access.expect(response, 403)
    response = await client.get(other_base, headers=access.authorization(assistant))
    access.expect(response, 200)
    assert (await operation("RestoreAccountDevice", assistant["deviceId"], {}, 2))["entityVersion"] == 3

    another_owner = await access.issue(client, tokens[0]["access_token"])
    assert (await operation("RegisterAccountDevice", another_owner["deviceId"], {}, actor=another_owner))["status"] == "accepted"
    assert (await operation("RevokeAccountDevice", another_owner["deviceId"], {}, 1))["entityVersion"] == 2
    await operation("RestoreAccountDevice", another_owner["deviceId"], {}, 2, actor=another_owner, status=403)
    assert (await operation("RestoreAccountDevice", another_owner["deviceId"], {}, 2))["entityVersion"] == 3
    response = await client.post(f"/v1/me/devices/{another_owner['deviceId']}/revoke", headers=access.authorization(owner))
    access.expect(response, 204)
    assert (await operation("RevokeAccountDevice", another_owner["deviceId"], {}, 3))["entityVersion"] == 4
    await operation("RestoreAccountDevice", another_owner["deviceId"], {}, 4, status=403)
    # Both paths follow identity -> account lock order and must finish without a deadlock.
    race_device = await access.issue(client, tokens[1]["access_token"])
    await operation("RegisterAccountDevice", race_device["deviceId"], {}, actor=race_device)
    await operation("RevokeAccountDevice", race_device["deviceId"], {}, 1)
    async def global_revoke():
        response = await client.post(f"/v1/me/devices/{race_device['deviceId']}/revoke", headers=access.authorization(assistant))
        access.expect(response, 204)
    async def local_restore():
        response = await client.post(base + "/sync/operations", headers=access.authorization(owner), json={"operations": [{
            "operationId": str(uuid7()), "contractVersion": 1, "action": "RestoreAccountDevice",
            "entityKey": race_device["deviceId"], "expectedVersion": 2, "payload": {},
        }]})
        assert response.status_code in (200, 403)
    await asyncio.wait_for(asyncio.gather(global_revoke(), local_restore()), timeout=10)
    response = await client.get(base, headers=access.authorization(race_device))
    access.expect(response, 401)
    denied = await client.get(base + "/audit-events", headers=access.authorization(assistant))
    access.expect(denied, 403)
    response = await client.get(base + "/audit-events?action=HttpAccessDenied", headers=access.authorization(owner))
    access.expect(response, 200)
    assert any(item["correlationId"] == denied.headers["X-Correlation-ID"] for item in response.json()["items"])
    response = await client.get(base + f"/audit-events?action=UpdateAccountDetails&objectType=account&objectId={account_id}", headers=access.authorization(owner))
    access.expect(response, 200)
    assert any(item["operationId"] == str(details_id) for item in response.json()["items"])
    for item in response.json()["items"]:
        assert item["accountId"] == str(account_id)
        assert UUID(item["correlationId"]).version == 7
        assert item["occurredAt"].endswith("Z")
        assert not {"payload", "accessToken", "secretHash", "requestHash"} & set(item)
    response = await client.get(base + "/audit-events?page=999&shows=1", headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["items"] == [] and response.json()["total"] > 0
    for query in ("shows=501", "from=2026-10-26T00:00:00", "from=2026-10-27T00:00:00Z&until=2026-10-26T00:00:00Z", "unknown=fixture"):
        response = await client.get(base + "/audit-events?" + query, headers=access.authorization(owner))
        access.expect(response, 422)
    response = await client.get(other_base + "/audit-events", headers=access.authorization(owner))
    access.expect(response, 404)

    from src.api.audit.repository.dao import dao_events
    original_create = dao_events.create
    async def fail_audit(db, **kwargs):
        return await original_create(db, **{**kwargs, "obj_in": {**kwargs["obj_in"], "outcome": "invalid"}})
    with patch.object(dao_events, "create", side_effect=fail_audit):
        response = await client.post(f"/v1/me/devices/{owner['deviceId']}/rotate-token", headers=access.authorization(owner), json={})
        access.expect(response, 503)
    response = await client.get("/v1/me", headers=access.authorization(owner))
    access.expect(response, 200)
    response = await client.post(f"/v1/me/devices/{owner['deviceId']}/rotate-token", headers=access.authorization(owner), json={})
    access.expect(response, 201)
    owner["accessToken"] = response.json()["accessToken"]
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE action='RotateDeviceToken' AND correlation_id=:id"), {"id": UUID(response.headers["X-Correlation-ID"])}) == 1

    # Prepare an old receipt without changing the PostgreSQL clock.
    from src.api.sync.repository.dao import dao_heads
    async with administrative() as db:
        old = await dao_heads.get_server_time(db) - timedelta(days=91)
    expired_id = uuid7()
    with patch.object(dao_heads, "get_server_time", return_value=old):
        assert (await operation("FutureOperation", account_id, {}, operation_id=expired_id))["status"] == "rejected"
    async with administrative() as db:
        original_hash = await db.scalar(text("SELECT request_hash FROM nightingale.operation_receipts WHERE operation_id=:id"), {"id": expired_id})
        preserved = tuple((await db.execute(text("SELECT (SELECT count(*) FROM nightingale.operation_receipts),(SELECT count(*) FROM nightingale.change_log),(SELECT count(*) FROM nightingale.audit_events WHERE account_id=:id)"), {"id": account_id})).one())
    async def maintenance(username, password):
        environment = dict(os.environ)
        environment["MAINTENANCE_DATABASE_URI"] = support["postgres"].database_url(username, password)
        environment["PYTHONPATH"] = str(ROOT)
        result = await asyncio.to_thread(subprocess.run, [sys.executable, str(ROOT / "scripts/purge_expired_results.py")], env=environment, capture_output=True, text=True, timeout=30)
        assert "Traceback" not in result.stderr and password not in result.stderr
        return result
    rejected = await maintenance("nightingale_app", support["postgres"].APP_PASSWORD)
    assert rejected.returncode == 2 and "PERMISSION_DENIED" in rejected.stderr
    for expected in (1, 0):
        completed = await maintenance("nightingale_migrator", support["postgres"].MIGRATOR_PASSWORD)
        assert completed.returncode == 0 and json.loads(completed.stdout) == {"purgedResults": expected}
    async with administrative() as db:
        remaining = tuple((await db.execute(text("SELECT (SELECT count(*) FROM nightingale.operation_receipts),(SELECT count(*) FROM nightingale.change_log),(SELECT count(*) FROM nightingale.audit_events WHERE account_id=:id)"), {"id": account_id})).one())
        assert remaining == preserved
        receipt = (await db.execute(text("SELECT request_hash,result_json,purged_at,result_expires_at FROM nightingale.operation_receipts WHERE operation_id=:id"), {"id": expired_id})).one()
        assert receipt.request_hash == original_hash and receipt.result_json is None and receipt.purged_at >= receipt.result_expires_at
    response = await client.get(base + f"/sync/operations/{expired_id}", headers=access.authorization(owner))
    access.expect(response, 410)
    assert (await operation("FutureOperation", account_id, {"changed": True}, operation_id=expired_id))["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    print("Team checks passed: directed invitations, 72-hour expiry, atomic acceptance, membership permissions, concurrent revoke/accept and lost response.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_team))
