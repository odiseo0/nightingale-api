from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.domain.errors import AccessDenied
from src.api.clinical_records.application.access_cases import (
    clinical_page,
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.diagnostic_results.domain.reports import (
    CorrectDiagnosticReportPayload,
    CreateDiagnosticReportPayload,
    DiagnosticReportHistoryResponse,
    DiagnosticReportQuery,
    DiagnosticReportResponse,
    UpdateDiagnosticReportPayload,
)
from src.api.diagnostic_results.domain.results import (
    AddDiagnosticReportResultPayload,
    DiagnosticReportResultHistoryResponse,
    DiagnosticReportResultResponse,
    InvalidateDiagnosticReportResultPayload,
    InvalidateReportAttachmentPayload,
    ReportAttachmentResponse,
    UpdateDiagnosticReportResultPayload,
    UploadReportAttachmentPayload,
)
from src.api.diagnostic_results.repository.dao import (
    dao_report_attachment_histories,
    dao_report_attachments,
    dao_report_histories,
    dao_report_result_histories,
    dao_report_results,
    dao_reports,
)
from src.api.diagnostic_results.repository.models import (
    DiagnosticReport,
    DiagnosticReportHistory,
    DiagnosticReportResult,
    DiagnosticReportResultHistory,
    ReportAttachment,
    ReportAttachmentHistory,
)
from src.api.encounters.application.encounters_cases import valid_encounter_for_record
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    lock_clinical_patient,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery
from src.core.services import report_storage
from src.core.utils.utils import Empty, EmptyType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

REPORT_ACTIONS = ("CreateDiagnosticReport", "UpdateDiagnosticReport", "CorrectDiagnosticReport")
RESULT_ACTIONS = (
    "AddDiagnosticReportResult",
    "UpdateDiagnosticReportResult",
    "InvalidateDiagnosticReportResult",
)
ATTACHMENT_ACTIONS = (
    "UploadReportAttachment",
    "InvalidateReportAttachment",
)


def report_response(row: DiagnosticReport) -> DiagnosticReportResponse:
    return DiagnosticReportResponse(
        report_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        source_name=row.source_name,
        source_type=row.source_type,
        sample_date=row.sample_date,
        issued_date=row.issued_date,
        report_kind=row.report_kind,
        report_status=row.report_status,
        attachment_id=row.attachment_id,
        clinical_summary=row.clinical_summary,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def result_response(row: DiagnosticReportResult) -> DiagnosticReportResultResponse:
    return DiagnosticReportResultResponse(
        result_id=row.id,
        report_id=row.report_id,
        patient_id=row.patient_id,
        analyte_name=row.analyte_name,
        result_kind=row.result_kind,
        value=row.value,
        text_value=row.text_value,
        unit=row.unit,
        reference_low=row.reference_low,
        reference_high=row.reference_high,
        reference_text=row.reference_text,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def attachment_response(row: ReportAttachment) -> ReportAttachmentResponse:
    return ReportAttachmentResponse(
        attachment_id=row.id,
        report_id=None,
        file_name=row.file_name,
        content_type=row.content_type,
        byte_size=row.byte_size,
        sha256=row.sha256,
        uploaded_at=row.uploaded_at,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def _history_fields(state, *extra: str) -> dict:
    data = state.model_dump(exclude={"version", "created_at", "updated_at"})
    for key in ("report_id", "result_id", "attachment_id", *extra):
        data.pop(key, None)
    return data


async def apply_diagnostic_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.diagnostic_reports != "read_write":
        return Err(AccessDenied())

    if action in REPORT_ACTIONS:
        return await _apply_report(db, context, action, entity_key, expected_version, payload, operation_id)
    if action in RESULT_ACTIONS:
        return await _apply_result(db, context, action, entity_key, expected_version, payload, operation_id)
    if action in ATTACHMENT_ACTIONS:
        return await _apply_attachment(db, context, action, entity_key, expected_version, payload, operation_id)
    return Err(AccountRuleError("UNSUPPORTED_OPERATION"))


async def _apply_report(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "CreateDiagnosticReport":
        if not isinstance(payload, CreateDiagnosticReportPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_reports.scoped(db, context.account.id, entity_key) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        if await lock_clinical_patient(db, context.account.id, payload.patient_id) is Empty:
            return Err(AccountObjectNotFound())
        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        if payload.attachment_id is not None:
            attachment = await dao_report_attachments.scoped(
                db, context.account.id, payload.attachment_id
            )
            if attachment is Empty or attachment.patient_id != payload.patient_id:
                return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = DiagnosticReport(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            **payload.model_dump(exclude={"patient_id", "encounter_id", "attachment_id"}),
            attachment_id=payload.attachment_id,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_reports.add(db, row)
        event = "created"
    else:
        row = await dao_reports.scoped(db, context.account.id, entity_key, lock=True)
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "CorrectDiagnosticReport":
            if not isinstance(payload, CorrectDiagnosticReportPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.correction_reason = payload.correction_reason
            event = "updated"
        elif action == "UpdateDiagnosticReport":
            if not isinstance(payload, UpdateDiagnosticReportPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            changes = payload.model_dump(exclude_unset=True)
            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))
            for name, value in changes.items():
                setattr(row, name, value)
            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.updated_at = await clinical_server_time(db)
        row.version += 1
        await dao_reports.flush(db)

    state = report_response(row)
    await dao_report_histories.add(
        db,
        DiagnosticReportHistory(
            account_id=row.account_id,
            id=row.id,
            **_history_fields(state),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.updated_at,
        ),
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [AccountChange("diagnostic_report", str(row.id), state, state.version, "clinical_diagnostic_reports")],
            False,
        )
    )


async def _apply_result(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "AddDiagnosticReportResult":
        if not isinstance(payload, AddDiagnosticReportResultPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_report_results.scoped(db, context.account.id, entity_key) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        report = await dao_reports.scoped(db, context.account.id, payload.report_id)
        if report is Empty or report.patient_id != payload.patient_id or report.record_status != "valid":
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = DiagnosticReportResult(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            report_id=payload.report_id,
            **payload.model_dump(exclude={"report_id", "patient_id"}),
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_report_results.add(db, row)
        event = "created"
    else:
        row = await dao_report_results.scoped(db, context.account.id, entity_key, lock=True)
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateDiagnosticReportResult":
            if not isinstance(payload, InvalidateDiagnosticReportResultPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdateDiagnosticReportResult":
            if not isinstance(payload, UpdateDiagnosticReportResultPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            changes = payload.model_dump(exclude_unset=True)
            from src.api.diagnostic_results.domain.results import (
                DiagnosticReportResultFields,
            )

            candidate = {
                name: getattr(row, name)
                for name in DiagnosticReportResultFields.model_fields
            }
            candidate.update(
                {k: v for k, v in changes.items() if k != "correction_reason"}
            )
            try:
                DiagnosticReportResultFields.model_validate(candidate)
            except ValueError:
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))
            for name, value in changes.items():
                setattr(row, name, value)
            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.updated_at = await clinical_server_time(db)
        row.version += 1
        await dao_report_results.flush(db)

    state = result_response(row)
    await dao_report_result_histories.add(
        db,
        DiagnosticReportResultHistory(
            account_id=row.account_id,
            id=row.id,
            report_id=row.report_id,
            **_history_fields(state),
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.updated_at,
        ),
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [AccountChange("diagnostic_report_result", str(row.id), state, state.version, "clinical_diagnostic_reports")],
            False,
        )
    )


async def _apply_attachment(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "UploadReportAttachment":
        if not isinstance(payload, UploadReportAttachmentPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_report_attachments.scoped(db, context.account.id, entity_key) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        if await lock_clinical_patient(db, context.account.id, payload.patient_id) is Empty:
            return Err(AccountObjectNotFound())
        try:
            content = report_storage.decode_and_verify(
                payload.content_base64, payload.sha256
            )
        except report_storage.StorageError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if len(content) != payload.byte_size:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        now = await clinical_server_time(db)
        row = ReportAttachment(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            file_name=payload.file_name,
            content_type=payload.content_type,
            byte_size=payload.byte_size,
            sha256=payload.sha256.lower(),
            storage_key=f"{context.account.id}/{entity_key}",
            uploaded_at=now,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_report_attachments.add(db, row)
        row.storage_key = await report_storage.save(
            context.account.id, entity_key, content
        )
        event = "created"
    else:
        row = await dao_report_attachments.scoped(db, context.account.id, entity_key, lock=True)
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateReportAttachment":
            if not isinstance(payload, InvalidateReportAttachmentPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.updated_at = await clinical_server_time(db)
        row.version += 1
        await dao_report_attachments.flush(db)

    state = attachment_response(row)
    await dao_report_attachment_histories.add(
        db,
        ReportAttachmentHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            **_history_fields(state),
            storage_key=row.storage_key,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.updated_at,
        ),
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [AccountChange("report_attachment", str(row.id), state, state.version, "clinical_diagnostic_reports")],
            False,
        )
    )


async def read_reports(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: DiagnosticReportQuery | PageQuery,
    report_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if report_id is None:
            if not isinstance(query, DiagnosticReportQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            rows, total = await dao_reports.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, report_response)
            action = "ReadPatientDiagnosticReports"
        else:
            row = await dao_reports.scoped(db, account_id, report_id)
            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            response = report_response(row)
            action = "ReadPatientDiagnosticReport"

        await record_clinical_read(db, scope.value, action, "diagnostic_report", str(report_id or patient_id))

    return Ok(response)


async def read_report_history(db, credential, account_id, patient_id, report_id, query: ClinicalHistoryQuery):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        row = await dao_reports.scoped(db, account_id, report_id)
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_report_histories.page(
            db, account_id, report_id, (query.page - 1) * query.shows, query.shows, query.after_version
        )
        response = clinical_page(rows, total, _report_history)
        await record_clinical_read(db, scope.value, "ReadPatientDiagnosticReportHistory", "diagnostic_report", str(report_id))

    return Ok(response)


def _report_history(row: DiagnosticReportHistory) -> DiagnosticReportHistoryResponse:
    data = report_history_view(row).model_dump(exclude={"version"})
    data.pop("report_id", None)
    return DiagnosticReportHistoryResponse(
        report_id=row.id,
        version=row.version,
        **data,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


def report_history_view(row: DiagnosticReportHistory) -> DiagnosticReportResponse:
    return DiagnosticReportResponse(
        report_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        source_name=row.source_name,
        source_type=row.source_type,
        sample_date=row.sample_date,
        issued_date=row.issued_date,
        report_kind=row.report_kind,
        report_status=row.report_status,
        attachment_id=row.attachment_id,
        clinical_summary=row.clinical_summary,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


async def read_report_results(db, credential, account_id, patient_id, report_id):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        report = await dao_reports.scoped(db, account_id, report_id)
        if report is Empty or report.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows = [
            result
            for result in await dao_report_results.for_report(db, account_id, report_id)
            if result.record_status == "valid"
        ]
        response = clinical_page(rows, len(rows), result_response)
        await record_clinical_read(db, scope.value, "ReadPatientDiagnosticReportResults", "diagnostic_report", str(report_id))

    return Ok(response)


async def read_attachment(
    db: AsyncSession, credential: str | None, account_id: UUID, attachment_id: UUID
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        row = await dao_report_attachments.scoped(db, account_id, attachment_id)
        if row is Empty or row.record_status != "valid":
            return Err(AccountObjectNotFound())

        await record_clinical_read(db, scope.value, "ReadReportAttachment", "report_attachment", str(attachment_id))

    content = await report_storage.fetch(account_id, attachment_id)
    state = attachment_response(row)
    return Ok((state, content))
