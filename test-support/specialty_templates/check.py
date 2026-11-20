import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]
postgres = support["postgres"]


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

    before_invalidation = await client.post(base + "/sync/snapshots",
        headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(before_invalidation, 201)
    invalidation_id = uuid7()
    from unittest.mock import patch
    from src.api.specialties.repository.dao import dao_specialty_record_histories
    from src.core.db import DAOError
    with patch.object(dao_specialty_record_histories, "add", side_effect=DAOError("Fixture rollback")):
        failed = await operation("InvalidateSpecialtyRecord", record,
            {"correctionReason": "Registro ficticio duplicado"}, 2,
            actor=assistant, operation_id=invalidation_id)
    assert failed["status"] == "retryable_failure"
    current = await get(f"/patients/{patient}/specialty-records/{record}", actor=assistant)
    assert current["version"] == 2 and current["recordStatus"] == "valid"
    invalidated = await operation("InvalidateSpecialtyRecord", record,
        {"correctionReason": "Registro ficticio duplicado"}, 2,
        actor=assistant, operation_id=invalidation_id)
    assert invalidated["entityVersion"] == 3 and invalidated["state"]["recordStatus"] == "entered-in-error"
    repeated = await operation("InvalidateSpecialtyRecord", record,
        {"correctionReason": "Registro ficticio duplicado"}, 2,
        actor=assistant, operation_id=invalidation_id)
    assert repeated["status"] == "duplicate"
    record_history = (await get(
        f"/patients/{patient}/specialty-records/{record}/history", actor=assistant
    ))["items"]
    assert [item["version"] for item in record_history] == [1, 2, 3]
    assert [len(item["values"]) for item in record_history] == [1, 1, 1]
    async with administrative() as db:
        assert await db.scalar(text("""
            SELECT count(*) FROM nightingale.specialty_record_values
            WHERE record_id=:record AND record_version IN (2,3)
        """), {"record": record}) == 2
    delta = await get(f"/sync/changes?cursor={before_invalidation.json()['baseCursor']}",
                      actor=assistant)
    invalidation_change = next(change for group in delta["groups"]
        for change in group["changes"] if change["entityKey"] == str(record))
    assert invalidation_change["state"]["recordStatus"] == "entered-in-error"

    retire_id = uuid7()
    from src.api.specialties.repository.dao import dao_template_histories
    with patch.object(dao_template_histories, "add", side_effect=DAOError("Fixture rollback")):
        failed_retire = await operation("RetireSpecialtyTemplate", template, {}, 2,
            actor=assistant, operation_id=retire_id)
    assert failed_retire["status"] == "retryable_failure"
    active_template = await get(f"/specialty-templates/{template}", actor=assistant)
    assert active_template["version"] == 2 and active_template["templateStatus"] == "active"
    retired = await operation("RetireSpecialtyTemplate", template, {}, 2,
        actor=assistant, operation_id=retire_id)
    assert retired["entityVersion"] == 3 and retired["state"]["templateStatus"] == "retired"
    assert len(retired["state"]["fields"]) == 3
    repeated_retire = await operation("RetireSpecialtyTemplate", template, {}, 2,
        actor=assistant, operation_id=retire_id)
    assert repeated_retire["status"] == "duplicate"
    template_history = (await get(f"/specialty-templates/{template}/history",
                                  actor=assistant))["items"]
    assert [item["version"] for item in template_history] == [1, 2, 3]
    assert [len(item["fields"]) for item in template_history] == [2, 3, 3]
    previous_record = await get(f"/patients/{patient}/specialty-records/{new_record['state']['recordId']}",
                                actor=assistant)
    assert previous_record["templateVersion"] == 2 and len(previous_record["values"]) == 2
    await operation("CaptureSpecialtyRecord", uuid7(), {
        "patientId": str(patient), "templateId": str(template),
        "values": [{"fieldKey": "motivo", "valueText": "No permitido"}],
    }, actor=assistant, status=404)

    patched = await operation("UpdateSpecialtyRecord", new_record["state"]["recordId"], {
        "correctionReason": "Solo cambia el motivo",
    }, 1, actor=assistant)
    assert patched["entityVersion"] == 2 and len(patched["state"]["values"]) == 2
    patch_history = (await get(
        f"/patients/{patient}/specialty-records/{new_record['state']['recordId']}/history",
        actor=assistant,
    ))["items"]
    assert [len(item["values"]) for item in patch_history] == [2, 2]
    cleared = await operation("UpdateSpecialtyRecord", new_record["state"]["recordId"], {
        "values": None,
    }, 2, actor=assistant)
    assert cleared["status"] == "rejected" and cleared["error"]["code"] == "VALIDATION_ERROR"
    after_null = await get(
        f"/patients/{patient}/specialty-records/{new_record['state']['recordId']}",
        actor=assistant,
    )
    assert after_null["version"] == 2 and len(after_null["values"]) == 2
    cleared_history = (await get(
        f"/patients/{patient}/specialty-records/{new_record['state']['recordId']}/history",
        actor=assistant,
    ))["items"]
    assert [len(item["values"]) for item in cleared_history] == [2, 2]

    retire_delta = await get(f"/sync/changes?cursor={before_invalidation.json()['baseCursor']}",
                             actor=assistant)
    retire_change = next(change for group in retire_delta["groups"]
        for change in group["changes"] if change["entityKey"] == str(template))
    assert retire_change["state"]["templateStatus"] == "retired"

    typed_template = uuid7()
    typed_fields = [
        {"fieldKey": "texto", "label": "Texto", "fieldKind": "text", "displayOrder": 1},
        {"fieldKey": "numero", "label": "Número", "fieldKind": "number", "displayOrder": 2},
        {"fieldKey": "logico", "label": "Lógico", "fieldKind": "boolean", "displayOrder": 3},
        {"fieldKey": "fecha", "label": "Fecha", "fieldKind": "date_partial", "displayOrder": 4},
    ]
    await operation("CreateSpecialtyTemplate", typed_template, {
        "name": "Fixture cuatro tipos", "fields": typed_fields,
    }, actor=assistant)
    wrong_values = [
        {"fieldKey": "texto", "valueNumber": "1"},
        {"fieldKey": "numero", "valueText": "incorrecto"},
        {"fieldKey": "logico", "valueText": "incorrecto"},
        {"fieldKey": "fecha", "valueBoolean": False},
    ]
    for value in wrong_values:
        rejected = await operation("CaptureSpecialtyRecord", uuid7(), {
            "patientId": str(patient), "templateId": str(typed_template),
            "values": [value],
        }, actor=assistant)
        assert rejected["status"] == "rejected" and rejected["error"]["code"] == "VALIDATION_ERROR"
    typed_record = uuid7()
    valid_record = await operation("CaptureSpecialtyRecord", typed_record, {
        "patientId": str(patient), "templateId": str(typed_template),
        "values": [
            {"fieldKey": "texto", "valueText": "Válido"},
            {"fieldKey": "numero", "valueNumber": "16"},
            {"fieldKey": "logico", "valueBoolean": False},
            {"fieldKey": "fecha", "valueDate": "2026-11"},
        ],
    }, actor=assistant)
    assert valid_record["status"] == "accepted" and len(valid_record["state"]["values"]) == 4
    wrong_edit = await operation("UpdateSpecialtyRecord", typed_record, {
        "values": [{"fieldKey": "texto", "valueNumber": "2"}],
    }, 1, actor=assistant)
    assert wrong_edit["status"] == "rejected"
    unchanged_type = await get(f"/patients/{patient}/specialty-records/{typed_record}",
                               actor=assistant)
    assert unchanged_type["version"] == 1 and len(unchanged_type["values"]) == 4

    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                UPDATE nightingale.specialty_record_values
                SET value_text=NULL,value_number=99
                WHERE record_id=:record AND record_version=1 AND field_key='texto'
            """), {"record": typed_record})
            incompatible = await db.scalar(text("""
                SELECT count(*) FROM nightingale.specialty_record_values v
                JOIN nightingale.specialty_records r
                    ON r.account_id=v.account_id AND r.id=v.record_id
                JOIN nightingale.specialty_template_fields f
                    ON f.account_id=r.account_id AND f.template_id=r.template_id
                    AND f.template_version=r.template_version AND f.field_key=v.field_key
                WHERE v.record_id=:record AND v.record_version=1
                    AND f.field_kind='text' AND v.value_text IS NULL
            """), {"record": typed_record})
            assert incompatible == 1
            await db.execute(text("""
                UPDATE nightingale.specialty_records SET version=3,updated_at=clock_timestamp()
                WHERE id=:record
            """), {"record": new_record["state"]["recordId"]})
            await db.execute(text("""
                INSERT INTO nightingale.specialty_record_histories (
                    account_id,id,patient_id,encounter_id,template_id,template_version,
                    recorded_at,record_status,correction_reason,version,created_by_user_id,
                    updated_by_user_id,created_at,updated_at,action,actor_user_id,
                    operation_id,changed_at
                )
                SELECT account_id,id,patient_id,encounter_id,template_id,template_version,
                    recorded_at,record_status,correction_reason,3,created_by_user_id,
                    updated_by_user_id,created_at,updated_at,'updated',actor_user_id,
                    operation_id,changed_at
                FROM nightingale.specialty_record_histories
                WHERE id=:record AND version=2
            """), {"record": new_record["state"]["recordId"]})
            current_values, previous_values = (await db.execute(text("""
                SELECT
                    (SELECT count(*) FROM nightingale.specialty_record_values
                        WHERE record_id=:record AND record_version=3),
                    (SELECT count(*) FROM nightingale.specialty_record_values
                        WHERE record_id=:record AND record_version=2)
            """), {"record": new_record["state"]["recordId"]})).one()
            assert current_values == 0 and previous_values == 2
            await db.rollback()

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    entities = {item["entityType"] for item in items}
    assert "specialty_record" in entities
    template_items = [item for item in items if item["entityType"] == "specialty_template"]
    template_keys = {(item["entityKey"]["templateId"], item["entityKey"]["version"])
                     for item in template_items}
    assert (str(template), "2") in template_keys, template_keys
    assert (str(typed_template), "1") in template_keys, template_keys
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.specialty_record_histories WHERE id=:id"), {"id": record}) == 3

    clinical_history = await get(
        f"/patients/{patient}/clinical-history?sections=specialty_templates", actor=assistant
    )
    specialty_entry = next(item for item in clinical_history["items"]
                           if item["entryId"] == str(typed_record))
    assert specialty_entry["entryType"] == "specialty_record"
    result = postgres.migrate("downgrade", "20261118_02")
    assert result.returncode == 0, result.stderr
    result = postgres.migrate("upgrade", "head")
    assert result.returncode == 0, result.stderr
    recovered_history = await get(
        f"/patients/{patient}/clinical-history?sections=specialty_templates", actor=assistant
    )
    assert any(item["entryId"] == str(typed_record) for item in recovered_history["items"])

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"specialtyTemplates": "none"}}, 1)
    await get(f"/specialty-templates", actor=assistant, status=403)
    await get(f"/patients/{patient}/specialty-records", actor=assistant, status=403)
    await operation("CreateSpecialtyTemplate", template, {"name": "X", "fields": v1_fields}, actor=assistant, status=403)
    print("Specialty template checks passed: E19 version change preserves prior records, no invented facts, sync, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_specialty_templates))
