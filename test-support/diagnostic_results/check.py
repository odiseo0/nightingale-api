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
postgres = support["postgres"]


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
    other_patient = uuid7()
    await operation("RegisterPatient", patient, {"fullName": "Fixture Patient"})
    await operation("RegisterPatient", other_patient, {"fullName": "Other Fixture Patient"})

    pdf = b"%PDF-1.4 PRIV-E18-INFORME-FICTICIO"
    digest = hashlib.sha256(pdf).hexdigest()
    attachment = uuid7()
    uploaded = await operation("UploadReportAttachment", attachment, {
        "patientId": str(patient), "fileName": "informe-álgebra-\"final\".pdf",
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

    other_pdf = b"%PDF-1.4 PRIV-E18-OTRA-FICHA"
    other_attachment = uuid7()
    await operation("UploadReportAttachment", other_attachment, {
        "patientId": str(other_patient), "fileName": "otra-ficha.pdf",
        "contentType": "application/pdf", "byteSize": len(other_pdf),
        "sha256": hashlib.sha256(other_pdf).hexdigest(),
        "contentBase64": base64.b64encode(other_pdf).decode(),
    }, actor=assistant)
    for action, key, payload in (
        ("UpdateDiagnosticReport", report, {"attachmentId": str(other_attachment)}),
        ("CreateDiagnosticReport", uuid7(), {
            "patientId": str(patient), "sourceName": "Vínculo inválido",
            "reportKind": "other", "reportStatus": "final",
            "attachmentId": str(other_attachment),
        }),
    ):
        await operation(action, key, payload, 1 if action.startswith("Update") else 0,
                        actor=assistant, status=404)
    unchanged = await get(f"/patients/{patient}/diagnostic-reports/{report}", actor=assistant)
    assert unchanged["version"] == 1 and unchanged["attachmentId"] == str(attachment)

    invalid_pdf = b"%PDF-1.4 PRIV-E18-ADJUNTO-ANULADO"
    invalid_attachment = uuid7()
    await operation("UploadReportAttachment", invalid_attachment, {
        "patientId": str(patient), "fileName": "anulado.pdf",
        "contentType": "application/pdf", "byteSize": len(invalid_pdf),
        "sha256": hashlib.sha256(invalid_pdf).hexdigest(),
        "contentBase64": base64.b64encode(invalid_pdf).decode(),
    }, actor=assistant)
    await operation("InvalidateReportAttachment", invalid_attachment, {}, 1, actor=assistant)
    await operation("UpdateDiagnosticReport", report, {
        "attachmentId": str(invalid_attachment),
    }, 1, actor=assistant, status=404)

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

    removed = uuid7()
    await operation("AddDiagnosticReportResult", removed, {
        "reportId": str(report), "patientId": str(patient), "analyteName": "Obsoleto",
        "resultKind": "text", "textValue": "Resultado que se retira",
    }, actor=assistant)
    legacy = await operation("CorrectDiagnosticReport", report, {
        "correctionReason": "Emisión corregida por el laboratorio",
    }, 1, actor=assistant)
    assert legacy["status"] == "rejected" and legacy["error"]["code"] == "VALIDATION_ERROR"
    capture = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant),
                                json={"includeClinical": True})
    access.expect(capture, 201)

    added = uuid7()
    correction_id = uuid7()
    correction = {
        "correctionReason": "Emisión corregida por el laboratorio",
        "results": [
            {
                "resultId": str(glucose), "analyteName": "Glucosa",
                "resultKind": "numeric", "value": "94", "unit": "mg/dL",
                "referenceLow": "70", "referenceHigh": "100",
            },
            {
                "resultId": str(added), "analyteName": "Nota nueva",
                "resultKind": "text", "textValue": "Resultado añadido",
            },
        ],
    }
    from unittest.mock import patch
    from src.api.diagnostic_results.repository.dao import dao_report_result_histories
    from src.core.db import DAOError
    with patch.object(dao_report_result_histories, "add", side_effect=DAOError("Fixture rollback")):
        failed = await operation("CorrectDiagnosticReport", report, correction, 1,
                                 actor=assistant, operation_id=correction_id)
    assert failed["status"] == "retryable_failure"
    before_retry = await get(f"/patients/{patient}/diagnostic-reports/{report}", actor=assistant)
    assert before_retry["version"] == 1

    corrected_report = await operation("CorrectDiagnosticReport", report, correction, 1,
                                       actor=assistant, operation_id=correction_id)
    assert corrected_report["entityVersion"] == 2
    assert corrected_report["state"]["correctionReason"] == "Emisión corregida por el laboratorio"
    repeated = await operation("CorrectDiagnosticReport", report, correction, 1,
                               actor=assistant, operation_id=correction_id)
    assert repeated["status"] == "duplicate"
    current_results = (await get(
        f"/patients/{patient}/diagnostic-reports/{report}/results", actor=assistant
    ))["items"]
    assert {item["resultId"] for item in current_results} == {str(glucose), str(added)}
    assert next(item for item in current_results if item["resultId"] == str(glucose))["value"] == "94"
    first_page = await get(
        f"/patients/{patient}/diagnostic-reports/{report}/results?page=1&shows=1",
        actor=assistant,
    )
    second_page = await get(
        f"/patients/{patient}/diagnostic-reports/{report}/results?page=2&shows=1",
        actor=assistant,
    )
    assert first_page["total"] == second_page["total"] == 2
    assert first_page["items"][0]["resultId"] != second_page["items"][0]["resultId"]
    empty_page = await get(
        f"/patients/{patient}/diagnostic-reports/{report}/results?page=3&shows=1",
        actor=assistant,
    )
    assert empty_page["items"] == []
    invalid_results = await get(
        f"/patients/{patient}/diagnostic-reports/{report}/results?recordStatus=entered-in-error",
        actor=assistant,
    )
    assert invalid_results["total"] == 1
    assert invalid_results["items"][0]["resultId"] == str(removed)
    delta = await get(f"/sync/changes?cursor={capture.json()['baseCursor']}", actor=assistant)
    group = next(item for item in delta["groups"] if item["operationId"] == str(correction_id))
    assert {change["entityKey"] for change in group["changes"]} == {
        str(report), str(glucose), str(added), str(removed),
    }
    assert next(change for change in group["changes"]
                if change["entityKey"] == str(removed))["state"]["recordStatus"] == "entered-in-error"
    await operation("SetPatientProfileStatus", other_patient, {"status": "inactive"}, 1,
                    actor=assistant)
    corrected_capture = await client.post(base + "/sync/snapshots",
        headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(corrected_capture, 201)
    captured_items = (await get(
        f"/sync/snapshots/{corrected_capture.json()['snapshotId']}/items?shows=500",
        actor=assistant,
    ))["items"]
    captured_results = [item for item in captured_items
                        if item["entityType"] == "diagnostic_report_result"]
    assert {item["entityKey"] for item in captured_results} == {str(glucose), str(added)}
    assert any(item["entityType"] == "patient_profile"
               and item["entityKey"] == str(other_patient) for item in captured_items)

    legacy_report = uuid7()
    legacy_result = uuid7()
    await operation("CreateDiagnosticReport", legacy_report, {
        "patientId": str(patient), "sourceName": "Fixture informe anterior",
        "reportKind": "laboratory", "reportStatus": "final",
    }, actor=assistant)
    await operation("AddDiagnosticReportResult", legacy_result, {
        "reportId": str(legacy_report), "patientId": str(patient),
        "analyteName": "Original recuperable", "resultKind": "text",
        "textValue": "Dato anterior conservado",
    }, actor=assistant)
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                UPDATE nightingale.diagnostic_reports
                SET version=2,correction_reason='Corrección anterior ficticia',
                    updated_at=clock_timestamp() WHERE id=:report
            """), {"report": legacy_report})
            await db.execute(text("""
                INSERT INTO nightingale.diagnostic_report_histories (
                    account_id,id,patient_id,encounter_id,source_name,source_type,
                    sample_date,issued_date,report_kind,report_status,attachment_id,
                    clinical_summary,captured_at_local,record_status,correction_reason,
                    created_by_user_id,updated_by_user_id,created_at,updated_at,version,
                    action,actor_user_id,operation_id,changed_at
                )
                SELECT account_id,id,patient_id,encounter_id,source_name,source_type,
                    sample_date,issued_date,report_kind,report_status,attachment_id,
                    clinical_summary,captured_at_local,record_status,
                    'Corrección anterior ficticia',created_by_user_id,updated_by_user_id,
                    created_at,updated_at,2,'updated',actor_user_id,operation_id,changed_at
                FROM nightingale.diagnostic_report_histories
                WHERE id=:report AND version=1
            """), {"report": legacy_report})
        candidate = await db.scalar(text("""
            SELECT r.id FROM nightingale.diagnostic_reports r
            JOIN nightingale.diagnostic_report_results x ON x.report_id=r.id
            WHERE r.id=:report AND r.version>1 AND x.record_status='valid'
                AND x.updated_at<r.updated_at
        """), {"report": legacy_report})
        assert candidate == legacy_report
        assert await db.scalar(text("""
            SELECT count(*) FROM nightingale.diagnostic_report_result_histories
            WHERE id=:result
        """), {"result": legacy_result}) == 1

    detached = await operation("UpdateDiagnosticReport", report, {
        "attachmentId": None,
    }, 2, actor=assistant)
    assert detached["entityVersion"] == 3 and detached["state"]["attachmentId"] is None
    report_history = (await get(
        f"/patients/{patient}/diagnostic-reports/{report}/history", actor=assistant
    ))["items"]
    assert [item["version"] for item in report_history] == [1, 2, 3]
    assert [item["attachmentId"] for item in report_history] == [str(attachment), str(attachment), None]

    linked_report = uuid7()
    await operation("CreateDiagnosticReport", linked_report, {
        "patientId": str(patient), "sourceName": "Fixture vínculo en carga",
        "reportKind": "imaging", "reportStatus": "final",
    }, actor=assistant)
    linked_pdf = b"%PDF-1.4 PRIV-E18-VINCULO-EN-CARGA"
    linked_attachment = uuid7()
    linked_upload = await operation("UploadReportAttachment", linked_attachment, {
        "patientId": str(patient), "reportId": str(linked_report),
        "fileName": "vinculado.pdf", "contentType": "application/pdf",
        "byteSize": len(linked_pdf), "sha256": hashlib.sha256(linked_pdf).hexdigest(),
        "contentBase64": base64.b64encode(linked_pdf).decode(),
    }, actor=assistant)
    assert linked_upload["state"]["reportId"] == str(linked_report)
    linked_state = await get(f"/patients/{patient}/diagnostic-reports/{linked_report}",
                             actor=assistant)
    assert linked_state["version"] == 2 and linked_state["attachmentId"] == str(linked_attachment)
    linked_history = (await get(
        f"/patients/{patient}/diagnostic-reports/{linked_report}/history", actor=assistant
    ))["items"]
    assert linked_history[-1]["version"] == 2
    assert linked_history[-1]["attachmentId"] == str(linked_attachment)
    recent_linked_history = await get(
        f"/patients/{patient}/diagnostic-reports/{linked_report}/history?afterVersion=1",
        actor=assistant,
    )
    assert recent_linked_history["total"] == 1
    assert recent_linked_history["items"][0]["version"] == 2
    from unittest.mock import AsyncMock
    from sqlalchemy import event
    from src.core.db.session import engine
    from src.core.services import report_storage
    statements = []

    def capture_statement(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", capture_statement)
    try:
        with patch.object(report_storage, "fetch", new=AsyncMock(side_effect=report_storage.StorageError("offline"))) as fetch:
            linked_metadata = await get(
                f"/patients/{patient}/report-attachments/{linked_attachment}", actor=assistant
            )
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", capture_statement)
    assert linked_metadata["reportId"] == str(linked_report)
    fetch.assert_not_awaited()
    related_statements = [statement for statement in statements
        if "FROM diagnostic_reports" in statement
        or "FROM report_attachments" in statement]
    assert len(related_statements) == 2, "adjunto e informe, sin cargas ORM implícitas"
    linked_capture = await client.post(base + "/sync/snapshots",
        headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(linked_capture, 201)
    linked_items = (await get(
        f"/sync/snapshots/{linked_capture.json()['snapshotId']}/items?shows=500",
        actor=assistant,
    ))["items"]
    captured_attachment = next(item for item in linked_items
        if item["entityType"] == "report_attachment" and item["entityKey"] == str(linked_attachment))
    assert captured_attachment["state"]["reportId"] == str(linked_report)

    retry_pdf = b"%PDF-1.4 PRIV-E18-REINTENTO-ADJUNTO"
    retry_attachment = uuid7()
    retry_operation = uuid7()
    retry_payload = {
        "patientId": str(patient), "fileName": "reintento.pdf",
        "contentType": "application/pdf", "byteSize": len(retry_pdf),
        "sha256": hashlib.sha256(retry_pdf).hexdigest(),
        "contentBase64": base64.b64encode(retry_pdf).decode(),
    }
    from src.api.diagnostic_results.repository.dao import dao_report_attachment_histories
    from src.core.db import DAOError
    with patch.object(dao_report_attachment_histories, "add", side_effect=DAOError("Fixture rollback")):
        failed_upload = await operation("UploadReportAttachment", retry_attachment,
            retry_payload, actor=assistant, operation_id=retry_operation)
    assert failed_upload["status"] == "retryable_failure"
    async with administrative() as db:
        assert await db.scalar(text("""
            SELECT count(*) FROM nightingale.report_attachments WHERE id=:attachment
        """), {"attachment": retry_attachment}) == 0
    retried_upload = await operation("UploadReportAttachment", retry_attachment,
        retry_payload, actor=assistant, operation_id=retry_operation)
    assert retried_upload["status"] == "accepted"
    retry_content = await client.get(
        base + f"/patients/{patient}/report-attachments/{retry_attachment}/content",
        headers=access.authorization(assistant),
    )
    access.expect(retry_content, 200)
    assert retry_content.content == retry_pdf

    for suffix in ("", "/content"):
        await get(
            f"/patients/{other_patient}/report-attachments/{attachment}{suffix}",
            actor=assistant,
            status=404,
        )

    from src.settings.storage_settings import storage_settings
    with patch.object(storage_settings, "STORAGE_ROOT", str(ROOT / ".tmp/other-storage")):
        content = await client.get(
            base + f"/patients/{patient}/report-attachments/{attachment}/content",
            headers=access.authorization(assistant),
        )
    access.expect(content, 200)
    assert content.content == pdf, "la descarga conserva el almacén registrado"
    assert content.headers["content-type"] == "application/pdf"
    assert "filename*=UTF-8''" in content.headers["content-disposition"]
    assert "informe-%C3" in content.headers["content-disposition"]

    clinical_history = await get(
        f"/patients/{patient}/clinical-history?sections=diagnostic_reports", actor=assistant
    )
    report_entry = next(item for item in clinical_history["items"]
                        if item["entryId"] == str(report))
    assert report_entry["entryType"] == "diagnostic_report" and report_entry["entityVersion"] == 3

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"diagnosticReports": "none"}}, 1)
    denied = await client.get(
        base + f"/patients/{patient}/report-attachments/{attachment}/content",
        headers=access.authorization(assistant),
    )
    access.expect(denied, 403)
    filtered_history = await get(f"/patients/{patient}/clinical-history", actor=assistant)
    assert all(item["entryId"] != str(report) for item in filtered_history["items"])
    await get(f"/patients/{patient}/diagnostic-reports", actor=assistant, status=403)
    await operation("CreateDiagnosticReport", report, {
        "patientId": str(patient), "sourceName": "X", "reportKind": "other",
        "reportStatus": "final",
    }, actor=assistant, status=403)

    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.diagnostic_report_result_histories WHERE id=:id"), {"id": glucose}) == 3
        assert await db.scalar(text("SELECT count(*) FROM nightingale.diagnostic_report_results WHERE report_id=:id AND record_status='valid'"), {"id": report}) == 2
        assert await db.scalar(text("SELECT record_status FROM nightingale.diagnostic_report_results WHERE id=:id"), {"id": removed}) == "entered-in-error"

    from sqlalchemy.exc import DBAPIError
    async with administrative() as db:
        try:
            async with db.begin():
                await db.execute(text("""
                    UPDATE nightingale.diagnostic_reports SET attachment_id=:attachment
                    WHERE id=:report
                """), {"attachment": other_attachment, "report": report})
        except DBAPIError as error:
            assert error.orig.sqlstate == "23503"
        else:
            raise AssertionError("SQL directo cruzó la ficha del adjunto")

    result = postgres.migrate("downgrade", "20261117_07")
    assert result.returncode == 0, result.stderr
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                UPDATE nightingale.diagnostic_reports SET attachment_id=:attachment
                WHERE id=:report
            """), {"attachment": other_attachment, "report": report})
    result = postgres.migrate("upgrade", "head")
    assert result.returncode != 0 and "cross_scope=1" in result.stderr
    result = postgres.migrate("downgrade", "20261117_07")
    assert result.returncode == 0, result.stderr
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                UPDATE nightingale.diagnostic_reports SET attachment_id=NULL
                WHERE id=:report
            """), {"report": report})
    result = postgres.migrate("upgrade", "head")
    assert result.returncode == 0, result.stderr
    async with administrative() as db:
        assert await db.scalar(text("""
            SELECT count(*) FROM nightingale.patient_clinical_timeline
            WHERE entry_type='diagnostic_report' AND entry_id=:report
        """), {"report": report}) == 1
    await check_s3_client_closes()
    print("Diagnostic checks passed: E18 original/correction/vigentes, attachments private, download reauthorized, privacy, permissions, composite FK and S3 client cleanup.")


async def check_s3_client_closes() -> None:
    from unittest.mock import AsyncMock, patch
    from src.core.services import report_storage

    account_id, attachment_id = uuid7(), uuid7()
    s3_client, http_client = AsyncMock(), AsyncMock()
    with (
        patch.object(report_storage, "_s3_enabled", return_value=True),
        patch.object(report_storage, "_import_s3", return_value=(s3_client, http_client)),
        patch.object(report_storage.storage_settings, "STORAGE_BUCKET", "fixture-bucket"),
    ):
        storage_key = await report_storage.save(account_id, attachment_id, b"fixture-upload")
    assert storage_key == f"s3://fixture-bucket/{account_id}/{attachment_id}"
    s3_client.upload.assert_awaited_once_with(f"{account_id}/{attachment_id}", b"fixture-upload")
    http_client.aclose.assert_awaited_once()

    s3_client, http_client = AsyncMock(), AsyncMock()
    s3_client.download.return_value = b"fixture-download"
    with patch.object(report_storage, "_import_s3", return_value=(s3_client, http_client)):
        content = await report_storage.fetch("s3://fixture-bucket/fixture-key")
    assert content == b"fixture-download"
    s3_client.download.assert_awaited_once_with("fixture-key")
    http_client.aclose.assert_awaited_once()

    s3_client, http_client = AsyncMock(), AsyncMock()
    s3_client.upload.side_effect = RuntimeError("fixture upload failure")
    with (
        patch.object(report_storage, "_s3_enabled", return_value=True),
        patch.object(report_storage, "_import_s3", return_value=(s3_client, http_client)),
    ):
        try:
            await report_storage.save(account_id, attachment_id, b"fixture-failure")
        except RuntimeError as error:
            assert str(error) == "fixture upload failure"
        else:
            raise AssertionError("el fallo ficticio de carga no se propagó")
    http_client.aclose.assert_awaited_once()


if __name__ == "__main__":
    asyncio.run(support["main"](check_diagnostic_results))
