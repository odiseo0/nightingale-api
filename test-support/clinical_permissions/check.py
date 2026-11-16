import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]

STAGE2_DEFAULTS = {
    "encounters": "read_write",
    "notes": "read_write",
    "measurements": "read_write",
    "immunizations": "read_write",
    "antecedents": "read_write",
}


async def check_clinical_permissions(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok
    from src.core.db import DAOError

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
                    m.encounters_access,m.notes_access,m.measurements_access,
                    m.immunizations_access,m.antecedents_access,h.permission_epoch,
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

    async def get_result(result_id, actor=assistant, status=200):
        response = await client.get(
            base + f"/sync/operations/{result_id}", headers=access.authorization(actor)
        )
        access.expect(response, status)
        return response.json()

    async def result_audits():
        async with administrative() as db:
            return (await db.execute(text("""
                SELECT object_key FROM nightingale.audit_events
                WHERE account_id=:account_id AND action='ReadOperationResult'
            """), {"account_id": account_id})).scalars().all()

    initial = await state()
    assert initial[1:9] == ("read_write",) * 8

    response = await client.get(base + "/access", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert response.json()["clinicalPermissions"] == {
        "clinicalProfile": "read_write",
        "conditions": "read_write",
        "allergies": "read_write",
        **STAGE2_DEFAULTS,
    }
    assert "SetMemberClinicalPermissions" not in response.json()["allowedActions"]

    permissions = {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}
    operation_id = uuid7()
    changed = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1, operation_id=operation_id)
    assert changed["status"] == "accepted" and changed["entityVersion"] == 2, changed
    assert changed["state"]["clinicalPermissions"] == {**permissions, **STAGE2_DEFAULTS}
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
    assert response.json()["clinicalPermissions"] == {**permissions, **STAGE2_DEFAULTS} and response.json()["membershipVersion"] == 2
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(assistant))
    access.expect(response, 403)
    response = await client.get(base + "/access", headers=access.authorization(assistant))
    assert response.json()["clinicalPermissions"] == {**permissions, **STAGE2_DEFAULTS}

    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 2))["entityVersion"] == 3
    assert (await state())[1:9] == ("none", "read", "read_write", "read_write", "read_write", "read_write", "read_write", "read_write")
    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "active"}, 3))["entityVersion"] == 4
    assert (await state())[1:9] == ("none", "read", "read_write", "read_write", "read_write", "read_write", "read_write", "read_write")

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
    assert after[0] == 5 and after[1:9] == ("read", "none", "read", "read_write", "read_write", "read_write", "read_write", "read_write")
    assert after[9] == before[9] + 1 and after[10:] == tuple(value + 1 for value in before[10:])

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
    assert winner["state"]["clinicalPermissions"] in (
        {**first_permissions, **STAGE2_DEFAULTS},
        {**second_permissions, **STAGE2_DEFAULTS},
    )
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(owner))
    assert response.json()["clinicalPermissions"] == winner["state"]["clinicalPermissions"]
    assert set(response.json()["clinicalPermissions"]) == {
        "clinicalProfile", "conditions", "allergies", *STAGE2_DEFAULTS
    }
    assert response.json()["membershipVersion"] == 6

    read_write = {"clinicalProfile": "none", "conditions": "read_write", "allergies": "read_write"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": read_write}, 6))["status"] == "accepted"
    patient_id = uuid7()
    assert (await operation("RegisterPatient", patient_id, {"fullName": "Fixture Patient"}))["status"] == "accepted"
    condition_id = uuid7()
    condition_payload = {"patientId": str(patient_id), "name": "Fixture condition"}
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id))["status"] == "accepted"
    allergy_review_id = uuid7()
    allergy_payload = {"section": "allergies", "informationStatus": "unknown"}
    assert (await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id))["status"] == "accepted"

    conditions_none = {"clinicalProfile": "none", "conditions": "none", "allergies": "read_write"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": conditions_none}, 7))["status"] == "accepted"
    await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id, status=403)
    await operation("CreatePatientCondition", condition_id, {**condition_payload, "name": "Changed"}, actor=assistant, operation_id=condition_id, status=403)
    await get_result(condition_id, status=403)
    duplicate = await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id)
    assert duplicate["status"] == "duplicate"
    assert (await get_result(allergy_review_id))["state"]["section"] == "allergies"

    allergies_none = {"clinicalProfile": "none", "conditions": "read_write", "allergies": "none"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": allergies_none}, 8))["status"] == "accepted"
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id))["status"] == "duplicate"
    assert (await get_result(condition_id))["state"]["name"] == "Fixture condition"
    await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id, status=403)
    await get_result(allergy_review_id, status=403)

    assistant_second = await access.issue(client, tokens[1]["access_token"])
    assert (await operation("RegisterAccountDevice", assistant_second["deviceId"], {}, actor=assistant_second))["status"] == "accepted"
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant_second, operation_id=condition_id))["status"] == "duplicate"
    assert (await get_result(condition_id, actor=assistant_second))["status"] == "accepted"
    await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant_second, operation_id=allergy_review_id, status=403)
    await get_result(allergy_review_id, actor=assistant_second, status=403)

    audits = await result_audits()
    assert len(audits) == 6 and set(audits) == {str(condition_id), str(allergy_review_id)}
    before_audits = len(audits)
    async def fail_audit(db, event):
        raise DAOError("Fixture audit failure")
    with patch("src.api.sync.application.operations_cases.record_control", side_effect=fail_audit):
        await get_result(condition_id, status=503)
    assert len(await result_audits()) == before_audits

    race_read = client.get(
        base + f"/sync/operations/{condition_id}", headers=access.authorization(assistant_second)
    )
    race_revoke = operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": conditions_none}, 9,
    )
    race_response, race_permission = await asyncio.gather(race_read, race_revoke)
    access.expect(race_response, race_response.status_code)
    assert race_response.status_code in (200, 403)
    assert race_permission["status"] == "accepted"
    await get_result(condition_id, actor=assistant_second, status=403)
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": allergies_none}, 10,
    ))["status"] == "accepted"

    routine_actions = {
        "encounters": "CreatePatientEncounter",
        "notes": "CreatePatientNote",
        "measurements": "RecordPatientMeasurement",
        "immunizations": "RecordPatientImmunization",
        "antecedents": "CreatePatientAntecedent",
    }
    routine_results = []
    for action in routine_actions.values():
        result_id = uuid7()
        result = await operation(
            action, uuid7(), {}, actor=assistant, operation_id=result_id
        )
        assert result["status"] == "rejected"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        routine_results.append(result_id)

    combined = {
        **allergies_none,
        "encounters": "none",
        "notes": "none",
        "measurements": "none",
        "immunizations": "none",
        "antecedents": "none",
    }
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": combined}, 11,
    ))["status"] == "accepted"
    for result_id in routine_results:
        await get_result(result_id, status=403)
    read_only = {**combined, **{section: "read" for section in routine_actions}}
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": read_only}, 12,
    ))["status"] == "accepted"
    for result_id in routine_results:
        await get_result(result_id, status=403)

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
