import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_clinical_permissions(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        users = await identified_users(db, [UUID(owner["userId"])])
    identity = users[UUID(owner["userId"])]
    data = BootstrapPracticeInput(
        owner_issuer=identity.oidc_issuer,
        owner_subject=identity.oidc_subject,
        owner_name="Fixture Owner",
        professional_name="Fixture Professional",
        display_name="Fixture Practice",
        time_zone="America/Caracas",
        location_name="Fixture Office",
        location_address="Fictional address",
        location_country="VE",
        location_state="Fixture State",
        location_city="Fixture City",
    )
    async with administrative() as db:
        created = await bootstrap_practice(db, data)
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, status=200):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1, "action": action,
            "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def accept(invitation_id):
        response = await client.post(
            f"/v1/me/invitations/{invitation_id}/accept",
            headers=access.authorization(assistant),
            json={"operationId": str(uuid7())},
        )
        access.expect(response, 200)

    async def state():
        async with administrative() as db:
            return (await db.execute(text("""
                SELECT m.version,m.clinical_profile_access,m.conditions_access,m.allergies_access,
                    h.permission_epoch,
                    (SELECT count(*) FROM nightingale.operation_receipts WHERE account_id=m.account_id),
                    (SELECT count(*) FROM nightingale.audit_events WHERE account_id=m.account_id),
                    (SELECT count(*) FROM nightingale.change_log WHERE account_id=m.account_id)
                FROM nightingale.account_memberships m
                JOIN nightingale.account_sync_heads h ON h.account_id=m.account_id
                WHERE m.account_id=:account_id AND m.user_id=:user_id
            """), {"account_id": account_id, "user_id": UUID(assistant["userId"])})).one()

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    invitation = uuid7()
    assert (await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))["status"] == "accepted"
    await accept(invitation)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"
    initial = await state()
    assert initial[1:4] == ("read_write", "read_write", "read_write")

    response = await client.get(base + "/access", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert response.json()["clinicalPermissions"] == {
        "clinicalProfile": "read_write", "conditions": "read_write", "allergies": "read_write"
    }
    assert "SetMemberClinicalPermissions" not in response.json()["allowedActions"]

    permissions = {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}
    operation_id = uuid7()
    changed = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1, operation_id=operation_id)
    assert changed["status"] == "accepted" and changed["entityVersion"] == 2, changed
    assert changed["state"]["clinicalPermissions"] == permissions
    duplicate = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1, operation_id=operation_id)
    assert duplicate["status"] == "duplicate" and duplicate["originalResult"]["status"] == "accepted"
    conflict = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {**permissions, "conditions": "read_write"}}, 1, operation_id=operation_id)
    assert conflict["status"] == "conflict" and conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 2))["error"]["code"] == "NO_CHANGES"
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1))["error"]["code"] == "VERSION_CONFLICT"
    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 2, actor=assistant, status=403)
    await operation("SetMemberClinicalPermissions", owner["userId"], {"clinicalPermissions": permissions}, 1, status=403)

    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["clinicalPermissions"] == permissions and response.json()["membershipVersion"] == 2
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(assistant))
    access.expect(response, 403)
    response = await client.get(base + "/access", headers=access.authorization(assistant))
    assert response.json()["clinicalPermissions"] == permissions

    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 2))["entityVersion"] == 3
    assert (await state())[1:4] == ("none", "read", "read_write")
    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "active"}, 3))["entityVersion"] == 4
    assert (await state())[1:4] == ("none", "read", "read_write")

    before = await state()
    original_append = dao_changes.append
    retry_id = uuid7()
    updated = {"clinicalProfile": "read", "conditions": "none", "allergies": "read"}
    async def fail_group(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_group):
        failed = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": updated}, 4, operation_id=retry_id)
    assert failed["status"] == "retryable_failure" and failed["error"]["code"] == "TEMPORARY_FAILURE"
    assert await state() == before
    recovered = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": updated}, 4, operation_id=retry_id)
    assert recovered["status"] == "accepted" and recovered["entityVersion"] == 5
    after = await state()
    assert after[0] == 5 and after[1:4] == ("read", "none", "read")
    assert after[4] == before[4] + 1 and after[5:] == tuple(value + 1 for value in before[5:])

    first_id = uuid7()
    second_id = uuid7()
    first_permissions = {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}
    second_permissions = {"clinicalProfile": "read_write", "conditions": "none", "allergies": "read"}
    first, second = await asyncio.gather(
        operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": first_permissions}, 5, operation_id=first_id),
        operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": second_permissions}, 5, operation_id=second_id),
    )
    assert sorted(item["status"] for item in (first, second)) == ["accepted", "conflict"]
    winner = first if first["status"] == "accepted" else second
    assert winner["state"]["clinicalPermissions"] in (first_permissions, second_permissions)
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(owner))
    assert response.json()["clinicalPermissions"] == winner["state"]["clinicalPermissions"]
    assert response.json()["membershipVersion"] == 6

    owner_second = await access.issue(client, tokens[0]["access_token"])
    assert (await operation("RegisterAccountDevice", owner_second["deviceId"], {}, actor=owner_second))["status"] == "accepted"
    assert (await operation("RevokeAccountDevice", owner["deviceId"], {}, 1, actor=owner_second))["status"] == "accepted"
    response = await client.get(base + f"/sync/operations/{winner['operationId']}", headers=access.authorization(owner))
    access.expect(response, 403)
    response = await client.get(base + f"/sync/operations/{winner['operationId']}", headers=access.authorization(owner_second))
    access.expect(response, 200)
    assert response.json()["state"]["clinicalPermissions"] == winner["state"]["clinicalPermissions"]
    response = await client.get(base + f"/members/{outsider['userId']}/clinical-permissions", headers=access.authorization(owner_second))
    access.expect(response, 404)
    print("Clinical permission checks passed: defaults, section levels, versions, idempotency, races, rollback and device revocation.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_permissions))
