import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_medications(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.core.db import DAOError
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-medication-signing-key-2026")
    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        identity = (await identified_users(db, [UUID(owner["userId"])]))[UUID(owner["userId"])]
    async with administrative() as db:
        created = await bootstrap_practice(db, BootstrapPracticeInput(
            owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
            owner_name="Fixture Owner", professional_name="Fixture Professional",
            display_name="Fixture Practice", time_zone="America/Caracas",
            location_name="Fixture Office", location_address="Fictional address",
            location_country="VE", location_state="Fixture State", location_city="Fixture City",
        ))
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, status=200):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1,
            "action": action, "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def get(path, actor=owner, status=200):
        response = await client.get(base + path, headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    await operation("RegisterAccountDevice", owner["deviceId"], {})
    invitation = uuid7()
    await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]})
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant)
    patient = uuid7()
    await operation("RegisterPatient", patient, {"fullName": "Fixture Patient"})

    declared, operation_id = uuid7(), uuid7()
    payload = {
        "patientId": str(patient), "medicationName": "PRIV-E15-METFORMINA",
        "sourceType": "other_professional", "startDate": "2021-03",
    }
    created = await operation("DeclarePatientMedication", declared, payload, actor=assistant, operation_id=operation_id)
    assert created["status"] == "accepted"
    assert created["state"]["startDate"] == "2021-03"
    assert created["state"]["doseDescription"] is None
    assert created["state"]["prescriberName"] is None
    assert created["state"]["reviewStatus"] == "declared"
    duplicate = await operation("DeclarePatientMedication", declared, payload, actor=assistant, operation_id=operation_id)
    assert duplicate["status"] == "duplicate"
    no_source = await operation("DeclarePatientMedication", uuid7(), {
        "patientId": str(patient), "medicationName": "Fixture",
    }, actor=assistant)
    assert no_source["status"] == "rejected"

    updated = await operation("UpdatePatientDeclaredMedication", declared, {
        "endDate": "2021-08", "correctionReason": "Fin conocido",
    }, 1, actor=assistant)
    assert updated["entityVersion"] == 2
    reviewed = await operation("ReviewPatientDeclaredMedication", declared, {}, 2, actor=assistant)
    assert reviewed["entityVersion"] == 3
    assert reviewed["state"]["reviewStatus"] == "reviewed"
    assert reviewed["state"]["sourceType"] == "other_professional"
    assert reviewed["state"]["reviewedByUserId"] == assistant["userId"]

    history = (await get(f"/patients/{patient}/declared-medications/{declared}/history"))["items"]
    assert len(history) == 3 and history[0]["action"] == "created"
    listed = await get(f"/patients/{patient}/declared-medications?reviewStatus=reviewed")
    assert listed["total"] == 1 and listed["items"][0]["medicationName"] == "PRIV-E15-METFORMINA"

    history = (await get(f"/patients/{patient}/clinical-history?sections=declared_medications"))["items"]
    assert any(entry["entryType"] == "declared_medication" and entry["entryId"] == str(declared) for entry in history), "timeline integra medicación declarada"

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    medications = [item for item in items if item["entityType"] == "declared_medication"]
    assert [item["entityKey"] for item in medications] == [str(declared)]
    assert medications[0]["state"]["startDate"] == "2021-03"
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.declared_medication_histories WHERE id=:id"), {"id": declared}) == 3

    retry, retry_medication = uuid7(), uuid7()
    retry_payload = {"patientId": str(patient), "medicationName": "Fixture rollback", "sourceType": "patient"}
    with patch("src.api.sync.application.operations_cases.apply_declared_medication_operation", side_effect=DAOError("Fixture rollback")):
        failed = await operation("DeclarePatientMedication", retry_medication, retry_payload, operation_id=retry)
    assert failed["status"] == "retryable_failure"
    assert (await operation("DeclarePatientMedication", retry_medication, retry_payload, operation_id=retry))["status"] == "accepted"

    await operation("InvalidatePatientDeclaredMedication", retry_medication, {"correctionReason": "Duplicado"}, 1)
    assert (await get(f"/patients/{patient}/declared-medications"))["total"] == 1

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"declaredMedications": "none"}}, 1)
    await get(f"/patients/{patient}/declared-medications", actor=assistant, status=403)
    await operation("DeclarePatientMedication", declared, payload, actor=assistant, operation_id=operation_id, status=403)
    print("Medication checks passed: E15 source/period/uncertainty, review, versions, sync, rollback, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_medications))
