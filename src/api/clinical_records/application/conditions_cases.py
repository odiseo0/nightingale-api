from __future__ import annotations

import calendar
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewHistoryResponse,
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
    PatientClinicalSectionReview,
    PatientClinicalSectionReviewHistory,
    PatientCondition,
    PatientConditionHistory,
)
from src.api.clinical_records.repository.dao import (
    dao_condition_histories,
    dao_conditions,
    dao_section_review_histories,
    dao_section_reviews,
)
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    clinical_today,
    lock_clinical_patient,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

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
        created_at=condition.created_at,
        updated_at=condition.updated_at,
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
    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "conditions"
    )
    active_count = await dao_conditions.active_count(db, context.account.id, patient_id)

    if review is Empty:
        return ClinicalSectionReviewResponse(
            patient_id=patient_id,
            section="conditions",
            information_status="not_recorded",
            source_type=None,
            reviewed_by_user_id=None,
            reviewed_at=None,
            active_count=active_count,
            version=0,
        )

    return ClinicalSectionReviewResponse(
        patient_id=patient_id,
        section="conditions",
        information_status=review.information_status,
        source_type=review.source_type,
        reviewed_by_user_id=review.reviewed_by_user_id,
        reviewed_at=review.reviewed_at,
        active_count=active_count,
        version=review.version,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


async def record_review_history(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    review: PatientClinicalSectionReview,
    action: str,
    operation_id: UUID,
) -> None:
    await dao_section_review_histories.add(
        db,
        PatientClinicalSectionReviewHistory(
            account_id=context.account.id,
            patient_id=patient_id,
            section="conditions",
            version=review.version,
            information_status=review.information_status,
            source_type=review.source_type,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=review.reviewed_at,
        ),
    )


async def derive_condition_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    operation_id: UUID,
) -> list[AccountChange]:
    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "conditions"
    )
    pertinent = await dao_conditions.has_pertinent(db, context.account.id, patient_id)

    if review is not Empty and review.information_status == (
        "has_entries" if pertinent else "unknown"
    ):
        return []

    now = await clinical_server_time(db)

    if review is Empty:
        review = PatientClinicalSectionReview(
            account_id=context.account.id,
            patient_id=patient_id,
            section="conditions",
            information_status="has_entries" if pertinent else "unknown",
            source_type="unknown",
            reviewed_by_user_id=context.actor.user_id,
            reviewed_at=now,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_section_reviews.add(db, review)
    else:
        review.information_status = "has_entries" if pertinent else "unknown"
        review.source_type = "unknown"
        review.reviewed_by_user_id = context.actor.user_id
        review.reviewed_at = now
        review.updated_at = now
        review.version += 1
        await dao_section_reviews.flush(db)

    await record_review_history(
        db, context, patient_id, review, "derived", operation_id
    )
    state = await condition_review_response(db, context, patient_id)

    return [
        AccountChange(
            "patient_clinical_section_review",
            str(patient_id),
            state,
            state.version,
            "clinical_conditions",
        )
    ]


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
            changed_at=condition.updated_at,
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

    if action == "CreatePatientCondition":
        if (
            not isinstance(payload, CreatePatientConditionPayload)
            or expected_version != 0
        ):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        patient_id = payload.patient_id
    else:
        patient_id = entity_key

    if (
        action == "CreatePatientCondition"
        and await lock_clinical_patient(db, context.account.id, patient_id) is Empty
    ):
        return Err(AccountObjectNotFound())

    today = await clinical_today(db, context.account.time_zone)

    if action == "CreatePatientCondition":
        try:
            validate_condition_dates(payload.onset_date, payload.abatement_date, today)
        except ValueError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        now = await clinical_server_time(db)
        condition = PatientCondition(
            id=entity_key,
            account_id=context.account.id,
            patient_id=patient_id,
            name=payload.name,
            clinical_status=payload.clinical_status,
            verification_status=payload.verification_status,
            onset_date=payload.onset_date,
            abatement_date=payload.abatement_date,
            source_type=payload.source_type,
            correction_reason=payload.correction_reason,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_conditions.add(db, condition)
        await record_condition_history(db, context, condition, "created", operation_id)
        state = condition_response(condition)
        changes = [
            AccountChange(
                "patient_condition", str(condition.id), state, 1, "clinical_conditions"
            )
        ]
        changes.extend(
            await derive_condition_review(db, context, patient_id, operation_id)
        )

        return Ok(AccountEffect(state, 1, changes, False))

    condition = await dao_conditions.scoped(db, context.account.id, entity_key)

    if condition is Empty:
        return Err(AccountObjectNotFound())

    if (
        await lock_clinical_patient(db, context.account.id, condition.patient_id)
        is Empty
    ):
        return Err(AccountObjectNotFound())

    if condition.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", condition.version))

    if condition.verification_status == "entered-in-error":
        return Err(AccountRuleError("INVALID_STATE_TRANSITION", condition.version))

    if action == "InvalidatePatientCondition":
        if not isinstance(payload, InvalidatePatientConditionPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        changes = {
            "verification_status": "entered-in-error",
            "correction_reason": payload.correction_reason,
        }
        history_action = "invalidated"
    elif action == "UpdatePatientCondition":
        if not isinstance(payload, UpdatePatientConditionPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        changes = payload.model_dump(exclude_unset=True)
        onset_date = changes.get("onset_date", condition.onset_date)
        abatement_date = changes.get("abatement_date", condition.abatement_date)

        try:
            validate_condition_dates(onset_date, abatement_date, today)
        except ValueError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if all(getattr(condition, name) == value for name, value in changes.items()):
            return Err(AccountRuleError("NO_CHANGES", condition.version))

        history_action = "updated"
    else:
        return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

    now = await clinical_server_time(db)

    condition.updated_by_user_id = context.actor.user_id
    condition = await dao_conditions.revise(db, condition, changes, now)
    await record_condition_history(db, context, condition, history_action, operation_id)
    state = condition_response(condition)
    changes_list = [
        AccountChange(
            "patient_condition",
            str(condition.id),
            state,
            state.version,
            "clinical_conditions",
        )
    ]
    changes_list.extend(
        await derive_condition_review(db, context, condition.patient_id, operation_id)
    )

    return Ok(AccountEffect(state, state.version, changes_list, False))


async def apply_section_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if (
        not isinstance(payload, SetPatientClinicalSectionReviewPayload)
        or payload.section != "conditions"
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))
    if await lock_clinical_patient(db, context.account.id, patient_id) is Empty:
        return Err(AccountObjectNotFound())

    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "conditions"
    )
    current_version = 0 if review is Empty else review.version
    if current_version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", current_version))

    pertinent = await dao_conditions.has_pertinent(db, context.account.id, patient_id)
    if (payload.information_status == "has_entries") != pertinent:
        return Err(AccountRuleError("INVALID_STATE_TRANSITION", current_version))
    if (
        review is not Empty
        and review.information_status == payload.information_status
        and review.source_type == payload.source_type
    ):
        return Err(AccountRuleError("NO_CHANGES", current_version))

    now = await clinical_server_time(db)
    if review is Empty:
        review = PatientClinicalSectionReview(
            account_id=context.account.id,
            patient_id=patient_id,
            section="conditions",
            information_status=payload.information_status,
            source_type=payload.source_type,
            reviewed_by_user_id=context.actor.user_id,
            reviewed_at=now,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_section_reviews.add(db, review)
    else:
        review.information_status = payload.information_status
        review.source_type = payload.source_type
        review.reviewed_by_user_id = context.actor.user_id
        review.reviewed_at = now
        review.updated_at = now
        review.version += 1
        await dao_section_reviews.flush(db)

    await record_review_history(db, context, patient_id, review, "set", operation_id)
    state = await condition_review_response(db, context, patient_id)
    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_clinical_section_review",
                    str(patient_id),
                    state,
                    state.version,
                    "clinical_conditions",
                )
            ],
            False,
        )
    )


