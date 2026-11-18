from typing import TYPE_CHECKING
from uuid import UUID, uuid7

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
from src.api.specialties.domain.records import (
    CaptureSpecialtyRecordPayload,
    InvalidateSpecialtyRecordPayload,
    SpecialtyRecordHistoryResponse,
    SpecialtyRecordResponse,
    SpecialtyRecordValue,
    SpecialtyRecordValueResponse,
    UpdateSpecialtyRecordPayload,
)
from src.api.specialties.domain.templates import (
    CreateSpecialtyTemplatePayload,
    RetireSpecialtyTemplatePayload,
    SpecialtyTemplateFieldResponse,
    SpecialtyTemplateHistoryResponse,
    SpecialtyTemplateQuery,
    SpecialtyTemplateResponse,
    UpdateSpecialtyTemplatePayload,
)
from src.api.specialties.repository.dao import (
    dao_specialty_record_histories,
    dao_specialty_record_values,
    dao_specialty_records,
    dao_template_fields,
    dao_template_histories,
    dao_templates,
)
from src.api.specialties.repository.models import (
    SpecialtyRecord,
    SpecialtyRecordHistory,
    SpecialtyRecordValueRow,
    SpecialtyTemplate,
    SpecialtyTemplateFieldRow,
    SpecialtyTemplateHistory,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

TEMPLATE_ACTIONS = ("CreateSpecialtyTemplate", "UpdateSpecialtyTemplate", "RetireSpecialtyTemplate")
RECORD_ACTIONS = ("CaptureSpecialtyRecord", "UpdateSpecialtyRecord", "InvalidateSpecialtyRecord")


def _field_rows(
    account_id: UUID, template_id: UUID, version: int, fields
) -> list[SpecialtyTemplateFieldRow]:
    return [
        SpecialtyTemplateFieldRow(
            id=uuid7(),
            account_id=account_id,
            template_id=template_id,
            template_version=version,
            field_key=field.field_key,
            label=field.label,
            field_kind=field.field_kind,
            required=field.required,
            options=field.options,
            display_order=field.display_order,
        )
        for field in fields
    ]


async def template_response(
    db: AsyncSession, row: SpecialtyTemplate
) -> SpecialtyTemplateResponse:
    fields = await dao_template_fields.for_version(
        db, row.account_id, row.id, row.version
    )

    return SpecialtyTemplateResponse(
        template_id=row.id,
        name=row.name,
        specialty=row.specialty,
        template_status=row.template_status,
        change_note=row.change_note,
        version=row.version,
        fields=[
            SpecialtyTemplateFieldResponse(
                field_key=field.field_key,
                label=field.label,
                field_kind=field.field_kind,
                required=field.required,
                options=field.options,
                display_order=field.display_order,
            )
            for field in fields
        ],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def record_response(
    db: AsyncSession, row: SpecialtyRecord
) -> SpecialtyRecordResponse:
    values = await dao_specialty_record_values.for_record_version(
        db, row.account_id, row.id, row.version
    )

    return SpecialtyRecordResponse(
        record_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        template_id=row.template_id,
        template_version=row.template_version,
        recorded_at=row.recorded_at,
        values=[
            SpecialtyRecordValueResponse(
                field_key=value.field_key,
                value_text=value.value_text,
                value_number=value.value_number,
                value_boolean=value.value_boolean,
                value_date=value.value_date,
            )
            for value in values
        ],
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def _value_rows(account_id, patient_id, record_id, version, values) -> list[SpecialtyRecordValueRow]:
    return [
        SpecialtyRecordValueRow(
            id=uuid7(),
            account_id=account_id,
            patient_id=patient_id,
            record_id=record_id,
            record_version=version,
            field_key=value.field_key,
            value_text=value.value_text,
            value_number=value.value_number,
            value_boolean=value.value_boolean,
            value_date=value.value_date,
        )
        for value in values
    ]


async def apply_specialty_operation(
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

    if action in TEMPLATE_ACTIONS:
        return await _apply_template(db, context, action, entity_key, expected_version, payload, operation_id)

    if action in RECORD_ACTIONS:
        return await _apply_record(db, context, action, entity_key, expected_version, payload, operation_id)

    return Err(AccountRuleError("UNSUPPORTED_OPERATION"))


async def _apply_template(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "CreateSpecialtyTemplate":
        if not isinstance(payload, CreateSpecialtyTemplatePayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_templates.scoped(db, context.account.id, entity_key) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))

        now = await clinical_server_time(db)
        row = SpecialtyTemplate(
            id=entity_key,
            account_id=context.account.id,
            name=payload.name,
            specialty=payload.specialty,
            template_status="active",
            change_note=payload.change_note,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_templates.add(db, row)
        await dao_template_fields.replace_for_version(
            db, context.account.id, row.id, 1, _field_rows(context.account.id, row.id, 1, payload.fields)
        )
        event = "created"
    else:
        row = await dao_templates.scoped(db, context.account.id, entity_key, lock=True)
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if action == "RetireSpecialtyTemplate":
            if not isinstance(payload, RetireSpecialtyTemplatePayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            if row.template_status == "retired":
                return Err(AccountRuleError("NO_CHANGES", row.version))
            row.template_status = "retired"
            event = "updated"
        elif action == "UpdateSpecialtyTemplate":
            if not isinstance(payload, UpdateSpecialtyTemplatePayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            if not payload.model_fields_set:
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.version += 1
            if "name" in payload.model_fields_set:
                row.name = payload.name
            if "change_note" in payload.model_fields_set:
                row.change_note = payload.change_note
            await dao_template_fields.replace_for_version(
                db, context.account.id, row.id, row.version,
                _field_rows(context.account.id, row.id, row.version, payload.fields),
            )
            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.updated_at = await clinical_server_time(db)
        await dao_templates.flush(db)

    state = await template_response(db, row)
    await dao_template_histories.add(
        db,
        SpecialtyTemplateHistory(
            account_id=row.account_id,
            id=row.id,
            name=row.name,
            specialty=row.specialty,
            template_status=row.template_status,
            change_note=row.change_note,
            version=row.version,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
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
            [AccountChange("specialty_template", str(row.id), state, state.version, "clinical_specialty_templates")],
            False,
        )
    )


async def _apply_record(db, context, action, entity_key, expected_version, payload, operation_id):
    if action == "CaptureSpecialtyRecord":
        if not isinstance(payload, CaptureSpecialtyRecordPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if await dao_specialty_records.scoped(db, context.account.id, entity_key) is not Empty:
            return Err(AccountRuleError("VERSION_CONFLICT", 1))
        if await lock_clinical_patient(db, context.account.id, payload.patient_id) is Empty:
            return Err(AccountObjectNotFound())
        if payload.encounter_id is not None and not await valid_encounter_for_record(
            db, context.account.id, payload.patient_id, payload.encounter_id
        ):
            return Err(AccountObjectNotFound())

        template = await dao_templates.scoped(db, context.account.id, payload.template_id)
        if template is Empty or template.template_status != "active":
            return Err(AccountObjectNotFound())

        invalid = await _unknown_fields(db, context, payload.template_id, template.version, payload.values)
        if invalid is not None:
            return invalid
        if len({value.field_key for value in payload.values}) != len(payload.values):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        missing_required = await _missing_required(db, context, payload.template_id, template.version, payload.values)
        if missing_required is not None:
            return missing_required

        now = await clinical_server_time(db)
        row = SpecialtyRecord(
            id=entity_key,
            account_id=context.account.id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            template_id=payload.template_id,
            template_version=template.version,
            recorded_at=payload.recorded_at or now,
            record_status="valid",
            correction_reason=None,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_specialty_records.add(db, row)
        await dao_specialty_record_values.replace_for_version(
            db, context.account.id, row.id, 1, _value_rows(context.account.id, payload.patient_id, row.id, 1, payload.values)
        )
        event = "created"
    else:
        row = await dao_specialty_records.scoped(db, context.account.id, entity_key, lock=True)
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
        if row.record_status != "valid":
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "InvalidateSpecialtyRecord":
            if not isinstance(payload, InvalidateSpecialtyRecordPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            row.record_status = "entered-in-error"
            row.correction_reason = payload.correction_reason
            event = "invalidated"
        elif action == "UpdateSpecialtyRecord":
            if not isinstance(payload, UpdateSpecialtyRecordPayload):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            values = payload.values if payload.values is not None else []
            invalid = await _unknown_fields(db, context, row.template_id, row.template_version, values)
            if invalid is not None:
                return invalid
            missing_required = await _missing_required(
                db, context, row.template_id, row.template_version, values
            )
            if missing_required is not None:
                return missing_required
            now = await clinical_server_time(db)
            row.version += 1
            if payload.recorded_at is not None:
                row.recorded_at = payload.recorded_at
            await dao_specialty_record_values.replace_for_version(
                db, context.account.id, row.id, row.version,
                _value_rows(context.account.id, row.patient_id, row.id, row.version, values),
            )
            event = "updated"
        else:
            return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

        row.updated_by_user_id = context.actor.user_id
        row.updated_at = await clinical_server_time(db)
        await dao_specialty_records.flush(db)

    state = await record_response(db, row)
    await dao_specialty_record_histories.add(
        db,
        SpecialtyRecordHistory(
            account_id=row.account_id,
            id=row.id,
            patient_id=row.patient_id,
            encounter_id=row.encounter_id,
            template_id=row.template_id,
            template_version=row.template_version,
            recorded_at=row.recorded_at,
            record_status=row.record_status,
            correction_reason=row.correction_reason,
            version=row.version,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
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
            [AccountChange("specialty_record", str(row.id), state, state.version, "clinical_specialty_templates")],
            False,
        )
    )


async def _unknown_fields(db, context, template_id, template_version, values) -> Result | None:
    fields = await dao_template_fields.for_version(db, context.account.id, template_id, template_version)
    known = {field.field_key for field in fields}
    if any(value.field_key not in known for value in values):
        return Err(AccountRuleError("VALIDATION_ERROR"))
    return None


async def _missing_required(db, context, template_id, template_version, values) -> Result | None:
    fields = await dao_template_fields.for_version(db, context.account.id, template_id, template_version)
    provided = {value.field_key for value in values}
    if any(field.required and field.field_key not in provided for field in fields):
        return Err(AccountRuleError("VALIDATION_ERROR"))
    return None


async def read_templates(db, credential, account_id, query: SpecialtyTemplateQuery | PageQuery, template_id=None):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        if template_id is None:
            if not isinstance(query, SpecialtyTemplateQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            rows, total = await dao_templates.page(db, account_id, query)
            items = [await template_response(db, row) for row in rows]
            response = clinical_page(items, total, lambda state: state)
            action = "ReadSpecialtyTemplates"
        else:
            row = await dao_templates.scoped(db, account_id, template_id)
            if row is Empty:
                return Err(AccountObjectNotFound())
            response = await template_response(db, row)
            action = "ReadSpecialtyTemplate"

        await record_clinical_read(db, scope.value, action, "specialty_template", str(template_id or account_id))

    return Ok(response)


async def read_template_history(db, credential, account_id, template_id, query: ClinicalHistoryQuery):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        row = await dao_templates.scoped(db, account_id, template_id)
        if row is Empty:
            return Err(AccountObjectNotFound())

        rows, total = await dao_template_histories.page(
            db, account_id, template_id, (query.page - 1) * query.shows, query.shows, query.after_version
        )

        states = []
        for history_row in rows:
            fields = await dao_template_fields.for_version(db, account_id, template_id, history_row.version)
            states.append(
                SpecialtyTemplateHistoryResponse(
                    template_id=history_row.id,
                    name=history_row.name,
                    specialty=history_row.specialty,
                    template_status=history_row.template_status,
                    change_note=history_row.change_note,
                    version=history_row.version,
                    fields=[
                        SpecialtyTemplateFieldResponse(
                            field_key=field.field_key,
                            label=field.label,
                            field_kind=field.field_kind,
                            required=field.required,
                            options=field.options,
                            display_order=field.display_order,
                        )
                        for field in fields
                    ],
                    created_at=history_row.created_at,
                    updated_at=history_row.updated_at,
                    action=history_row.action,
                    actor_user_id=history_row.actor_user_id,
                    operation_id=history_row.operation_id,
                    changed_at=history_row.changed_at,
                )
            )
        response = clinical_page(states, total, lambda state: state)
        await record_clinical_read(db, scope.value, "ReadSpecialtyTemplateHistory", "specialty_template", str(template_id))

    return Ok(response)


async def read_specialty_records(
    db, credential, account_id, patient_id, query: PageQuery, record_id=None
):
    from src.api.specialties.domain.records import SpecialtyRecordQuery

    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if record_id is None:
            if not isinstance(query, SpecialtyRecordQuery):
                return Err(AccountRuleError("VALIDATION_ERROR"))
            rows, total = await dao_specialty_records.page(db, account_id, patient_id, query)
            items = [await record_response(db, row) for row in rows]
            response = clinical_page(items, total, lambda state: state)
            action = "ReadSpecialtyRecords"
        else:
            row = await dao_specialty_records.scoped(db, account_id, record_id)
            if row is Empty or row.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            response = await record_response(db, row)
            action = "ReadSpecialtyRecord"

        await record_clinical_read(db, scope.value, action, "specialty_record", str(record_id or patient_id))

    return Ok(response)


async def read_specialty_record_history(db, credential, account_id, patient_id, record_id, query: ClinicalHistoryQuery):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "specialty_templates")
        if isinstance(scope, Err):
            return scope

        row = await dao_specialty_records.scoped(db, account_id, record_id)
        if row is Empty or row.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_specialty_record_histories.page(
            db, account_id, record_id, (query.page - 1) * query.shows, query.shows, query.after_version
        )
        response = clinical_page(rows, total, _record_history_view)
        await record_clinical_read(db, scope.value, "ReadSpecialtyRecordHistory", "specialty_record", str(record_id))

    return Ok(response)


def _record_history_view(row: SpecialtyRecordHistory) -> SpecialtyRecordHistoryResponse:
    return SpecialtyRecordHistoryResponse(
        record_id=row.id,
        patient_id=row.patient_id,
        encounter_id=row.encounter_id,
        template_id=row.template_id,
        template_version=row.template_version,
        recorded_at=row.recorded_at,
        values=[],
        record_status=row.record_status,
        correction_reason=row.correction_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
    )
