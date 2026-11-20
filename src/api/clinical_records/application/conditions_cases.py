from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.domain.errors import AccessDenied
from src.api.clinical_records.application.entries_cases import (
    EntryAdapter,
    apply_entry_write,
    current_section_review,
    derive_section_review,
    read_entry,
    read_entry_history,
)
from src.api.clinical_records.application.entries_cases import (
    apply_section_review as apply_entry_review,
)
from src.api.clinical_records.application.entries_cases import (
    read_section_review as read_entry_review,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewResponse,
    ConditionQuery,
    CreatePatientConditionPayload,
    InvalidatePatientConditionPayload,
    PatientConditionHistoryResponse,
    PatientConditionResponse,
    SetPatientClinicalSectionReviewPayload,
    UpdatePatientConditionPayload,
)
from src.api.clinical_records.repository.conditions import (
    PatientCondition,
    PatientConditionHistory,
)
from src.api.clinical_records.repository.dao import (
    dao_condition_histories,
    dao_conditions,
)
from src.api.patients.application.patients_cases import clinical_today
from src.core import Err, Result
from src.core.schema import PageQuery
from src.core.utils.utils import EmptyType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def condition_response(condition: PatientCondition) -> PatientConditionResponse:
    return PatientConditionResponse(
        condition_id=condition.id,
        patient_id=condition.patient_id,
        name=condition.name,
        clinical_status=condition.clinical_status,
        verification_status=condition.verification_status,
        onset_date=condition.onset_date,
        abatement_date=condition.abatement_date,
        source_type=condition.source_type,
        correction_reason=condition.correction_reason,
        created_at=condition.date_added,
        updated_at=condition.date_updated,
        version=condition.version,
    )


def condition_history_response(
    row: PatientConditionHistory,
) -> PatientConditionHistoryResponse:
    return PatientConditionHistoryResponse(
        condition_id=row.id,
        patient_id=row.patient_id,
        name=row.name,
        clinical_status=row.clinical_status,
        verification_status=row.verification_status,
        onset_date=row.onset_date,
        abatement_date=row.abatement_date,
        source_type=row.source_type,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


def validate_condition_dates(
    onset: str | None, abatement: str | None, today: date
) -> None:
    def parts(value: str) -> tuple[int, int, int]:
        return tuple(int(part) for part in value.split("-"))

    if onset is not None and parts(onset) > (today.year, today.month, today.day):
        raise ValueError("El inicio no puede ser futuro")

    if onset is None or abatement is None:
        return

    start = parts(onset)
    end = parts(abatement)
    end_latest = (
        end[0],
        end[1] if len(end) > 1 else 12,
        end[2]
        if len(end) > 2
        else calendar.monthrange(end[0], end[1] if len(end) > 1 else 12)[1],
    )

    if end_latest < start:
        raise ValueError("El fin es inequívocamente anterior al inicio")


async def condition_review_response(
    db: AsyncSession, context: AccountContext, patient_id: UUID
) -> ClinicalSectionReviewResponse:
    return await current_section_review(
        db,
        context,
        patient_id,
        "conditions",
        await dao_conditions.active_count(db, context.account.id, patient_id),
    )


async def derive_condition_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    operation_id: UUID,
    was_pertinent: bool,
) -> list[AccountChange]:
    return await derive_section_review(
        db,
        context,
        patient_id,
        "conditions",
        operation_id,
        was_pertinent,
        await dao_conditions.has_pertinent(db, context.account.id, patient_id),
    )


async def record_condition_history(
    db: AsyncSession,
    context: AccountContext,
    condition: PatientCondition,
    action: str,
    operation_id: UUID,
) -> None:
    await dao_condition_histories.add(
        db,
        PatientConditionHistory(
            account_id=condition.account_id,
            id=condition.id,
            patient_id=condition.patient_id,
            version=condition.version,
            name=condition.name,
            clinical_status=condition.clinical_status,
            verification_status=condition.verification_status,
            onset_date=condition.onset_date,
            abatement_date=condition.abatement_date,
            source_type=condition.source_type,
            correction_reason=condition.correction_reason,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=condition.date_updated,
        ),
    )


