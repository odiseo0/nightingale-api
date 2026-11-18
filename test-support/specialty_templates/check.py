import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_specialty_templates(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-specialty-signing-key-2026")
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

    template = uuid7()
    v1_fields = [
        {"fieldKey": "motivo", "label": "Motivo de consulta", "fieldKind": "text",
         "required": True, "displayOrder": 1},
        {"fieldKey": "dolor", "label": "Dolor", "fieldKind": "boolean", "displayOrder": 2},
    ]
    created_template = await operation("CreateSpecialtyTemplate", template, {
        "name": "PRIV-E19-ODONTO-CONSULTA", "fields": v1_fields,
    }, actor=assistant)
    assert created_template["state"]["version"] == 1
    assert len(created_template["state"]["fields"]) == 2

    record = uuid7()
    created_record = await operation("CaptureSpecialtyRecord", record, {
        "patientId": str(patient), "templateId": str(template),
        "values": [{"fieldKey": "motivo", "valueText": "Revisión semestral"}],
    }, actor=assistant)
    assert created_record["state"]["templateVersion"] == 1
    assert created_record["state"]["values"][0]["valueText"] == "Revisión semestral"

    missing_required = await operation("CaptureSpecialtyRecord", uuid7(), {
        "patientId": str(patient), "templateId": str(template), "values": [],
    }, actor=assistant)
    assert missing_required["status"] == "rejected"

    v2_fields = v1_fields + [
        {"fieldKey": "pieza", "label": "Pieza dental", "fieldKind": "number", "displayOrder": 3},
    ]
    updated_template = await operation("UpdateSpecialtyTemplate", template, {
        "name": "PRIV-E19-ODONTO-CONSULTA", "changeNote": "Añade pieza dental",
        "fields": v2_fields,
    }, 1, actor=assistant)
    assert updated_template["entityVersion"] == 2
    assert len(updated_template["state"]["fields"]) == 3

    old_record = await get(f"/patients/{patient}/specialty-records/{record}")
    assert old_record["templateVersion"] == 1, "el registro previo conserva su versión"
    assert len(old_record["values"]) == 1, "cambiar la plantilla no inventa campos"

    history = (await get(f"/specialty-templates/{template}/history"))["items"]
    assert len(history) == 2 and len(history[0]["fields"]) == 2 and len(history[1]["fields"]) == 3

    new_record = await operation("CaptureSpecialtyRecord", uuid7(), {
        "patientId": str(patient), "templateId": str(template),
        "values": [
            {"fieldKey": "motivo", "valueText": "Dolor"},
            {"fieldKey": "pieza", "valueNumber": "16"},
        ],
    }, actor=assistant)
    assert new_record["state"]["templateVersion"] == 2

    updated_record = await operation("UpdateSpecialtyRecord", record, {
        "values": [{"fieldKey": "motivo", "valueText": "Revisión anual"}],
    }, 1, actor=assistant)
    assert updated_record["entityVersion"] == 2

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    entities = {item["entityType"] for item in items}
    assert {"specialty_template", "specialty_record"} <= entities
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.specialty_record_histories WHERE id=:id"), {"id": record}) == 2

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"specialtyTemplates": "none"}}, 1)
    await get(f"/specialty-templates", actor=assistant, status=403)
    await get(f"/patients/{patient}/specialty-records", actor=assistant, status=403)
    await operation("CreateSpecialtyTemplate", template, {"name": "X", "fields": v1_fields}, actor=assistant, status=403)
    print("Specialty template checks passed: E19 version change preserves prior records, no invented facts, sync, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_specialty_templates))
