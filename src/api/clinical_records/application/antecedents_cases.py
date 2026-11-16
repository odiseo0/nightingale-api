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
from src.api.clinical_records.application.timeline_cases import project_antecedent
from src.api.clinical_records.domain.antecedents import (
    AntecedentQuery,
    CreatePatientAntecedentPayload,
    InvalidatePatientAntecedentPayload,
    PatientAntecedentHistoryResponse,
    PatientAntecedentResponse,
    UpdatePatientAntecedentPayload,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.repository.dao import (
    dao_antecedent_histories,
    dao_antecedents,
)
from src.api.clinical_records.repository.models import (
    PatientAntecedent,
    PatientAntecedentHistory,
)
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


def antecedent_response(row: PatientAntecedent) -> PatientAntecedentResponse:
    return PatientAntecedentResponse(
        antecedent_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        category=row.category,
        content=row.content,
        related_person_description=row.related_person_description,
        occurrence_date=row.occurrence_date,
        source_type=row.source_type,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def history_response(row: PatientAntecedentHistory) -> PatientAntecedentHistoryResponse:
    return PatientAntecedentHistoryResponse(
        antecedent_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        category=row.category,
        content=row.content,
        related_person_description=row.related_person_description,
        occurrence_date=row.occurrence_date,
        source_type=row.source_type,
        captured_at_local=row.captured_at_local,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def apply_antecedent_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.antecedents != "read_write":
        return Err(AccessDenied())

    if action == "CreatePatientAntecedent":
        if not isinstance(payload, CreatePatientAntecedentPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_antecedents.scoped(db, context.account.id, entity_key)
            is not Empty
        ):
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
        row = PatientAntecedent(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            **payload.model_dump(exclude={"patient_id", "encounter_id"}),
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_antecedents.add(db, row)
        event = "created"
    else:
        row = await dao_antecedents.scoped(
            db, context.account.id, entity_key, lock=True
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidatePatientAntecedent":
            if not isinstance(payload, InvalidatePatientAntecedentPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdatePatientAntecedent":
            if not isinstance(payload, UpdatePatientAntecedentPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)

            if (
                changes.get("category", row.category) == "family"
                and changes.get(
                    "related_person_description", row.related_person_description
                )
                is None
            ):
                return Err(AccountRuleError("VALIDATION_ERROR", row.version))

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
        await dao_antecedents.flush(db)

    await dao_antecedent_histories.add(
        db,
        PatientAntecedentHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            category=row.category,
            content=row.content,
            related_person_description=row.related_person_description,
            occurrence_date=row.occurrence_date,
            source_type=row.source_type,
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
    state = antecedent_response(row)
    await project_antecedent(db, context.account.id, state)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_antecedent",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_antecedents",
                )
            ],
            False,
        )
    )


async def read_antecedents(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: AntecedentQuery | PageQuery,
    antecedent_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "antecedents")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if antecedent_id is None:
            if not isinstance(query, AntecedentQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_antecedents.page(db, account_id, patient_id, query)
            response = clinical_page(rows, total, antecedent_response)
            action = "ReadPatientAntecedents"
        else:
            row = await dao_antecedents.scoped(db, account_id, antecedent_id)

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = antecedent_response(row)
            action = "ReadPatientAntecedent"

        await record_clinical_read(
            db,
            scope.value,
            action,
            "patient_antecedent",
            str(antecedent_id or patient_id),
        )

    return Ok(response)


async def read_antecedent_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    antecedent_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "antecedents")

        if isinstance(scope, Err):
            return scope

        row = await dao_antecedents.scoped(db, account_id, antecedent_id)

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_antecedent_histories.page(
            db,
            account_id,
            antecedent_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(rows, total, history_response)
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientAntecedentHistory",
            "patient_antecedent",
            str(antecedent_id),
        )

    return Ok(response)
