from datetime import datetime
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
from src.api.clinical_records.application.timeline_cases import _date_precision, project_stage3_entry
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
    CorrectDiagnosticReportResultPayload,
    DiagnosticReportResultHistoryResponse,
    DiagnosticReportResultQuery,
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
        created_at=row.date_added,
        updated_at=row.date_updated,
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
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def attachment_response(
    row: ReportAttachment, report_id: UUID | None = None
) -> ReportAttachmentResponse:
    return ReportAttachmentResponse(
        attachment_id=row.id,
        patient_id=row.patient_id,
        report_id=report_id,
        file_name=row.file_name,
        content_type=row.content_type,
        byte_size=row.byte_size,
        sha256=row.sha256,
        uploaded_at=row.uploaded_at,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def _history_fields(state, *extra: str) -> dict:
    data = state.model_dump(exclude={"version", "created_at", "updated_at"})
    for key in ("report_id", "result_id", "attachment_id", *extra):
        data.pop(key, None)
    return data


async def _attachment_matches_report(
    db: AsyncSession, account_id: UUID, patient_id: UUID, attachment_id: UUID
) -> bool:
    attachment = await dao_report_attachments.get_by(db, where={"account_id": account_id, "id": attachment_id}, execution_options={"populate_existing": True})

    return (
        attachment is not Empty
        and attachment.patient_id == patient_id
        and attachment.record_status == "valid"
    )


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
        if await dao_reports.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        if await lock_clinical_patient(db, context.account.id, payload.patient_id) is Empty:
            return Err(AccountObjectNotFound())
        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        if payload.attachment_id is not None and not await _attachment_matches_report(
            db, context.account.id, payload.patient_id, payload.attachment_id
        ):
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
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_reports.add(db, row)
        event = "created"
    else:
        row = await dao_reports.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})
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
            attachment_id = changes.get("attachment_id")
            if attachment_id is not None and not await _attachment_matches_report(
                db, context.account.id, row.patient_id, attachment_id
            ):
                return Err(AccountObjectNotFound())
            for name, value in changes.items():
                setattr(row, name, value)
            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_reports.flush(db)

    state = report_response(row)
    await dao_report_histories.add(
        db,
        DiagnosticReportHistory(
            account_id=row.account_id,
            id=row.id,
            **_history_fields(state),
            attachment_id=row.attachment_id,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )

    occurrence_date, date_precision = _date_precision(row.sample_date or row.issued_date)
    await project_stage3_entry(
        db,
        row.account_id,
        patient_id=row.patient_id,
        entry_type="diagnostic_report",
        entry_id=row.id,
        source_section="diagnostic_reports",
        occurrence_date=occurrence_date,
        occurred_at=row.date_updated,
        date_precision=date_precision,
        accepted_at=row.date_updated,
        entity_version=row.version,
        record_status=row.record_status,
    )
    changes = [
        AccountChange(
            "diagnostic_report",
            str(row.id),
            state,
            state.version,
            "clinical_diagnostic_reports",
        )
    ]
    if action == "CorrectDiagnosticReport" and isinstance(payload, CorrectDiagnosticReportPayload):
        corrected = await _replace_report_results(
            db, context, row, payload, operation_id, row.date_updated
        )
        if isinstance(corrected, Err):
            return corrected
        changes.extend(corrected.value)

    return Ok(AccountEffect(state, state.version, changes, False))


async def _corrected_result_change(
    db: AsyncSession,
    context: AccountContext,
    row: DiagnosticReportResult,
    operation_id: UUID,
    event: str,
) -> AccountChange:
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
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )

    return AccountChange(
        "diagnostic_report_result",
        str(row.id),
        state,
        row.version,
        "clinical_diagnostic_reports",
    )


async def _replace_report_results(
    db: AsyncSession,
    context: AccountContext,
    report: DiagnosticReport,
    payload: CorrectDiagnosticReportPayload,
    operation_id: UUID,
    now: datetime,
) -> Result[list[AccountChange], AccountObjectNotFound]:
    existing = {
        row.id: row
        for row in await dao_report_results.for_report(db, report.account_id, report.id)
    }
    retained = set()
    changes = []

    for item in payload.results:
        row = existing.get(item.result_id)
        if row is None:
            if await dao_report_results.get(db, item.result_id) is not Empty:
                return Err(AccountObjectNotFound())
            row = DiagnosticReportResult(
                id=item.result_id,
                account_id=report.account_id,
                patient_id=report.patient_id,
                report_id=report.id,
                **item.model_dump(exclude={"result_id"}),
                record_status="valid",
                correction_reason=payload.correction_reason,
                created_by_user_id=context.actor.user_id,
                updated_by_user_id=context.actor.user_id,
                date_added=now,
                date_updated=now,
                version=1,
            )
            await dao_report_results.add(db, row)
            event = "created"
        else:
            if row.record_status != "valid":
                return Err(AccountObjectNotFound())
            values = item.model_dump(exclude={"result_id"})
            if all(getattr(row, name) == value for name, value in values.items()):
                retained.add(row.id)
                continue
            for name, value in values.items():
                setattr(row, name, value)
            row.correction_reason = payload.correction_reason
            row.updated_by_user_id = context.actor.user_id
            row.date_updated = now
            row.version += 1
            await dao_report_results.flush(db)
            event = "updated"
        retained.add(row.id)
        changes.append(await _corrected_result_change(db, context, row, operation_id, event))

    for row in existing.values():
        if row.id not in retained and row.record_status == "valid":
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            row.updated_by_user_id = context.actor.user_id
            row.date_updated = now
            row.version += 1
            await dao_report_results.flush(db)
            changes.append(await _corrected_result_change(db, context, row, operation_id, "invalidated"))

    return Ok(changes)


