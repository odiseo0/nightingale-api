import asyncio
import base64
import hashlib
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_diagnostic_results(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-diagnostic-signing-key-2026")
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

    pdf = b"%PDF-1.4 PRIV-E18-INFORME-FICTICIO"
    digest = hashlib.sha256(pdf).hexdigest()
    attachment = uuid7()
    uploaded = await operation("UploadReportAttachment", attachment, {
        "patientId": str(patient), "fileName": "informe.pdf",
        "contentType": "application/pdf", "byteSize": len(pdf),
        "sha256": digest, "contentBase64": base64.b64encode(pdf).decode(),
    }, actor=assistant)
    assert uploaded["state"]["sha256"] == digest
    bad_digest = await operation("UploadReportAttachment", uuid7(), {
        "patientId": str(patient), "fileName": "x.pdf", "contentType": "application/pdf",
        "byteSize": len(pdf), "sha256": "0" * 64,
        "contentBase64": base64.b64encode(pdf).decode(),
    }, actor=assistant)
    assert bad_digest["status"] == "rejected"

    report = uuid7()
    created_report = await operation("CreateDiagnosticReport", report, {
        "patientId": str(patient), "sourceName": "PRIV-E18-LAB CENTRAL",
        "sampleDate": "2026-11-10", "reportKind": "laboratory", "reportStatus": "final",
        "attachmentId": str(attachment),
    }, actor=assistant)
    assert created_report["state"]["attachmentId"] == str(attachment)

    glucose = uuid7()
    created_result = await operation("AddDiagnosticReportResult", glucose, {
        "reportId": str(report), "patientId": str(patient), "analyteName": "Glucosa",
        "resultKind": "numeric", "value": "700", "unit": "mg/dL",
        "referenceLow": "70", "referenceHigh": "100",
    }, actor=assistant)
    assert created_result["state"]["value"] == "700"

    corrected = await operation("UpdateDiagnosticReportResult", glucose, {
        "analyteName": "Glucosa", "resultKind": "numeric", "value": "92", "unit": "mg/dL",
        "referenceLow": "70", "referenceHigh": "100", "correctionReason": "Transcripción",
    }, 1, actor=assistant)
    assert corrected["entityVersion"] == 2

    results = (await get(f"/patients/{patient}/diagnostic-reports/{report}/results"))["items"]
    assert len(results) == 1 and results[0]["value"] == "92", "la corrección no duplica puntos vigentes"

    history = (await get(f"/patients/{patient}/diagnostic-reports/{report}/history"))["items"]
    assert len(history) == 1 and history[0]["action"] == "created"

    corrected_report = await operation("CorrectDiagnosticReport", report, {
        "correctionReason": "Emisión corregida por el laboratorio",
    }, 1, actor=assistant)
    assert corrected_report["entityVersion"] == 2
    assert corrected_report["state"]["correctionReason"] == "Emisión corregida por el laboratorio"

    content = await client.get(
        base + f"/patients/{patient}/report-attachments/{attachment}/content",
        headers=access.authorization(assistant),
    )
    access.expect(content, 200)
    assert content.content == pdf, "la descarga reautorizada entrega los bytes originales"
    assert content.headers["content-type"] == "application/pdf"

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"diagnosticReports": "none"}}, 1)
    denied = await client.get(
        base + f"/patients/{patient}/report-attachments/{attachment}/content",
        headers=access.authorization(assistant),
    )
    access.expect(denied, 403)
    await get(f"/patients/{patient}/diagnostic-reports", actor=assistant, status=403)
    await operation("CreateDiagnosticReport", report, {
        "patientId": str(patient), "sourceName": "X", "reportKind": "other",
        "reportStatus": "final",
    }, actor=assistant, status=403)

    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.diagnostic_report_result_histories WHERE id=:id"), {"id": glucose}) == 2
        assert await db.scalar(text("SELECT count(*) FROM nightingale.diagnostic_report_results WHERE report_id=:id AND record_status='valid'"), {"id": report}) == 1
    print("Diagnostic checks passed: E18 original/correction/vigentes, attachments private, download reauthorized, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_diagnostic_results))
