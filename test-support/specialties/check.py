import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_specialties(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-dental-signing-key-2026")
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

    bad_tooth = await operation("RecordDentalFinding", uuid7(), {
        "patientId": str(patient), "toothFdi": 49, "findingKind": "caries",
    }, actor=assistant)
    assert bad_tooth["status"] == "rejected", "pieza FDI inválida rechazada"
    bad_surface = await operation("RecordDentalFinding", uuid7(), {
        "patientId": str(patient), "toothFdi": 16, "surface": "lateral",
        "findingKind": "caries",
    }, actor=assistant)
    assert bad_surface["status"] == "rejected", "superficie fuera del conjunto rechazada"

    finding = uuid7()
    created_finding = await operation("RecordDentalFinding", finding, {
        "patientId": str(patient), "toothFdi": 16, "surface": "oclusal",
        "findingKind": "caries", "note": "PRIV-DENTAL-CARIES-16",
        "recordedDate": "2026-11",
    }, actor=assistant)
    assert created_finding["state"]["findingStatus"] == "active"

    duplicate = await operation("RecordDentalFinding", uuid7(), {
        "patientId": str(patient), "toothFdi": 16, "surface": "oclusal",
        "findingKind": "caries",
    }, actor=assistant)
    assert duplicate["status"] == "rejected", "hallazgo duplicado vigente rechazado"

    treatment = uuid7()
    created_treatment = await operation("AddDentalTreatment", treatment, {
        "findingId": str(finding), "patientId": str(patient),
        "treatmentKind": "filling", "note": "Obturación",
    }, actor=assistant)
    assert created_treatment["state"]["treatmentStatus"] == "planned"

    no_date = await operation("UpdateDentalTreatment", treatment, {
        "treatmentStatus": "performed",
    }, 1, actor=assistant)
    assert no_date["status"] == "rejected", "realizada sin fecha rechazada"

    performed = await operation("UpdateDentalTreatment", treatment, {
        "treatmentStatus": "performed", "performedDate": "2026-11-18",
    }, 1, actor=assistant)
    assert performed["entityVersion"] == 2
    assert performed["state"]["treatmentStatus"] == "performed"

    resolved = await operation("ResolveDentalFinding", finding, {}, 1, actor=assistant)
    assert resolved["state"]["findingStatus"] == "resolved"

    refill_allowed = await operation("RecordDentalFinding", uuid7(), {
        "patientId": str(patient), "toothFdi": 16, "surface": "oclusal",
        "findingKind": "caries",
    }, actor=assistant)
    assert refill_allowed["status"] == "accepted", "resuelto permite nuevo hallazgo vigente"

    history = (await get(f"/patients/{patient}/dental-findings/{finding}/history"))["items"]
    assert len(history) == 2 and history[0]["findingStatus"] == "active"

    listed = await get(f"/patients/{patient}/dental-findings?toothFdi=16")
    assert listed["total"] == 2

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    entities = {item["entityType"] for item in items}
    assert {"dental_finding", "dental_treatment"} <= entities
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-DENTAL-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.dental_finding_histories WHERE id=:id"), {"id": finding}) == 2

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"specialtyTemplates": "none"}}, 1)
    await get(f"/patients/{patient}/dental-findings", actor=assistant, status=403)
    await operation("RecordDentalFinding", finding, {
        "patientId": str(patient), "toothFdi": 16, "findingKind": "caries",
    }, actor=assistant, status=403)
    print("Specialty checks passed: odontogram FDI/surfaces/duplicates, resolve, treatments, sync, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_specialties))
