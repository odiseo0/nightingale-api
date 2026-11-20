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
from src.api.clinical_records.application.timeline_cases import project_immunization
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.immunizations import (
    ImmunizationQuery,
    InvalidatePatientImmunizationPayload,
    PatientImmunizationHistoryResponse,
    PatientImmunizationResponse,
    RecordPatientImmunizationPayload,
    UpdatePatientImmunizationPayload,
)
from src.api.clinical_records.repository.dao import (
    dao_immunization_histories,
    dao_immunizations,
)
from src.api.clinical_records.repository.models import (
    PatientImmunization,
    PatientImmunizationHistory,
)
from src.api.encounters.application.encounters_cases import valid_encounter_for_record
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


def immunization_response(row: PatientImmunization) -> PatientImmunizationResponse:
    return PatientImmunizationResponse(
        immunization_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        vaccine_name=row.vaccine_name,
        occurrence_date=row.occurrence_date,
        record_kind=row.record_kind,
        source_type=row.source_type,
        captured_at_local=row.captured_at_local,
        product_name=row.product_name,
        dose_description=row.dose_description,
        lot_number=row.lot_number,
        route=row.route,
        body_site=row.body_site,
        location_text=row.location_text,
        administrator_name=row.administrator_name,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.date_added,
        updated_at=row.date_updated,
        version=row.version,
    )


def history_response(
    row: PatientImmunizationHistory,
) -> PatientImmunizationHistoryResponse:
    return PatientImmunizationHistoryResponse(
        immunization_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        vaccine_name=row.vaccine_name,
        occurrence_date=row.occurrence_date,
        record_kind=row.record_kind,
        source_type=row.source_type,
        captured_at_local=row.captured_at_local,
        product_name=row.product_name,
        dose_description=row.dose_description,
        lot_number=row.lot_number,
        route=row.route,
        body_site=row.body_site,
        location_text=row.location_text,
        administrator_name=row.administrator_name,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def apply_immunization_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.immunizations != "read_write":
        return Err(AccessDenied())

    if action == "RecordPatientImmunization":
        if not isinstance(payload, RecordPatientImmunizationPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_immunizations.get_by(db, where={"account_id": context.account.id, "id": entity_key}, execution_options={"populate_existing": True})
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
        row = PatientImmunization(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            **payload.model_dump(exclude={"patient_id", "encounter_id"}),
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_immunizations.add(db, row)
        event = "created"
    else:
        row = await dao_immunizations.get_by(
            db, where={"account_id": context.account.id, "id": entity_key},
            for_update=True, execution_options={"populate_existing": True}
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidatePatientImmunization":
            if not isinstance(payload, InvalidatePatientImmunizationPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdatePatientImmunization":
            if not isinstance(payload, UpdatePatientImmunizationPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)

            if changes.get(
                "record_kind", row.record_kind
            ) == "administered_here" and not await valid_encounter_for_record(
                db, context.account.id, row.patient_id, row.encounter_id
            ):
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
        await dao_immunizations.flush(db)

    await dao_immunization_histories.add(
        db,
        PatientImmunizationHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            vaccine_name=row.vaccine_name,
            occurrence_date=row.occurrence_date,
            record_kind=row.record_kind,
            source_type=row.source_type,
            captured_at_local=row.captured_at_local,
            product_name=row.product_name,
            dose_description=row.dose_description,
            lot_number=row.lot_number,
            route=row.route,
            body_site=row.body_site,
            location_text=row.location_text,
            administrator_name=row.administrator_name,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.date_updated,
        ),
    )
    state = immunization_response(row)
    await project_immunization(db, context.account.id, state)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_immunization",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_immunizations",
                )
            ],
            False,
        )
    )


async def read_immunizations(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: ImmunizationQuery | PageQuery,
    immunization_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "immunizations")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if immunization_id is None:
            if not isinstance(query, ImmunizationQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_immunizations.page(
                db, account_id, patient_id, query
            )
            response = clinical_page(rows, total, immunization_response)
            action = "ReadPatientImmunizations"
        else:
            row = await dao_immunizations.get_by(db, where={"account_id": account_id, "id": immunization_id}, execution_options={"populate_existing": True})

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = immunization_response(row)
            action = "ReadPatientImmunization"

        await record_clinical_read(
            db,
            scope.value,
            action,
            "patient_immunization",
            str(immunization_id or patient_id),
        )

    return Ok(response)


async def read_immunization_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    immunization_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "immunizations")

        if isinstance(scope, Err):
            return scope

        row = await dao_immunizations.get_by(db, where={"account_id": account_id, "id": immunization_id}, execution_options={"populate_existing": True})

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_immunization_histories.get_multi(
            db,
            where={"account_id": account_id, "id": immunization_id},
            page=(query.page - 1) * query.shows,
            shows=query.shows,
            ordering=[("version", False)],
            after_version=query.after_version,
        )
        response = clinical_page(rows, total, history_response)
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientImmunizationHistory",
            "patient_immunization",
            str(immunization_id),
        )

    return Ok(response)
