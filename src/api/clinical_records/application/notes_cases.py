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
from src.api.clinical_records.application.timeline_cases import project_note
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.notes import (
    CreatePatientNotePayload,
    InvalidatePatientNotePayload,
    NoteQuery,
    PatientNoteHistoryResponse,
    PatientNoteResponse,
    UpdatePatientNotePayload,
)
from src.api.clinical_records.repository.dao import dao_note_histories, dao_notes
from src.api.clinical_records.repository.models import PatientNote, PatientNoteHistory
from src.api.encounters.application.encounters_cases import encounter_for_record
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    lock_clinical_patient,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel, PageQuery
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def note_response(row: PatientNote) -> PatientNoteResponse:
    return PatientNoteResponse(
        note_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        body=row.body,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def history_response(row: PatientNoteHistory) -> PatientNoteHistoryResponse:
    return PatientNoteHistoryResponse(
        note_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        body=row.body,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def apply_note_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.notes != "read_write":
        return Err(AccessDenied())

    if action == "CreatePatientNote":
        if not isinstance(payload, CreatePatientNotePayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if await dao_notes.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await lock_clinical_patient(db, context.account.id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        if not await encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = PatientNote(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            body=payload.body,
            captured_at_local=payload.captured_at_local,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_notes.add(db, row)
        event = "created"
    else:
        row = await dao_notes.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidatePatientNote":
            if not isinstance(payload, InvalidatePatientNotePayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdatePatientNote":
            if not isinstance(payload, UpdatePatientNotePayload):
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
        row.date_updated = await clinical_server_time(db)
        row.version += 1
        await dao_notes.flush(db)

    await dao_note_histories.add(
        db,
        PatientNoteHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            body=row.body,
            captured_at_local=row.captured_at_local,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = note_response(row)
    await project_note(db, context.account.id, state)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_note", str(row.id), state, state.version, "clinical_notes"
                )
            ],
            False,
        )
    )


async def read_notes(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: NoteQuery | PageQuery,
    note_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "notes")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if note_id is None:
            if not isinstance(query, NoteQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_notes.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, note_response)
            action = "ReadPatientNotes"
        else:
            row = await dao_notes.get_by(db, where={"account_id": account_id, "id": note_id}, execution_options={"populate_existing": True})

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = note_response(row)
            action = "ReadPatientNote"

        await record_clinical_read(
            db, scope.value, action, "patient_note", str(note_id or patient_id)
        )

    return Ok(response)


async def read_note_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    note_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "notes")

        if isinstance(scope, Err):
            return scope

        row = await dao_notes.get_by(db, where={"account_id": account_id, "id": note_id}, execution_options={"populate_existing": True})

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_note_histories.get_multi(
            db,
            where={"account_id": account_id, "id": note_id},
            page=(query.page - 1) * query.shows,
            shows=query.shows,
            ordering=[("version", False)],
            after_version=query.after_version,
        )
        response = clinical_page(rows, total, history_response)
        await record_clinical_read(
            db, scope.value, "ReadPatientNoteHistory", "patient_note", str(note_id)
        )

    return Ok(response)
