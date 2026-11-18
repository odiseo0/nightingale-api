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
from src.api.medications.domain.medications import (
    DeclaredMedicationHistoryResponse,
    DeclaredMedicationQuery,
    DeclaredMedicationResponse,
    DeclarePatientMedicationPayload,
    InvalidatePatientDeclaredMedicationPayload,
    UpdatePatientDeclaredMedicationPayload,
)
from src.api.medications.domain.reviews import ReviewPatientDeclaredMedicationPayload
from src.api.medications.repository.dao import (
    dao_declared_medication_histories,
    dao_declared_medications,
)
from src.api.medications.repository.models import (
    DeclaredMedication,
    DeclaredMedicationHistory,
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


def medication_response(row: DeclaredMedication) -> DeclaredMedicationResponse:
    return DeclaredMedicationResponse(
        medication_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        medication_name=row.medication_name,
        source_type=row.source_type,
        start_date=row.start_date,
        end_date=row.end_date,
        dose_description=row.dose_description,
        frequency_description=row.frequency_description,
        prescriber_name=row.prescriber_name,
        route_description=row.route_description,
        review_status=row.review_status,
        reviewed_at=row.reviewed_at,
        reviewed_by_user_id=row.reviewed_by_user_id,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def history_response(
    row: DeclaredMedicationHistory,
) -> DeclaredMedicationHistoryResponse:
    return DeclaredMedicationHistoryResponse(
        medication_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        medication_name=row.medication_name,
        source_type=row.source_type,
        start_date=row.start_date,
        end_date=row.end_date,
        dose_description=row.dose_description,
        frequency_description=row.frequency_description,
        prescriber_name=row.prescriber_name,
        route_description=row.route_description,
        review_status=row.review_status,
        reviewed_at=row.reviewed_at,
        reviewed_by_user_id=row.reviewed_by_user_id,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def apply_declared_medication_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.declared_medications != "read_write":
        return Err(AccessDenied())

    if action == "DeclarePatientMedication":
        if not isinstance(payload, DeclarePatientMedicationPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_declared_medications.scoped(
                db, context.account.id, entity_key
            )
            is not Empty
        ):
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        if (
            await lock_clinical_patient(db, context.account.id, payload.patient_id)
            is Empty
        ):
            return Err(AccountObjectNotFound())

        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        now = await clinical_server_time(db)
        row = DeclaredMedication(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            **payload.model_dump(exclude={"patient_id", "encounter_id"}),
            review_status="declared",
            reviewed_at=None,
            reviewed_by_user_id=None,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_declared_medications.add(db, row)
        event = "created"
    else:
        row = await dao_declared_medications.scoped(
            db, context.account.id, entity_key, lock=True
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        now = await clinical_server_time(db)

        if action == "InvalidatePatientDeclaredMedication":
            if not isinstance(payload, InvalidatePatientDeclaredMedicationPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "ReviewPatientDeclaredMedication":
            if not isinstance(payload, ReviewPatientDeclaredMedicationPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            if row.review_status == "reviewed":
                return Err(AccountRuleError("NO_CHANGES", row.version))

            row.review_status = "reviewed"
            row.reviewed_at = now
            row.reviewed_by_user_id = context.actor.user_id
            event = "updated"
        elif action == "UpdatePatientDeclaredMedication":
            if not isinstance(payload, UpdatePatientDeclaredMedicationPayload):
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
        row.updated_at = now
        row.version += 1
        await dao_declared_medications.flush(db)

    await dao_declared_medication_histories.add(
        db,
        DeclaredMedicationHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            medication_name=row.medication_name,
            source_type=row.source_type,
            start_date=row.start_date,
            end_date=row.end_date,
            dose_description=row.dose_description,
            frequency_description=row.frequency_description,
            prescriber_name=row.prescriber_name,
            route_description=row.route_description,
            review_status=row.review_status,
            reviewed_at=row.reviewed_at,
            reviewed_by_user_id=row.reviewed_by_user_id,
            captured_at_local=row.captured_at_local,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.updated_at,
        ),
    )
    state = medication_response(row)
    from src.api.clinical_records.application.timeline_cases import (
        _date_precision,
        project_stage3_entry,
    )

    occurrence_date, date_precision = _date_precision(row.start_date)
    await project_stage3_entry(
        db,
        row.account_id,
        patient_id=row.patient_id,
        entry_type="declared_medication",
        entry_id=row.id,
        source_section="declared_medications",
        occurrence_date=occurrence_date,
        occurred_at=row.updated_at,
        date_precision=date_precision,
        accepted_at=row.updated_at,
        entity_version=row.version,
        record_status=row.record_status,
    )

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "declared_medication",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_declared_medications",
                )
            ],
            False,
        )
    )


async def read_declared_medications(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: DeclaredMedicationQuery | PageQuery,
    medication_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(
            db, credential, account_id, "declared_medications"
        )

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if medication_id is None:
            if not isinstance(query, DeclaredMedicationQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_declared_medications.page(
                db, account_id, patient_id, query
            )
            response = clinical_page(rows, total, medication_response)
            action = "ReadPatientDeclaredMedications"
        else:
            row = await dao_declared_medications.scoped(
                db, account_id, medication_id
            )

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = medication_response(row)
            action = "ReadPatientDeclaredMedication"

        await record_clinical_read(
            db,
            scope.value,
            action,
            "declared_medication",
            str(medication_id or patient_id),
        )

    return Ok(response)


async def read_declared_medication_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    medication_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(
            db, credential, account_id, "declared_medications"
        )

        if isinstance(scope, Err):
            return scope

        row = await dao_declared_medications.scoped(db, account_id, medication_id)

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_declared_medication_histories.page(
            db,
            account_id,
            medication_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(rows, total, history_response)
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientDeclaredMedicationHistory",
            "declared_medication",
            str(medication_id),
        )

    return Ok(response)
