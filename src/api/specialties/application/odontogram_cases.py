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
from src.api.encounters.application.encounters_cases import valid_encounter_for_record
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    lock_clinical_patient,
)
from src.api.specialties.domain.odontogram import (
    AddDentalTreatmentPayload,
    DentalFindingHistoryResponse,
    DentalFindingQuery,
    DentalFindingResponse,
    DentalTreatmentHistoryResponse,
    DentalTreatmentResponse,
    InvalidateDentalFindingPayload,
    InvalidateDentalTreatmentPayload,
    RecordDentalFindingPayload,
    ResolveDentalFindingPayload,
    UpdateDentalFindingPayload,
    UpdateDentalTreatmentPayload,
)
from src.api.specialties.repository.models import (
    DentalFinding,
    DentalFindingHistory,
    DentalTreatment,
    DentalTreatmentHistory,
)
from src.api.specialties.repository.specialty_dao import (
    dao_dental_finding_histories,
    dao_dental_findings,
    dao_dental_treatment_histories,
    dao_dental_treatments,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

FINDING_ACTIONS = ("RecordDentalFinding", "UpdateDentalFinding", "ResolveDentalFinding", "InvalidateDentalFinding")
TREATMENT_ACTIONS = ("AddDentalTreatment", "UpdateDentalTreatment", "InvalidateDentalTreatment")


def finding_response(row: DentalFinding) -> DentalFindingResponse:
    return DentalFindingResponse(
        finding_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        tooth_fdi=row.tooth_fdi,
        surface=row.surface,
        finding_kind=row.finding_kind,
        finding_status=row.finding_status,
        note=row.note,
        recorded_date=row.recorded_date,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def treatment_response(row: DentalTreatment) -> DentalTreatmentResponse:
    return DentalTreatmentResponse(
        treatment_id=row.id,
        finding_id=row.finding_id,
        patient_id=row.patient_id,
        treatment_kind=row.treatment_kind,
        treatment_status=row.treatment_status,
        note=row.note,
        performed_date=row.performed_date,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def _finding_history_fields(state) -> dict:
    data = state.model_dump(exclude={"finding_id", "version", "created_at", "updated_at"})
    return data


def _treatment_history_fields(state) -> dict:
    data = state.model_dump(exclude={"treatment_id", "version", "created_at", "updated_at"})
    return data


async def apply_dental_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.specialty_templates != "read_write":
        return Err(AccessDenied())

    if action in FINDING_ACTIONS:
        return await _apply_finding(db, context, action, entity_key, expected_version, payload, operation_id)

    if action in TREATMENT_ACTIONS:
        return await _apply_treatment(db, context, action, entity_key, expected_version, payload, operation_id)

    return Err(AccountRuleError("UNSUPPORTED_OPERATION"))


async def _apply_finding(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "RecordDentalFinding":
        if not isinstance(payload, RecordDentalFindingPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_dental_findings.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        if await lock_clinical_patient(db, context.account.id, payload.patient_id) is Empty:
            return Err(AccountObjectNotFound())
        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        duplicate = await _active_duplicate(db, context, payload)
        if duplicate:
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", 1))

        now = await clinical_server_time(db)
        row = DentalFinding(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            **payload.model_dump(exclude={"patient_id", "encounter_id"}),
            finding_status="active",
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_dental_findings.add(db, row)
        event = "created"
    else:
        row = await dao_dental_findings.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateDentalFinding":
            if not isinstance(payload, InvalidateDentalFindingPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "ResolveDentalFinding":
            if not isinstance(payload, ResolveDentalFindingPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            if row.finding_status == "resolved":
                return Err(AccountRuleError("NO_CHANGES", row.version))
            row.finding_status = "resolved"
            event = "updated"
        elif action == "UpdateDentalFinding":
            if not isinstance(payload, UpdateDentalFindingPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            changes = payload.model_dump(exclude_unset=True)
            candidate_tooth = changes.get("tooth_fdi", row.tooth_fdi)
            candidate_surface = changes.get("surface", row.surface)
            candidate_kind = changes.get("finding_kind", row.finding_kind)
            if (candidate_tooth, candidate_surface, candidate_kind) != (
                row.tooth_fdi, row.surface, row.finding_kind,
            ):
                duplicate = await _active_duplicate_values(
                    db, context, row.patient_id, candidate_tooth, candidate_surface,
                    candidate_kind, exclude_id=row.id,
                )
                if duplicate:
                    return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))
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
        await dao_dental_findings.flush(db)

    state = finding_response(row)
    await dao_dental_finding_histories.add(
        db,
        DentalFindingHistory(
            account_id=row.account_id,
            id=row.id,
            **_finding_history_fields(state),
            version=row.version,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
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
            [AccountChange("dental_finding", str(row.id), state, state.version, "clinical_specialty_templates")],
            False,
        )
    )


async def _active_duplicate(db, context, payload) -> bool:
    return await _active_duplicate_values(
        db, context, payload.patient_id, payload.tooth_fdi, payload.surface,
        payload.finding_kind,
    )


async def _active_duplicate_values(db, context, patient_id, tooth_fdi, surface, finding_kind, exclude_id=None) -> bool:
    from sqlalchemy import select

    statement = select(DentalFinding.id).where(
        DentalFinding.account_id == context.account.id,
        DentalFinding.patient_id == patient_id,
        DentalFinding.tooth_fdi == tooth_fdi,
        DentalFinding.finding_kind == finding_kind,
        DentalFinding.finding_status == "active",
        DentalFinding.record_status == "valid",
        DentalFinding.surface.is_(None) if surface is None else DentalFinding.surface == surface,
    )
    if exclude_id is not None:
        statement = statement.where(DentalFinding.id != exclude_id)

    return await db.scalar(statement) is not None


async def _apply_treatment(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "AddDentalTreatment":
        if not isinstance(payload, AddDentalTreatmentPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_dental_treatments.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True}) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        finding = await dao_dental_findings.get_by(db, where={"account_id": context.account.id, "id": payload.finding_id}, execution_options={"populate_existing": True})
        if finding is Empty or finding.patient_id != payload.patient_id or finding.record_status != "valid":
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = DentalTreatment(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            finding_id=payload.finding_id,
            **payload.model_dump(exclude={"finding_id", "patient_id"}),
            treatment_status="planned",
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_dental_treatments.add(db, row)
        event = "created"
    else:
        row = await dao_dental_treatments.get_by(db, where={"account_id": context.account.id, "id": entity_key}, for_update=True, execution_options={"populate_existing": True})
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateDentalTreatment":
            if not isinstance(payload, InvalidateDentalTreatmentPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdateDentalTreatment":
            if not isinstance(payload, UpdateDentalTreatmentPayload):
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
        await dao_dental_treatments.flush(db)

    state = treatment_response(row)
    await dao_dental_treatment_histories.add(
        db,
        DentalTreatmentHistory(
            account_id=row.account_id,
            id=row.id,
            **_treatment_history_fields(state),
            version=row.version,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            date_added=row.date_added,
            date_updated=row.date_updated,
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
            [AccountChange("dental_treatment", str(row.id), state, state.version, "clinical_specialty_templates")],
            False,
        )
    )


async def read_dental_findings(
    db, credential, account_id, patient_id, query: DentalFindingQuery | PageQuery, finding_id=None
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if finding_id is None:
            if not isinstance(query, DentalFindingQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            rows, total = await dao_dental_findings.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, finding_response)
            action = "ReadDentalFindings"
        else:
            row = await dao_dental_findings.get_by(db, where={"account_id": account_id, "id": finding_id}, execution_options={"populate_existing": True})
            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            response = finding_response(row)
            action = "ReadDentalFinding"

        await record_clinical_read(db, scope.value, action, "dental_finding", str(finding_id or patient_id))

    return Ok(response)


async def read_dental_finding_history(db, credential, account_id, patient_id, finding_id, query: ClinicalHistoryQuery):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        row = await dao_dental_findings.get_by(db, where={"account_id": account_id, "id": finding_id}, execution_options={"populate_existing": True})
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_dental_finding_histories.get_multi(
            db, where={"account_id": account_id, "id": finding_id},
            page=(query.page - 1) * query.shows, shows=query.shows,
            ordering=[("version", False)], after_version=query.after_version,
        )
        response = clinical_page(rows, total, _finding_history)
        await record_clinical_read(db, scope.value, "ReadDentalFindingHistory", "dental_finding", str(finding_id))

    return Ok(response)


def _finding_history(row: DentalFindingHistory) -> DentalFindingHistoryResponse:
    return DentalFindingHistoryResponse(
        finding_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        tooth_fdi=row.tooth_fdi,
        surface=row.surface,
        finding_kind=row.finding_kind,
        finding_status=row.finding_status,
        note=row.note,
        recorded_date=row.recorded_date,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


async def read_dental_treatments(db, credential, account_id, patient_id, finding_id, treatment_id=None):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        finding = await dao_dental_findings.get_by(db, where={"account_id": account_id, "id": finding_id}, execution_options={"populate_existing": True})
        if finding is Empty or finding.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        if treatment_id is None:
            rows = await dao_dental_treatments.for_finding(db, account_id, finding_id)
            response = clinical_page(rows, len(rows), treatment_response)
            action = "ReadDentalTreatments"
        else:
            row = await dao_dental_treatments.get_by(db, where={"account_id": account_id, "id": treatment_id}, execution_options={"populate_existing": True})
            if row is Empty or row.finding_id != finding_id:
                return Err(AccountObjectNotFound())
            response = treatment_response(row)
            action = "ReadDentalTreatment"

        await record_clinical_read(db, scope.value, action, "dental_treatment", str(treatment_id or finding_id))

    return Ok(response)


async def read_dental_treatment_history(db, credential, account_id, patient_id, treatment_id, query: ClinicalHistoryQuery):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        row = await dao_dental_treatments.get_by(db, where={"account_id": account_id, "id": treatment_id}, execution_options={"populate_existing": True})
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_dental_treatment_histories.get_multi(
            db, where={"account_id": account_id, "id": treatment_id},
            page=(query.page - 1) * query.shows, shows=query.shows,
            ordering=[("version", False)], after_version=query.after_version,
        )
        response = clinical_page(rows, total, _treatment_history)
        await record_clinical_read(db, scope.value, "ReadDentalTreatmentHistory", "dental_treatment", str(treatment_id))

    return Ok(response)


def _treatment_history(row: DentalTreatmentHistory) -> DentalTreatmentHistoryResponse:
    return DentalTreatmentHistoryResponse(
        treatment_id=row.id,
        finding_id=row.finding_id,
        patient_id=row.patient_id,
        treatment_kind=row.treatment_kind,
        treatment_status=row.treatment_status,
        note=row.note,
        performed_date=row.performed_date,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )


async def read_dental_treatment_for_patient(db, credential, account_id, patient_id, treatment_id):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        row = await dao_dental_treatments.get_by(db, where={"account_id": account_id, "id": treatment_id}, execution_options={"populate_existing": True})
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        await record_clinical_read(
            db, scope.value, "ReadDentalTreatment", "dental_treatment", str(treatment_id)
        )

    return Ok(treatment_response(row))