async def apply_condition_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.conditions != "read_write":
        return Err(AccessDenied())

    if action == "SetPatientClinicalSectionReview":
        return await apply_section_review(
            db, context, entity_key, expected_version, payload, operation_id
        )

    kind = {
        "CreatePatientCondition": "create",
        "UpdatePatientCondition": "update",
        "InvalidatePatientCondition": "invalidate",
    }.get(action)
    expected = {
        "create": CreatePatientConditionPayload,
        "update": UpdatePatientConditionPayload,
        "invalidate": InvalidatePatientConditionPayload,
    }

    if kind is None or not isinstance(payload, expected[kind]):
        return Err(
            AccountRuleError(
                "UNSUPPORTED_OPERATION" if kind is None else "VALIDATION_ERROR"
            )
        )

    today = await clinical_today(db, context.account.time_zone)

    def valid(
        data: CreatePatientConditionPayload
        | UpdatePatientConditionPayload
        | InvalidatePatientConditionPayload,
        entry: PatientCondition | EmptyType,
    ) -> bool:
        if isinstance(data, InvalidatePatientConditionPayload):
            return True

        values = data.model_dump(exclude_unset=True) if kind == "update" else {}

        try:
            validate_condition_dates(
                values.get("onset_date", getattr(entry, "onset_date", data.onset_date)),
                values.get(
                    "abatement_date",
                    getattr(entry, "abatement_date", data.abatement_date),
                ),
                today,
            )
        except ValueError:
            return False

        return True

    async def create(
        ctx: AccountContext,
        key: UUID,
        data: CreatePatientConditionPayload,
        now: datetime,
    ) -> PatientCondition:
        condition = PatientCondition(
            id=key,
            account_id=ctx.account.id,
            patient_id=data.patient_id,
            name=data.name,
            clinical_status=data.clinical_status,
            verification_status=data.verification_status,
            onset_date=data.onset_date,
            abatement_date=data.abatement_date,
            source_type=data.source_type,
            correction_reason=data.correction_reason,
            created_by_user_id=ctx.actor.user_id,
            updated_by_user_id=ctx.actor.user_id,
            date_added=now,
            date_updated=now,
            version=1,
        )
        await dao_conditions.add(db, condition)

        return condition

    return await apply_entry_write(
        db,
        context,
        "conditions",
        kind,
        entity_key,
        expected_version,
        payload,
        operation_id,
        EntryAdapter(
            read=lambda key: dao_conditions.get_by(db, where={"account_id": context.account.id, "id": key}, execution_options={"populate_existing": True}),
            create=create,
            revise=lambda entry, changes, now: dao_conditions.revise(
                db, entry, changes, now
            ),
            response=condition_response,
            history=lambda ctx, entry, event, op: record_condition_history(
                db, ctx, entry, event, op
            ),
            valid=valid,
            has_pertinent=lambda patient_id: dao_conditions.has_pertinent(
                db, context.account.id, patient_id
            ),
        ),
    )


async def apply_section_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if not isinstance(payload, SetPatientClinicalSectionReviewPayload):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    return await apply_entry_review(
        db,
        context,
        patient_id,
        "conditions",
        expected_version,
        payload,
        operation_id,
        lambda: dao_conditions.has_pertinent(db, context.account.id, patient_id),
        lambda: dao_conditions.active_count(db, context.account.id, patient_id),
    )


async def read_conditions(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: ConditionQuery | PageQuery,
    condition_id: UUID | None = None,
):
    return await read_entry(
        db,
        credential,
        account_id,
        patient_id,
        "conditions",
        condition_id,
        query,
        lambda key: dao_conditions.get_by(db, where={"account_id": account_id, "id": key}, execution_options={"populate_existing": True}),
        lambda filters: dao_conditions.page(db, account_id, patient_id, filters),
        condition_response,
        "ReadPatientConditions",
        "patient_condition",
    )


async def read_condition_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    condition_id: UUID,
    query: ClinicalHistoryQuery,
):
    return await read_entry_history(
        db,
        credential,
        account_id,
        patient_id,
        "conditions",
        condition_id,
        query,
        lambda key: dao_conditions.get_by(db, where={"account_id": account_id, "id": key}, execution_options={"populate_existing": True}),
        lambda offset, shows, after: dao_condition_histories.get_multi(
            db, where={"account_id": account_id, "id": condition_id},
            page=offset, shows=shows, ordering=[("version", False)], after_version=after,
        ),
        condition_history_response,
        "ReadPatientConditionHistory",
        "patient_condition",
    )


async def read_section_review(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: PageQuery | ClinicalHistoryQuery,
    history: bool = False,
):
    return await read_entry_review(
        db,
        credential,
        account_id,
        patient_id,
        "conditions",
        query,
        history,
        "ReadClinicalSectionReview",
        lambda: dao_conditions.active_count(db, account_id, patient_id),
    )
