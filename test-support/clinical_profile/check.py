import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_clinical_profile(runtime, administrative, client, tokens):
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

    async def profile(actor=owner, status=200):
        response = await client.get(base + f"/patients/{patient_id}/clinical-profile", headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT p.version,
                    (SELECT count(*) FROM nightingale.patient_clinical_profile_histories h WHERE h.account_id=p.account_id AND h.patient_id=p.patient_id),
                    (SELECT count(*) FROM nightingale.operation_receipts r WHERE r.account_id=p.account_id),
                    (SELECT count(*) FROM nightingale.audit_events a WHERE a.account_id=p.account_id),
                    (SELECT count(*) FROM nightingale.change_log c WHERE c.account_id=p.account_id)
                FROM nightingale.patient_clinical_profiles p
                WHERE p.account_id=:account_id AND p.patient_id=:patient_id
            """), {"account_id": account_id, "patient_id": patient_id})).one())

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    invitation = uuid7()
    assert (await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))["status"] == "accepted"
    response = await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())})
    access.expect(response, 200)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"
    patient_id = uuid7()
    registered = await operation("RegisterPatient", patient_id, {"fullName": "Fixture Patient", "birthDate": "2000-02-29"})
    assert registered["status"] == "accepted" and registered["entityVersion"] == 1
    empty = await profile()
    assert empty["version"] == 0 and empty["sexAtBirth"] is None and empty["ageYears"] == 26
    assert empty["birthDate"] == "2000-02-29" and empty["patientVersion"] == 1
    response = await client.get(base + f"/patients/{patient_id}/clinical-profile/history", headers=access.authorization(owner))
    assert response.json()["total"] == 0

    first_id = uuid7()
    first = await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown", "sourceType": "patient"}, operation_id=first_id)
    assert first["status"] == "accepted" and first["entityVersion"] == 1, first
    duplicate = await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown", "sourceType": "patient"}, operation_id=first_id)
    assert duplicate["status"] == "duplicate"
    assert (await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown", "sourceType": "patient"}, 1))["error"]["code"] == "NO_CHANGES"
    assert (await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "female", "sourceType": "professional"}, 1))["entityVersion"] == 2
    assert (await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": None, "sourceType": "unknown"}, 2))["entityVersion"] == 3
    response = await client.get(base + f"/patients/{patient_id}/clinical-profile/history?shows=2&page=2", headers=access.authorization(owner))
    assert response.json()["total"] == 3 and len(response.json()["items"]) == 1
    assert [item["version"] for item in response.json()["items"]] == [3]
    response = await client.get(base + f"/patients/{patient_id}/clinical-profile/history?afterVersion=1", headers=access.authorization(owner))
    assert [item["version"] for item in response.json()["items"]] == [2, 3]

    before = await counts()
    original_append = dao_changes.append
    retry_id = uuid7()
    async def fail_group(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_group):
        failed = await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "other", "sourceType": "patient"}, 3, operation_id=retry_id)
    assert failed["status"] == "retryable_failure"
    assert await counts() == before
    recovered = await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "other", "sourceType": "patient"}, 3, operation_id=retry_id)
    assert recovered["status"] == "accepted" and recovered["entityVersion"] == 4
    assert (await counts())[0:2] == (4, 4)

    first_update = operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "female", "sourceType": "patient"}, 4)
    second_update = operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "male", "sourceType": "patient"}, 4)
    first_result, second_result = await asyncio.gather(first_update, second_update)
    assert sorted(item["status"] for item in (first_result, second_result)) == ["accepted", "conflict"]
    winner = first_result if first_result["status"] == "accepted" else second_result
    assert winner["entityVersion"] == 5 and (await counts())[0:2] == (5, 5)

    changed_birth = await operation("UpdatePatientProfile", patient_id, {"birthDate": "1999-02-28"}, 1)
    assert changed_birth["status"] == "accepted" and changed_birth["entityVersion"] == 2
    response = await client.get(base + f"/patients/{patient_id}/birth-date-changes", headers=access.authorization(owner))
    changes = response.json()
    assert changes["total"] == 1
    assert changes["items"][0]["previousBirthDate"] == "2000-02-29"
    assert changes["items"][0]["newBirthDate"] == "1999-02-28"
    assert changes["items"][0]["patientVersion"] == 2

    assistant_write = await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown"}, 5, actor=assistant)
    assert assistant_write["status"] == "accepted" and assistant_write["entityVersion"] == 6
    denied_id = assistant_write["operationId"]
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}}, 1))["entityVersion"] == 2
    await profile(assistant, 403)
    await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown"}, 5, actor=assistant, status=403)
    response = await client.get(base + f"/sync/operations/{denied_id}", headers=access.authorization(assistant))
    access.expect(response, 403)
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"clinicalProfile": "read_write", "conditions": "read", "allergies": "read_write"}}, 2))["entityVersion"] == 3
    await profile(assistant)

    await profile(outsider, 404)
    response = await client.get(base + f"/patients/{uuid7()}/clinical-profile", headers=access.authorization(owner))
    access.expect(response, 404)
    for factory, statement in (
        (runtime, "UPDATE nightingale.patient_clinical_profile_histories SET source_type='external_document'"),
        (administrative, "DELETE FROM nightingale.patient_clinical_profile_histories"),
        (administrative, "INSERT INTO nightingale.patient_clinical_profile_histories(account_id,patient_id,version,source_type,action,actor_user_id,operation_id,changed_at) SELECT account_id,patient_id,99,'unknown','set',actor_user_id,operation_id,changed_at FROM nightingale.patient_clinical_profile_histories LIMIT 1"),
        (administrative, "UPDATE nightingale.patient_birth_date_changes SET new_birth_date='2001-01-01'"),
    ):
        try:
            async with factory() as db:
                async with db.begin():
                    await db.execute(text(statement))
        except DBAPIError:
            pass
        else:
            raise AssertionError("Clinical history was modified")

    async with administrative() as db:
        events = (await db.execute(text("SELECT action,object_key,object_type FROM nightingale.audit_events WHERE action LIKE 'ReadClinicalProfile%' OR action='ReadBirthDateChanges'"))).all()
        assert events and all(set(event._mapping).issubset({"action", "object_key", "object_type"}) for event in events)
        assert all("female" not in str(event) and "2000-02-29" not in str(event) for event in events)
    print("Clinical profile checks passed: absent profile, age, versions, history, birth changes, isolation, races and rollback.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_profile))
