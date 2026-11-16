import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_notes(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.core.db import DAOError
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-note-signing-key-2026")
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
    professional_id = created.value.professional_id
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
    encounter = uuid7()
    await operation("CreatePatientEncounter", encounter, {
        "patientId": str(patient), "attendingProfessionalId": str(professional_id),
    })
    before_visit = await get(f"/patients/{patient}/last-visit")

    note, linked = uuid7(), uuid7()
    note_operation = uuid7()
    created_note = await operation("CreatePatientNote", note, {
        "patientId": str(patient), "body": "PRIV-E07-NOTA",
        "capturedAtLocal": "2026-11-02T14:00:00-04:00",
    }, actor=assistant, operation_id=note_operation)
    assert created_note["status"] == "accepted" and created_note["state"]["createdAt"].endswith("Z")
    assert created_note["state"]["capturedAtLocal"] == "2026-11-02T18:00:00Z"
    duplicate = await operation("CreatePatientNote", note, {
        "patientId": str(patient), "body": "PRIV-E07-NOTA",
        "capturedAtLocal": "2026-11-02T14:00:00-04:00",
    }, actor=assistant, operation_id=note_operation)
    assert duplicate["status"] == "duplicate"
    await operation("CreatePatientNote", linked, {
        "patientId": str(patient), "encounterId": str(encounter), "body": "Linked fixture",
    }, actor=assistant)
    assert (await get(f"/patients/{patient}/notes"))["total"] == 2
    assert (await get(f"/patients/{patient}/notes?encounterId={encounter}"))["total"] == 1
    assert (await get(f"/patients/{patient}/last-visit")) == before_visit

    assert (await operation("UpdatePatientNote", note, {"body": "PRIV-E07-NOTA"}, 1, actor=assistant))["error"]["code"] == "NO_CHANGES"
    updated = await operation("UpdatePatientNote", note, {"body": "PRIV-E07-CORREGIDA"}, 1, actor=assistant)
    assert updated["entityVersion"] == 2
    history = (await get(f"/patients/{patient}/notes/{note}/history"))["items"]
    assert [row["version"] for row in history] == [1, 2]
    assert history[0]["body"] == "PRIV-E07-NOTA"
    conflict = await operation("UpdatePatientNote", note, {"body": "Old version"}, 1, actor=assistant)
    assert conflict["status"] == "conflict"
    await operation("InvalidatePatientNote", linked, {}, 1, actor=assistant)
    assert (await get(f"/patients/{patient}/notes"))["total"] == 1

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    notes = [item for item in items if item["entityType"] == "patient_note"]
    assert [item["entityKey"] for item in notes] == [str(note)]
    assert notes[0]["state"]["body"] == "PRIV-E07-CORREGIDA"

    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.patient_conditions")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.patient_allergy_intolerances")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.patient_clinical_timeline WHERE entry_type='note'")) == 2

    retry, retry_note = uuid7(), uuid7()
    payload = {"patientId": str(patient), "body": "PRIV-E07-ROLLBACK"}
    with patch("src.api.sync.application.operations_cases.apply_note_operation", side_effect=DAOError("Fixture rollback")):
        failed = await operation("CreatePatientNote", retry_note, payload, operation_id=retry)
    assert failed["status"] == "retryable_failure"
    assert (await operation("CreatePatientNote", retry_note, payload, operation_id=retry))["status"] == "accepted"

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"notes": "read"}}, 1)
    await operation("CreatePatientNote", note, {
        "patientId": str(patient), "body": "PRIV-E07-NOTA", "capturedAtLocal": "2026-11-02T14:00:00-04:00",
    }, actor=assistant, operation_id=note_operation, status=403)
    response = await client.get(base + f"/sync/operations/{note_operation}", headers=access.authorization(assistant))
    access.expect(response, 403)
    assert (await get(f"/patients/{patient}/notes", actor=assistant))["total"] == 2
    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"notes": "none"}}, 2)
    await get(f"/patients/{patient}/notes", actor=assistant, status=403)
    print("Note checks passed: independent/linked notes, versions, history, no derived effects, sync, rollback and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_notes))
