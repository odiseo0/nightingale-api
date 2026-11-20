from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.accounts_cases import encounter_participants
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.appointments.application.appointments_cases import encounter_appointment
from src.api.authorization.domain.errors import AccessDenied
from src.api.clinical_records.application.access_cases import (
    clinical_page,
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.application.timeline_cases import project_encounter
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.encounters.domain.encounters import (
    CreatePatientEncounterPayload,
    EncounterQuery,
    InvalidatePatientEncounterPayload,
    LastVisitResponse,
    PatientEncounterHistoryResponse,
    PatientEncounterResponse,
    UpdatePatientEncounterPayload,
)
from src.api.encounters.repository.dao import dao_encounter_histories, dao_encounters
from src.api.encounters.repository.models import (
    ClinicalEncounter,
    ClinicalEncounterHistory,
)
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


def encounter_response(row: ClinicalEncounter) -> PatientEncounterResponse:
    return PatientEncounterResponse(
        encounter_id=row.id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        attending_professional_id=row.attending_professional_id,
        assistant_user_id=row.assistant_user_id,
        occurred_at=row.occurred_at,
        ended_at=row.ended_at,
        captured_at_local=row.captured_at_local,
        reason=row.reason,
        reason_source_type=row.reason_source_type,
        history_present_illness=row.history_present_illness,
        findings=row.findings,
        assessment=row.assessment,
        indications=row.indications,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def encounter_history_response(
    row: ClinicalEncounterHistory,
) -> PatientEncounterHistoryResponse:
    return PatientEncounterHistoryResponse(
        encounter_id=row.id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        attending_professional_id=row.attending_professional_id,
        assistant_user_id=row.assistant_user_id,
        occurred_at=row.occurred_at,
        ended_at=row.ended_at,
        captured_at_local=row.captured_at_local,
        reason=row.reason,
        reason_source_type=row.reason_source_type,
        history_present_illness=row.history_present_illness,
        findings=row.findings,
        assessment=row.assessment,
        indications=row.indications,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def record_history(
    db: AsyncSession,
    context: AccountContext,
    row: ClinicalEncounter,
    action: str,
    operation_id: UUID,
) -> None:
    await dao_encounter_histories.add(
        db,
        ClinicalEncounterHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            appointment_id=row.appointment_id,
            attending_professional_id=row.attending_professional_id,
            assistant_user_id=row.assistant_user_id,
            occurred_at=row.occurred_at,
            ended_at=row.ended_at,
            captured_at_local=row.captured_at_local,
            reason=row.reason,
            reason_source_type=row.reason_source_type,
            history_present_illness=row.history_present_illness,
            findings=row.findings,
            assessment=row.assessment,
            indications=row.indications,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )


async def apply_encounter_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
    occurred_at_local: datetime | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.encounters != "read_write":
        return Err(AccessDenied())

    if action == "CreatePatientEncounter":
        if not isinstance(payload, CreatePatientEncounterPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if await dao_encounters.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await lock_clinical_patient(db, context.account.id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        if not await encounter_appointment(
            db, context.account.id, payload.patient_id, payload.appointment_id
        ) or not await encounter_participants(
            db,
            context.account.id,
            payload.attending_professional_id,
            payload.assistant_user_id,
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        captured = payload.captured_at_local or occurred_at_local
        occurred = payload.occurred_at or captured or now

        if occurred > now or payload.ended_at is not None and payload.ended_at > now:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if payload.ended_at is not None and payload.ended_at < occurred:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        row = ClinicalEncounter(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            attending_professional_id=payload.attending_professional_id,
            assistant_user_id=payload.assistant_user_id,
            occurred_at=occurred,
            ended_at=payload.ended_at,
            captured_at_local=captured,
            reason=payload.reason,
            reason_source_type=payload.reason_source_type,
            history_present_illness=payload.history_present_illness,
            findings=payload.findings,
            assessment=payload.assessment,
            indications=payload.indications,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_encounters.add(db, row)
        event = "created"
    else:
        row = await dao_encounters.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        now = await clinical_server_time(db)

        if action == "InvalidatePatientEncounter":
            if not isinstance(payload, InvalidatePatientEncounterPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdatePatientEncounter":
            if not isinstance(payload, UpdatePatientEncounterPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)
            occurred = changes.get("occurred_at", row.occurred_at)
            ended = changes.get("ended_at", row.ended_at)

            if (
                occurred > now
                or ended is not None
                and (ended > now or ended < occurred)
            ):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if all(getattr(row, name) == value for name, value in changes.items()):
                return Err(AccountRuleError("NO_CHANGES", row.version))

            for name, value in changes.items():
                setattr(row, name, value)

            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.date_updated = now
        row.version += 1
        await dao_encounters.flush(db)

    await record_history(db, context, row, event, operation_id)
    state = encounter_response(row)
    await project_encounter(db, context.account.id, state)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "clinical_encounter",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_encounters",
                )
            ],
            False,
        )
    )


async def encounter_for_record(
    db: AsyncSession, account_id: UUID, patient_id: UUID, encounter_id: UUID | None
) -> bool:
    if encounter_id is None:
        return True

    row = await dao_encounters.get_by(db, where={"account_id": account_id, "id": encounter_id}, execution_options={"populate_existing": True})

    return row is not Empty and row.patient_id == patient_id


async def valid_encounter_for_record(
    db: AsyncSession, account_id: UUID, patient_id: UUID, encounter_id: UUID | None
) -> bool:
    if encounter_id is None:
        return False

    row = await dao_encounters.get_by(db, where={"account_id": account_id, "id": encounter_id}, execution_options={"populate_existing": True})

    return (
        row is not Empty
        and row.patient_id == patient_id
        and row.record_status == "valid"
    )


async def read_encounters(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: EncounterQuery | PageQuery,
    encounter_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "encounters")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if encounter_id is None:
            if not isinstance(query, EncounterQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_encounters.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, encounter_response)
            action = "ReadPatientEncounters"
        else:
            row = await dao_encounters.get_by(db, where={"account_id": account_id, "id": encounter_id}, execution_options={"populate_existing": True})

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = encounter_response(row)
            action = "ReadPatientEncounter"

        await record_clinical_read(
            db,
            scope.value,
            action,
            "clinical_encounter",
            str(encounter_id or patient_id),
        )

    return Ok(response)


async def read_encounter_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    encounter_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "encounters")

        if isinstance(scope, Err):
            return scope

        row = await dao_encounters.get_by(db, where={"account_id": account_id, "id": encounter_id}, execution_options={"populate_existing": True})

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_encounter_histories.get_multi(
            db,
            where={"account_id": account_id, "id": encounter_id},
            page=(query.page - 1) * query.shows,
            shows=query.shows,
            ordering=[("version", False)],
            after_version=query.after_version,
        )
        response = clinical_page(rows, total, encounter_history_response)
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientEncounterHistory",
            "clinical_encounter",
            str(encounter_id),
        )

    return Ok(response)


async def read_last_visit(
    db: AsyncSession, credential: str | None, account_id: UUID, patient_id: UUID
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "encounters")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        row = await dao_encounters.latest_valid(db, account_id, patient_id)
        response = LastVisitResponse(
            encounter_id=None if row is Empty else row.id,
            occurred_at=None if row is Empty else row.occurred_at,
        )
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientLastVisit",
            "clinical_encounter",
            str(patient_id),
        )

    return Ok(response)
