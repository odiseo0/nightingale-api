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
from src.api.clinical_records.application.timeline_cases import project_measurement
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.measurements import (
    CorrectPatientMeasurementPayload,
    InvalidatePatientMeasurementPayload,
    MeasurementQuery,
    MeasurementSummaryResponse,
    MeasurementValues,
    PatientMeasurementHistoryResponse,
    PatientMeasurementResponse,
    RecordPatientMeasurementPayload,
)
from src.api.clinical_records.repository.dao import (
    dao_measurement_histories,
    dao_measurements,
)
from src.api.clinical_records.repository.models import (
    PatientMeasurement,
    PatientMeasurementHistory,
)
from src.api.encounters.application.encounters_cases import encounter_for_record
from src.api.patients.application.patients_cases import (
    clinical_date,
    clinical_patient,
    clinical_server_time,
    lock_clinical_patient,
)
from src.api.patients.domain.patients import PatientProfileResponse
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.schema import BaseModel, PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def measurement_response(
    db: AsyncSession,
    context: AccountContext,
    row: PatientMeasurement,
    patient: PatientProfileResponse | None = None,
) -> PatientMeasurementResponse:
    patient = patient or await clinical_patient(db, context.account.id, row.patient_id)
    if patient is Empty or patient is None:
        raise DAOError("La ficha de la medición no existe")

    day = await clinical_date(db, context.account.time_zone, row.measured_at)
    birth = patient.birth_date
    age_years = (
        None
        if birth is None
        else (day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day)))
    )

    return PatientMeasurementResponse(
        measurement_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        kind=row.kind,
        measured_at=row.measured_at,
        captured_at_local=row.captured_at_local,
        method=row.method,
        body_site=row.body_site,
        value=row.value,
        systolic_value=row.systolic_value,
        diastolic_value=row.diastolic_value,
        unit=row.unit,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        age_years=age_years,
        age_as_of=day,
        patient_version=patient.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def history_response(
    row: PatientMeasurementHistory,
) -> PatientMeasurementHistoryResponse:
    return PatientMeasurementHistoryResponse(
        measurement_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        kind=row.kind,
        measured_at=row.measured_at,
        captured_at_local=row.captured_at_local,
        method=row.method,
        body_site=row.body_site,
        value=row.value,
        systolic_value=row.systolic_value,
        diastolic_value=row.diastolic_value,
        unit=row.unit,
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def apply_measurement_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
    occurred_at_local: datetime | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.measurements != "read_write":
        return Err(AccessDenied())

    if action == "RecordPatientMeasurement":
        if not isinstance(payload, RecordPatientMeasurementPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if (
            await dao_measurements.scoped(db, context.account.id, entity_key)
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
        captured = payload.captured_at_local or occurred_at_local
        measured = payload.measured_at or captured or now

        if measured > now:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        row = PatientMeasurement(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            kind=payload.kind,
            measured_at=measured,
            captured_at_local=captured,
            method=payload.method,
            body_site=payload.body_site,
            value=payload.value,
            systolic_value=payload.systolic_value,
            diastolic_value=payload.diastolic_value,
            unit=payload.unit,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_measurements.add(db, row)
        event = "created"
    else:
        row = await dao_measurements.scoped(
            db, context.account.id, entity_key, lock=True
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        now = await clinical_server_time(db)

        if action == "InvalidatePatientMeasurement":
            if not isinstance(payload, InvalidatePatientMeasurementPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "CorrectPatientMeasurement":
            if not isinstance(payload, CorrectPatientMeasurementPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            changes = payload.model_dump(exclude_unset=True)
            measured = changes.get("measured_at", row.measured_at)

            if measured > now:
                return Err(AccountRuleError("VALIDATION_ERROR"))
            try:
                MeasurementValues(
                    kind=row.kind,
                    unit=row.unit,
                    measured_at=measured,
                    captured_at_local=changes.get(
                        "captured_at_local", row.captured_at_local
                    ),
                    method=changes.get("method", row.method),
                    body_site=changes.get("body_site", row.body_site),
                    value=changes.get("value", row.value),
                    systolic_value=changes.get("systolic_value", row.systolic_value),
                    diastolic_value=changes.get("diastolic_value", row.diastolic_value),
                )
            except ValueError:
                return Err(AccountRuleError("VALIDATION_ERROR", row.version))

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
        await dao_measurements.flush(db)

    await dao_measurement_histories.add(
        db,
        PatientMeasurementHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            kind=row.kind,
            measured_at=row.measured_at,
            captured_at_local=row.captured_at_local,
            method=row.method,
            body_site=row.body_site,
            value=row.value,
            systolic_value=row.systolic_value,
            diastolic_value=row.diastolic_value,
            unit=row.unit,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            action=event,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=row.updated_at,
        ),
    )
    state = await measurement_response(db, context, row)
    await project_measurement(db, context.account.id, state)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_measurement",
                    str(row.id),
                    state,
                    state.version,
                    "clinical_measurements",
                )
            ],
            False,
        )
    )


async def read_measurements(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: MeasurementQuery | PageQuery,
    measurement_id: UUID | None = None,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "measurements")

        if isinstance(scope, Err):
            return scope

        patient = await clinical_patient(db, account_id, patient_id)

        if patient is Empty:
            return Err(AccountObjectNotFound())

        if measurement_id is None:
            if not isinstance(query, MeasurementQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            rows, total = await dao_measurements.page(db, account_id, patient_id, query)
            response = PaginatedResponse[PatientMeasurementResponse](
                items=[
                    await measurement_response(db, scope.value, row, patient)
                    for row in rows
                ],
                total=total,
            )
            action = "ReadPatientMeasurements"
        else:
            row = await dao_measurements.scoped(db, account_id, measurement_id)

            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = await measurement_response(db, scope.value, row, patient)
            action = "ReadPatientMeasurement"

        await record_clinical_read(
            db,
            scope.value,
            action,
            "patient_measurement",
            str(measurement_id or patient_id),
        )

    return Ok(response)


async def read_measurement_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    measurement_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "measurements")

        if isinstance(scope, Err):
            return scope

        row = await dao_measurements.scoped(db, account_id, measurement_id)

        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_measurement_histories.page(
            db,
            account_id,
            measurement_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(rows, total, history_response)
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientMeasurementHistory",
            "patient_measurement",
            str(measurement_id),
        )

    return Ok(response)


async def read_measurement_summary(
    db: AsyncSession, credential: str | None, account_id: UUID, patient_id: UUID
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "measurements")

        if isinstance(scope, Err):
            return scope

        patient = await clinical_patient(db, account_id, patient_id)

        if patient is Empty:
            return Err(AccountObjectNotFound())

        rows = await dao_measurements.latest_by_kind(db, account_id, patient_id)
        response = MeasurementSummaryResponse(
            patient_id=patient_id,
            items=[
                await measurement_response(db, scope.value, row, patient)
                for row in rows
            ],
        )
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientMeasurementSummary",
            "patient_measurement",
            str(patient_id),
        )

    return Ok(response)