async def condition_read_scope(
    db: AsyncSession, credential: str | None, account_id: UUID
):
    identity = await authenticate(db, credential)
    if isinstance(identity, Err):
        return identity
    scope = await account_context(db, identity.value, account_id, require_device=True)
    if isinstance(scope, Err):
        return scope
    if (
        scope.value.account.status != "active"
        or scope.value.clinical_permissions.conditions == "none"
    ):
        return Err(AccessDenied())
    return scope


async def read_conditions(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: ConditionQuery | PageQuery,
    condition_id: UUID | None = None,
):
    async with transaction(db):
        scope = await condition_read_scope(db, credential, account_id)
        if isinstance(scope, Err):
            return scope
        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if condition_id is None:
            rows, total = await dao_conditions.page(db, account_id, patient_id, query)
            response = PaginatedResponse[PatientConditionResponse](
                items=[condition_response(row) for row in rows], total=total
            )
        else:
            condition = await dao_conditions.scoped(db, account_id, condition_id)
            if condition is Empty or condition.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            response = condition_response(condition)

        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadPatientConditions",
                object_type="patient_condition",
                object_key=str(condition_id or patient_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)


async def read_condition_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    condition_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await condition_read_scope(db, credential, account_id)
        if isinstance(scope, Err):
            return scope
        condition = await dao_conditions.scoped(db, account_id, condition_id)
        if condition is Empty or condition.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_condition_histories.page(
            db,
            account_id,
            condition_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = PaginatedResponse[PatientConditionHistoryResponse](
            items=[condition_history_response(row) for row in rows], total=total
        )
        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadPatientConditionHistory",
                object_type="patient_condition",
                object_key=str(condition_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)


async def read_section_review(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: PageQuery | ClinicalHistoryQuery,
    history: bool = False,
):
    async with transaction(db):
        scope = await condition_read_scope(db, credential, account_id)
        if isinstance(scope, Err):
            return scope
        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if history:
            after_version = (
                query.after_version if isinstance(query, ClinicalHistoryQuery) else None
            )
            rows, total = await dao_section_review_histories.page(
                db,
                account_id,
                patient_id,
                "conditions",
                (query.page - 1) * query.shows,
                query.shows,
                after_version,
            )
            response = PaginatedResponse[ClinicalSectionReviewHistoryResponse](
                items=[
                    ClinicalSectionReviewHistoryResponse.model_validate(row)
                    for row in rows
                ],
                total=total,
            )
        else:
            response = await condition_review_response(db, scope.value, patient_id)

        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadClinicalSectionReview",
                object_type="patient_clinical_section_review",
                object_key=str(patient_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)
