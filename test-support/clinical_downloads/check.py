import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_clinical_downloads(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.audit.repository.dao import dao_events
    from src.core import Ok
    from src.settings.api_settings import api_settings
    from pydantic import SecretStr

    api_settings.sync_signing_key = SecretStr("fixture-clinical-download-signing-key-2026")
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

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1, "action": action,
            "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
        access.expect(response, 200)
        return response.json()["results"][0]

    async def capture(actor=owner, include=False, status=201):
        response = await client.post(base + "/sync/snapshots", headers=access.authorization(actor), json={"includeClinical": include})
        assert response.status_code == status, response.text
        return response.json()

    async def items(snapshot_id, actor=owner, shows=500):
        response = await client.get(base + f"/sync/snapshots/{snapshot_id}/items?shows={shows}", headers=access.authorization(actor))
        access.expect(response, 200)
        return response.json()["items"]

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    patient_id = uuid7()
    assert (await operation("RegisterPatient", patient_id, {"fullName": "Fixture Patient", "birthDate": "2000-02-29", "phoneCode": "+58", "phone": "4120000000", "identificationBasis": "own_document"}))["status"] == "accepted"
    identifier_id = uuid7()
    assert (await operation("AddPatientIdentifier", identifier_id, {"patientId": str(patient_id), "documentType": "national_id", "documentNumber": "FIXTURE-001"}))["status"] == "accepted"
    assert (await operation("SetPatientCompletion", patient_id, {"completionStatus": "complete"}, 1))["status"] == "accepted"
    assert (await operation("SetPatientProfileStatus", patient_id, {"status": "inactive"}, 2))["status"] == "accepted"
    assert (await operation("SetPatientSexAtBirth", patient_id, {"sexAtBirth": "unknown", "sourceType": "patient"}))["status"] == "accepted"
    condition_id = uuid7()
    assert (await operation("CreatePatientCondition", condition_id, {"patientId": str(patient_id), "name": "CND-A", "onsetDate": "2020-01-01"}))["status"] == "accepted"
    allergy_id = uuid7()
    assert (await operation("CreatePatientAllergyIntolerance", allergy_id, {"patientId": str(patient_id), "substance": "ALG-A", "type": "unknown"}))["status"] == "accepted"

    plain = await capture()
    assert plain["clinicalSections"] == []
    plain_items = await items(plain["snapshotId"])
    assert not any(item["entityType"].startswith("patient_clinical") or item["entityType"] in ("patient_condition", "patient_allergy_intolerance") for item in plain_items)
    assert not any(item["entityType"] == "patient_profile" and item["state"]["patientId"] == str(patient_id) for item in plain_items)

    clinical = await capture(include=True)
    assert set(clinical["clinicalSections"]) == {
        "profile", "conditions", "allergies", "encounters", "notes",
        "measurements", "immunizations", "antecedents", "declared_medications",
        "care_plans", "diagnostic_reports", "specialty_templates",
    }
    clinical_items = await items(clinical["snapshotId"])
    types = {item["entityType"] for item in clinical_items}
    assert {"patient_clinical_profile", "patient_condition", "patient_allergy_intolerance", "patient_clinical_section_review"}.issubset(types)
    assert not any(item["entityType"].endswith("history") for item in clinical_items)
    assert any(item["entityType"] == "patient_allergy_intolerance" and item["state"]["substance"] == "ALG-A" for item in clinical_items)
    assert any(item["entityType"] == "patient_profile" and item["state"]["patientId"] == str(patient_id) for item in clinical_items)
    assert (await operation("UpdatePatientCondition", condition_id, {"clinicalStatus": "resolved"}, 1))["status"] == "accepted"
    response = await client.get(base + f"/sync/changes?cursor={clinical['baseCursor']}", headers=access.authorization(owner))
    access.expect(response, 200)
    assert any(change["entityType"] == "patient_condition" for group in response.json()["groups"] for change in group["changes"])

    invitation = uuid7()
    assert (await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))["status"] == "accepted"
    response = await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())})
    access.expect(response, 200)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"clinicalProfile": "read_write", "conditions": "none", "allergies": "read_write"}}, 1))["entityVersion"] == 2

    limited = await capture(actor=assistant, include=True)
    assert set(limited["clinicalSections"]) == {
        "profile", "allergies", "encounters", "notes", "measurements",
        "immunizations", "antecedents", "declared_medications",
        "care_plans", "diagnostic_reports", "specialty_templates",
    }
    limited_items = await items(limited["snapshotId"], actor=assistant)
    assert not any(item["entityType"] == "patient_condition" for item in limited_items)
    assert any(item["entityType"] == "patient_allergy_intolerance" for item in limited_items)
    response = await client.get(base + f"/sync/changes?cursor={limited['baseCursor']}", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert not any(change["entityType"] == "patient_condition" for group in response.json()["groups"] for change in group["changes"])
    response = await client.get(base + f"/sync/snapshots/{clinical['snapshotId']}", headers=access.authorization(owner))
    access.expect(response, 410)
    response = await client.get(base + f"/sync/changes?cursor={clinical['baseCursor']}", headers=access.authorization(owner))
    access.expect(response, 410)

    async with administrative() as db:
        events = (await db.execute(text("SELECT action,object_type,object_key FROM nightingale.audit_events WHERE action IN ('CaptureClinicalSnapshot','ReadClinicalSnapshotPage','ReadClinicalChanges')"))).all()
        assert len(events) >= 2
        assert all("CND-A" not in str(event) and "ALG-A" not in str(event) for event in events)

    from unittest.mock import patch
    original_create = dao_events.create
    with patch.object(dao_events, "create", side_effect=SQLAlchemyError("Fixture audit failure")):
        response = await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json={"includeClinical": True})
        access.expect(response, 503)
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.sync_snapshots WHERE account_id=:id AND clinical_sections<>'[]'"), {"id": account_id}) == 2
        delta_audits = await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE account_id=:id AND action='ReadClinicalChanges'"), {"id": account_id})
    assert delta_audits == 2
    with patch.object(dao_events, "create", side_effect=SQLAlchemyError("Fixture audit failure")):
        response = await client.get(base + f"/sync/changes?cursor={limited['baseCursor']}", headers=access.authorization(assistant))
        access.expect(response, 503)
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE account_id=:id AND action='ReadClinicalChanges'"), {"id": account_id}) == delta_audits
    response = await client.get(
        base + f"/sync/snapshots/{limited['snapshotId']}/items?shows=1",
        headers=access.authorization(assistant),
    )
    access.expect(response, 200)
    assert response.json()["total"] == limited["itemCount"] == len(limited_items)
    assert (await operation("UpdatePatientCondition", condition_id, {"clinicalStatus": "active"}, 2))["status"] == "accepted"
    response = await client.get(base + f"/sync/changes?cursor={limited['baseCursor']}", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert response.json()["groups"] == []
    assert response.json()["nextCursor"] != limited["baseCursor"]
    print("Clinical download checks passed: opt-in, sections, current state, invisible delta groups, authorized totals, epoch, audit and rollback.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_downloads))
