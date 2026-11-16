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


async def check_conditions(runtime, administrative, client, tokens):
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
        owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
        owner_name="Fixture Owner", professional_name="Fixture Professional",
        display_name="Fixture Practice", time_zone="America/Caracas",
        location_name="Fixture Office", location_address="Fictional address",
        location_country="VE", location_state="Fixture State", location_city="Fixture City",
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

    async def review(actor=owner, status=200):
        response = await client.get(base + f"/patients/{patient_id}/clinical-sections/conditions", headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    async def history_total(table):
        async with administrative() as db:
            return await db.scalar(text(f"SELECT count(*) FROM nightingale.{table} WHERE account_id=:id"), {"id": account_id})

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    invitation = uuid7()
    assert (await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))["status"] == "accepted"
    response = await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())})
    access.expect(response, 200)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"
    patient_id = uuid7()
    assert (await operation("RegisterPatient", patient_id, {"fullName": "Fixture Patient"}))["status"] == "accepted"

    initial = await review()
    assert initial["informationStatus"] == "not_recorded" and initial["version"] == 0
    none_known = await operation("SetPatientClinicalSectionReview", patient_id, {"section": "conditions", "informationStatus": "none_known", "sourceType": "patient"})
    assert none_known["status"] == "accepted" and none_known["entityVersion"] == 1

    condition_id = uuid7()
    create_id = uuid7()
    created_condition = await operation("CreatePatientCondition", condition_id, {"patientId": str(patient_id), "name": "CND-A", "onsetDate": "2024-02-29", "abatementDate": "2024-03"}, operation_id=create_id)
    assert created_condition["status"] == "accepted" and created_condition["entityVersion"] == 1
    assert (await review())["informationStatus"] == "has_entries"
    duplicate = await operation("CreatePatientCondition", condition_id, {"patientId": str(patient_id), "name": "CND-A", "onsetDate": "2024-02-29", "abatementDate": "2024-03"}, operation_id=create_id)
    assert duplicate["status"] == "duplicate"
    second_id = uuid7()
    assert (await operation("CreatePatientCondition", second_id, {"patientId": str(patient_id), "name": "CND-A"}))["status"] == "accepted"
    for payload in ({"patientId": str(patient_id), "name": " "}, {"patientId": str(patient_id), "name": "CND-A", "onsetDate": "2023-02-29"}, {"patientId": str(patient_id), "name": "CND-A", "onsetDate": "2999"}):
        assert (await operation("CreatePatientCondition", uuid7(), payload))["error"]["code"] == "VALIDATION_ERROR"

    updated = await operation("UpdatePatientCondition", condition_id, {"clinicalStatus": "resolved", "verificationStatus": "confirmed", "onsetDate": "2024", "abatementDate": "2024-03"}, 1)
    assert updated["status"] == "accepted" and updated["entityVersion"] == 2, updated
    assert (await operation("UpdatePatientCondition", condition_id, {"verificationStatus": "refuted"}, 2))["entityVersion"] == 3
    assert (await review())["informationStatus"] == "has_entries"
    assert (await operation("InvalidatePatientCondition", second_id, {"correctionReason": "Fixture wrong patient"}, 1))["entityVersion"] == 2
    assert (await review())["informationStatus"] == "unknown"
    assert (await operation("UpdatePatientCondition", second_id, {"clinicalStatus": "active"}, 2))["error"]["code"] == "INVALID_STATE_TRANSITION"

    response = await client.get(base + f"/patients/{patient_id}/conditions", headers=access.authorization(owner))
    assert [str(item["conditionId"]) for item in response.json()["items"]] == [str(condition_id)]
    response = await client.get(base + f"/patients/{patient_id}/conditions?includeEnteredInError=true", headers=access.authorization(owner))
    assert response.json()["total"] == 2
    response = await client.get(base + f"/patients/{patient_id}/conditions/{condition_id}/history", headers=access.authorization(owner))
    assert [item["version"] for item in response.json()["items"]] == [1, 2, 3]

    reviewed = await operation("SetPatientClinicalSectionReview", patient_id, {"section": "conditions", "informationStatus": "none_known", "sourceType": "patient"}, 3)
    assert reviewed["status"] == "accepted"
    third_id = uuid7()
    assert (await operation("CreatePatientCondition", third_id, {"patientId": str(patient_id), "name": "Fixture condition"}))["status"] == "accepted"
    fourth_id = uuid7()
    create = operation("CreatePatientCondition", fourth_id, {"patientId": str(patient_id), "name": "Concurrent condition"})
    absent = operation("SetPatientClinicalSectionReview", patient_id, {"section": "conditions", "informationStatus": "none_known"}, (await review())["version"])
    create_result, absent_result = await asyncio.gather(create, absent)
    assert create_result["status"] == "accepted"
    assert absent_result["status"] in ("accepted", "rejected")
    assert (await review())["informationStatus"] == "has_entries"

    before = await history_total("patient_conditions")
    before_receipts = await history_total("operation_receipts")
    original_append = dao_changes.append
    retry_id = uuid7()
    async def fail_group(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_group):
        failed = await operation("UpdatePatientCondition", condition_id, {"clinicalStatus": "active"}, 3, operation_id=retry_id)
    assert failed["status"] == "retryable_failure"
    assert await history_total("patient_conditions") == before and await history_total("operation_receipts") == before_receipts
    recovered = await operation("UpdatePatientCondition", condition_id, {"clinicalStatus": "active"}, 3, operation_id=retry_id)
    assert recovered["status"] == "accepted" and recovered["entityVersion"] == 4

    assistant_write = await operation("UpdatePatientCondition", condition_id, {"sourceType": "professional"}, 4, actor=assistant)
    assert assistant_write["status"] == "accepted"
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"clinicalProfile": "read_write", "conditions": "none", "allergies": "read_write"}}, 1))["entityVersion"] == 2
    await review(assistant, 403)
    await operation("UpdatePatientCondition", condition_id, {"sourceType": "patient"}, 5, actor=assistant, status=403)
    response = await client.get(base + f"/sync/operations/{assistant_write['operationId']}", headers=access.authorization(assistant))
    access.expect(response, 403)
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"clinicalProfile": "read_write", "conditions": "read_write", "allergies": "read_write"}}, 2))["entityVersion"] == 3
    await review(assistant)
    await review(outsider, 404)

    for factory, statement in (
        (runtime, "UPDATE nightingale.patient_condition_histories SET name='altered'"),
        (administrative, "DELETE FROM nightingale.patient_condition_histories"),
        (administrative, "UPDATE nightingale.patient_clinical_section_review_histories SET information_status='none_known'"),
    ):
        try:
            async with factory() as db:
                async with db.begin():
                    await db.execute(text(statement))
        except DBAPIError:
            pass
        else:
            raise AssertionError("Condition history was modified")
    print("Condition checks passed: states, partial dates, section reviews, idempotency, races, permissions and rollback.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_conditions))