async def _apply_result(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "AddDiagnosticReportResult":
        if not isinstance(payload, AddDiagnosticReportResultPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_report_results.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        report = await dao_reports.get_by(db, where={"account_id": context.account.id, "id": payload.report_id}, execution_options={"populate_existing": True})
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
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_report_results.add(db, row)
        event = "created"
    else:
        row = await dao_report_results.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})
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
        row.date_updated = await clinical_server_time(db)
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
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
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


async def _link_report_attachment(
    db: AsyncSession,
    context: AccountContext,
    report_id: UUID,
    attachment_id: UUID,
    patient_id: UUID,
    operation_id: UUID,
    now: datetime,
) -> Result[AccountChange, AccountObjectNotFound]:
    report = await dao_reports.get_by(db, where={"account_id": context.account.id, "id": report_id}, for_update=True, execution_options={"populate_existing": True})
    if (
        report is Empty
        or report.patient_id != patient_id
        or report.record_status != "valid"
    ):
        return Err(AccountObjectNotFound())

    report.attachment_id = attachment_id
    report.updated_by_user_id = context.actor.user_id
    report.date_updated = now
    report.version += 1
    await dao_reports.flush(db)
    state = report_response(report)
    await dao_report_histories.add(
        db,
        DiagnosticReportHistory(
            account_id=report.account_id,
            id=report.id,
            **_history_fields(state),
            attachment_id=attachment_id,
            created_by_user_id=report.created_by_user_id,
            updated_by_user_id=report.updated_by_user_id,
            date_added=report.date_added,
            date_updated=report.date_updated,
            version=report.version,
            action="updated",
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=now,
        ),
    )

    return Ok(AccountChange(
        "diagnostic_report",
        str(report.id),
        state,
        report.version,
        "clinical_diagnostic_reports",
    ))


async def _apply_attachment(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "UploadReportAttachment":
        if not isinstance(payload, UploadReportAttachmentPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_report_attachments.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
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
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_report_attachments.add(db, row)
        row.storage_key = await report_storage.save(
            context.account.id, entity_key, content
        )
        event = "created"
    else:
        row = await dao_report_attachments.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})
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
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_report_attachments.flush(db)

    report_id = payload.report_id if action == "UploadReportAttachment" else None
    linked = None
    if report_id is not None:
        linked = await _link_report_attachment(
            db, context, report_id, row.id, row.patient_id, operation_id, row.date_updated
        )
        if isinstance(linked, Err):
            return linked

    state = attachment_response(row, report_id)
    await dao_report_attachment_histories.add(
        db,
        ReportAttachmentHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            **_history_fields(state, "patient_id"),
            storage_key=row.storage_key,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )

    changes = [
        AccountChange(
            "report_attachment",
            str(row.id),
            state,
            state.version,
            "clinical_diagnostic_reports",
        )
    ]
    if linked is not None:
        changes.append(linked.value)

    return Ok(AccountEffect(state, state.version, changes, False))


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
            row = await dao_reports.get_by(db, where={"account_id": account_id, "id": report_id}, execution_options={"populate_existing": True})
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

        row = await dao_reports.get_by(db, where={"account_id": account_id, "id": report_id}, execution_options={"populate_existing": True})
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_report_histories.get_multi(
            db,
            where={"account_id": account_id, "id": report_id},
            page=(query.page - 1) * query.shows,
            shows=query.shows,
            ordering=[("version", False)],
            after_version=query.after_version,
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
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


async def read_report_results(
    db, credential, account_id, patient_id, report_id, query: DiagnosticReportResultQuery
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        report = await dao_reports.get_by(db, where={"account_id": account_id, "id": report_id}, execution_options={"populate_existing": True})
        if report is Empty or report.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_report_results.page_for_report(
            db, account_id, report_id, query
        )
        response = clinical_page(rows, total, result_response)
        await record_clinical_read(db, scope.value, "ReadPatientDiagnosticReportResults", "diagnostic_report", str(report_id))

    return Ok(response)


async def read_attachment(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    attachment_id: UUID,
    load_content: bool = False,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "diagnostic_reports")
        if isinstance(scope, Err):
            return scope

        row = await dao_report_attachments.get_by(db, where={"account_id": account_id, "id": attachment_id}, execution_options={"populate_existing": True})
        if (
            row is Empty
            or row.patient_id != patient_id
            or row.record_status != "valid"
        ):
            return Err(AccountObjectNotFound())

        report_id = await dao_reports.for_attachment(db, account_id, attachment_id)
        await record_clinical_read(db, scope.value, "ReadReportAttachment", "report_attachment", str(attachment_id))

    content = await report_storage.fetch(row.storage_key) if load_content else None
    state = attachment_response(row, report_id)
    return Ok((state, content))
