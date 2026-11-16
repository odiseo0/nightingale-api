import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_clinical_history(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.core.db import DAOError
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-clinical-history-signing-key-2026")
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
    encounter, note, measurement, immunization, antecedent, condition, allergy = [uuid7() for _ in range(7)]
    await operation("CreatePatientEncounter", encounter, {"patientId": str(patient), "attendingProfessionalId": str(professional_id), "occurredAt": "2020-01-02T10:00:00Z"})
    await operation("CreatePatientNote", note, {"patientId": str(patient), "body": "PRIV-NOTE"})
    await operation("RecordPatientMeasurement", measurement, {"patientId": str(patient), "kind": "weight", "value": 70, "unit": "kg", "measuredAt": "2020-01-03T10:00:00Z"})
    await operation("RecordPatientImmunization", immunization, {"patientId": str(patient), "vaccineName": "PRIV-VACCINE", "occurrenceDate": "2020-05"})
    await operation("CreatePatientAntecedent", antecedent, {"patientId": str(patient), "category": "other", "content": "PRIV-ANTECEDENT", "occurrenceDate": "2020"})
    await operation("CreatePatientCondition", condition, {"patientId": str(patient), "name": "PRIV-CONDITION", "onsetDate": "2010"})
    await operation("CreatePatientAllergyIntolerance", allergy, {"patientId": str(patient), "substance": "PRIV-ALLERGY", "onsetDate": "2011-02"})

    history = await get(f"/patients/{patient}/clinical-history?shows=100", actor=assistant)
    assert history["total"] == 7
    assert {item["entryType"] for item in history["items"]} == {
        "encounter", "note", "measurement", "immunization", "antecedent", "condition", "allergy_intolerance"
    }
    assert all("body" not in item and "name" not in item and "value" not in item and "vaccineName" not in item and "substance" not in item for item in history["items"])
    filtered = await get(f"/patients/{patient}/clinical-history?sections=conditions&sections=allergies", actor=assistant)
    assert filtered["total"] == 2
    detail = await get(f"/patients/{patient}/conditions/{condition}", actor=assistant)
    assert detail["name"] == "PRIV-CONDITION"

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={
        "includeClinical": True, "appointmentsFrom": "2026-11-01", "appointmentsUntil": "2026-12-01",
    })
    access.expect(snapshot, 201)
    body = snapshot.json()
    items = (await get(f"/sync/snapshots/{body['snapshotId']}/items?shows=500", actor=assistant))["items"]
    expected_types = {
        "clinical_encounter", "patient_note", "patient_measurement", "patient_immunization",
        "patient_antecedent", "patient_condition", "patient_allergy_intolerance",
    }
    assert expected_types.issubset({item["entityType"] for item in items})
    await operation("UpdatePatientNote", note, {"body": "PRIV-NOTE-CORRECTED"}, 1)
    await operation("InvalidatePatientImmunization", immunization, {}, 1)
    delta = await get(f"/sync/changes?cursor={body['baseCursor']}", actor=assistant)
    changes = [change for group in delta["groups"] for change in group["changes"]]
    note_change = next(change for group in delta["groups"] for change in group["changes"] if change["entityType"] == "patient_note")
    invalid_change = next(change for group in delta["groups"] for change in group["changes"] if change["entityType"] == "patient_immunization")
    assert note_change["state"]["body"] == "PRIV-NOTE-CORRECTED"
    assert invalid_change["state"]["recordStatus"] == "entered-in-error"
    later = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(later, 201)
    later_items = (await get(f"/sync/snapshots/{later.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    assert not any(item["entityType"] == "patient_immunization" and item["entityKey"] == str(immunization) for item in later_items)

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"notes": "none", "immunizations": "none"}}, 1)
    partial = await get(f"/patients/{patient}/clinical-history?shows=100", actor=assistant)
    assert partial["total"] == 5
    assert not any(item["entryType"] in ("note", "immunization") for item in partial["items"])
    await get(f"/patients/{patient}/notes/{note}", actor=assistant, status=403)

    with patch("src.api.clinical_records.application.history_cases.record_clinical_read", side_effect=DAOError("Fixture audit failure")):
        await get(f"/patients/{patient}/clinical-history", status=503)
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
    print("Clinical history checks passed: all sources, permissions, precision, snapshot, delta, invalidation and audit rollback.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_history))
