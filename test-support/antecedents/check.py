import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_antecedents(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.core.db import DAOError
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-antecedent-signing-key-2026")
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
    await operation("CreatePatientEncounter", encounter, {"patientId": str(patient), "attendingProfessionalId": str(professional_id)})

    family, personal, other = uuid7(), uuid7(), uuid7()
    family_id = uuid7()
    family_payload = {
        "patientId": str(patient), "encounterId": str(encounter), "category": "family",
        "content": "PRIV-FAMILIAR", "relatedPersonDescription": "Fixture relative",
        "occurrenceDate": "2020", "sourceType": "related_person",
    }
    created_family = await operation("CreatePatientAntecedent", family, family_payload, actor=assistant, operation_id=family_id)
    assert created_family["status"] == "accepted" and created_family["state"]["occurrenceDate"] == "2020"
    duplicate = await operation("CreatePatientAntecedent", family, family_payload, actor=assistant, operation_id=family_id)
    assert duplicate["status"] == "duplicate"
    await operation("CreatePatientAntecedent", personal, {
        "patientId": str(patient), "category": "personal", "content": "PRIV-PERSONAL",
        "occurrenceDate": "2020-05", "sourceType": "patient",
    }, actor=assistant)
    await operation("CreatePatientAntecedent", other, {
        "patientId": str(patient), "category": "other", "content": "PRIV-OTRO",
    }, actor=assistant)
    assert (await get(f"/patients/{patient}/antecedents"))["total"] == 3
    assert (await get(f"/patients/{patient}/antecedents?category=family"))["total"] == 1
    missing = await operation("CreatePatientAntecedent", uuid7(), {
        "patientId": str(patient), "category": "family", "content": "Fixture missing",
    }, actor=assistant)
    assert missing["status"] == "rejected"
    assert (await operation("UpdatePatientAntecedent", family, {"relatedPersonDescription": None}, 1, actor=assistant))["status"] == "rejected"
    updated = await operation("UpdatePatientAntecedent", family, {"sourceType": "external_document"}, 1, actor=assistant)
    assert updated["entityVersion"] == 2
    history = (await get(f"/patients/{patient}/antecedents/{family}/history"))["items"]
    assert len(history) == 2 and history[0]["relatedPersonDescription"] == "Fixture relative"
    await operation("InvalidatePatientAntecedent", other, {}, 1, actor=assistant)
    assert (await get(f"/patients/{patient}/antecedents"))["total"] == 2

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    antecedents = [item for item in items if item["entityType"] == "patient_antecedent"]
    assert {item["entityKey"] for item in antecedents} == {str(family), str(personal)}
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.patient_conditions")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        row = (await db.execute(text("SELECT occurrence_date,date_precision FROM nightingale.patient_clinical_timeline WHERE entry_type='antecedent' AND entry_id=:id"), {"id": family})).one()
        assert row == ("2020", "year")

    retry, retry_antecedent = uuid7(), uuid7()
    retry_payload = {"patientId": str(patient), "category": "other", "content": "PRIV-ROLLBACK"}
    with patch("src.api.sync.application.operations_cases.apply_antecedent_operation", side_effect=DAOError("Fixture rollback")):
        failed = await operation("CreatePatientAntecedent", retry_antecedent, retry_payload, operation_id=retry)
    assert failed["status"] == "retryable_failure"
    assert (await operation("CreatePatientAntecedent", retry_antecedent, retry_payload, operation_id=retry))["status"] == "accepted"

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"antecedents": "none"}}, 1)
    await get(f"/patients/{patient}/antecedents", actor=assistant, status=403)
    await operation("CreatePatientAntecedent", family, family_payload, actor=assistant, operation_id=family_id, status=403)
    print("Antecedent checks passed: categories, related person, uncertainty, history, sync, rollback, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_antecedents))
