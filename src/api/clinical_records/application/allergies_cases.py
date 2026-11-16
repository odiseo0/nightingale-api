from __future__ import annotations

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
from src.api.clinical_records.application.conditions_cases import (
    validate_condition_dates,
)
from src.api.clinical_records.domain.allergies import (
    AllergyQuery,
    CreatePatientAllergyIntolerancePayload,
    InvalidatePatientAllergyIntolerancePayload,
    PatientAllergyIntoleranceHistoryResponse,
    PatientAllergyIntoleranceResponse,
    UpdatePatientAllergyIntolerancePayload,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewHistoryResponse,
    ClinicalSectionReviewResponse,
    SetPatientClinicalSectionReviewPayload,
)
from src.api.clinical_records.repository.allergies import (
    PatientAllergyIntolerance,
    PatientAllergyIntoleranceHistory,
)
from src.api.clinical_records.repository.conditions import (
    PatientClinicalSectionReview,
    PatientClinicalSectionReviewHistory,
)
from src.api.clinical_records.repository.dao import (
    dao_allergies,
    dao_allergy_histories,
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


def allergy_response(
    allergy: PatientAllergyIntolerance,
) -> PatientAllergyIntoleranceResponse:
    return PatientAllergyIntoleranceResponse(
        allergy_id=allergy.id,
        patient_id=allergy.patient_id,
        substance=allergy.substance,
        type=allergy.type,
        reaction_description=allergy.reaction_description,
        clinical_status=allergy.clinical_status,
        verification_status=allergy.verification_status,
        onset_date=allergy.onset_date,
        last_occurrence_date=allergy.last_occurrence_date,
        source_type=allergy.source_type,
        correction_reason=allergy.correction_reason,
        created_at=allergy.created_at,
        updated_at=allergy.updated_at,
        version=allergy.version,
    )


def allergy_history_response(
    row: PatientAllergyIntoleranceHistory,
) -> PatientAllergyIntoleranceHistoryResponse:
    return PatientAllergyIntoleranceHistoryResponse(
        allergy_id=row.id,
        patient_id=row.patient_id,
        substance=row.substance,
        type=row.type,
        reaction_description=row.reaction_description,
        clinical_status=row.clinical_status,
        verification_status=row.verification_status,
        onset_date=row.onset_date,
        last_occurrence_date=row.last_occurrence_date,
        source_type=row.source_type,
        correction_reason=row.correction_reason,
        action=row.action,
        actor_user_id=row.actor_user_id,
        operation_id=row.operation_id,
        changed_at=row.changed_at,
        version=row.version,
    )


async def allergy_review_response(
    db: AsyncSession, context: AccountContext, patient_id: UUID
) -> ClinicalSectionReviewResponse:
    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "allergies"
    )
    active_count = await dao_allergies.active_count(db, context.account.id, patient_id)

    if review is Empty:
        return ClinicalSectionReviewResponse(
            patient_id=patient_id,
            section="allergies",
            information_status="not_recorded",
            source_type=None,
            reviewed_by_user_id=None,
            reviewed_at=None,
            active_count=active_count,
            version=0,
        )

    return ClinicalSectionReviewResponse(
        patient_id=patient_id,
        section="allergies",
        information_status=review.information_status,
        source_type=review.source_type,
        reviewed_by_user_id=review.reviewed_by_user_id,
        reviewed_at=review.reviewed_at,
        active_count=active_count,
        version=review.version,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


async def record_allergy_review_history(
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
            section="allergies",
            version=review.version,
            information_status=review.information_status,
            source_type=review.source_type,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=review.reviewed_at,
        ),
    )


async def derive_allergy_review(
    db: AsyncSession, context: AccountContext, patient_id: UUID, operation_id: UUID
) -> list[AccountChange]:
    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "allergies"
    )
    pertinent = await dao_allergies.has_pertinent(db, context.account.id, patient_id)

    if review is not Empty and review.information_status == (
        "has_entries" if pertinent else "unknown"
    ):
        return []

    now = await clinical_server_time(db)

    if review is Empty:
        review = PatientClinicalSectionReview(
            account_id=context.account.id,
            patient_id=patient_id,
            section="allergies",
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

    await record_allergy_review_history(
        db, context, patient_id, review, "derived", operation_id
    )
    state = await allergy_review_response(db, context, patient_id)

    return [
        AccountChange(
            "patient_clinical_section_review",
            str(patient_id),
            state,
            state.version,
            "clinical_allergies",
        )
    ]


async def record_allergy_history(
    db: AsyncSession,
    context: AccountContext,
    allergy: PatientAllergyIntolerance,
    action: str,
    operation_id: UUID,
) -> None:
    await dao_allergy_histories.add(
        db,
        PatientAllergyIntoleranceHistory(
            account_id=allergy.account_id,
            id=allergy.id,
            patient_id=allergy.patient_id,
            version=allergy.version,
            substance=allergy.substance,
            type=allergy.type,
            reaction_description=allergy.reaction_description,
            clinical_status=allergy.clinical_status,
            verification_status=allergy.verification_status,
            onset_date=allergy.onset_date,
            last_occurrence_date=allergy.last_occurrence_date,
            source_type=allergy.source_type,
            correction_reason=allergy.correction_reason,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=allergy.updated_at,
        ),
    )


async def apply_allergy_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if context.clinical_permissions.allergies != "read_write":
        return Err(AccessDenied())

    if action == "SetPatientClinicalSectionReview":
        return await apply_allergy_review(
            db, context, entity_key, expected_version, payload, operation_id
        )

    if action == "CreatePatientAllergyIntolerance":
        if (
            not isinstance(payload, CreatePatientAllergyIntolerancePayload)
            or expected_version != 0
        ):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        patient_id = payload.patient_id
    else:
        patient_id = entity_key

    if (
        action == "CreatePatientAllergyIntolerance"
        and await lock_clinical_patient(db, context.account.id, patient_id) is Empty
    ):
        return Err(AccountObjectNotFound())

    today = await clinical_today(db, context.account.time_zone)

    if action == "CreatePatientAllergyIntolerance":
        try:
            validate_condition_dates(
                payload.onset_date, payload.last_occurrence_date, today
            )
        except ValueError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        now = await clinical_server_time(db)
        allergy = PatientAllergyIntolerance(
            id=entity_key,
            account_id=context.account.id,
            patient_id=patient_id,
            substance=payload.substance,
            type=payload.type,
            reaction_description=payload.reaction_description,
            clinical_status=payload.clinical_status,
            verification_status=payload.verification_status,
            onset_date=payload.onset_date,
            last_occurrence_date=payload.last_occurrence_date,
            source_type=payload.source_type,
            correction_reason=payload.correction_reason,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_allergies.add(db, allergy)
        await record_allergy_history(db, context, allergy, "created", operation_id)
        state = allergy_response(allergy)
        changes = [
            AccountChange(
                "patient_allergy_intolerance",
                str(allergy.id),
                state,
                1,
                "clinical_allergies",
            )
        ]
        changes.extend(
            await derive_allergy_review(db, context, patient_id, operation_id)
        )

        return Ok(AccountEffect(state, 1, changes, False))

    allergy = await dao_allergies.scoped(db, context.account.id, entity_key)

    if allergy is Empty:
        return Err(AccountObjectNotFound())

    if await lock_clinical_patient(db, context.account.id, allergy.patient_id) is Empty:
        return Err(AccountObjectNotFound())

    if allergy.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", allergy.version))

    if allergy.verification_status == "entered-in-error":
        return Err(AccountRuleError("INVALID_STATE_TRANSITION", allergy.version))

    if action == "InvalidatePatientAllergyIntolerance":
        if not isinstance(payload, InvalidatePatientAllergyIntolerancePayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        changes = {
            "verification_status": "entered-in-error",
            "correction_reason": payload.correction_reason,
        }
        history_action = "invalidated"
    elif action == "UpdatePatientAllergyIntolerance":
        if not isinstance(payload, UpdatePatientAllergyIntolerancePayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        changes = payload.model_dump(exclude_unset=True)
        onset_date = changes.get("onset_date", allergy.onset_date)
        last_occurrence_date = changes.get(
            "last_occurrence_date", allergy.last_occurrence_date
        )

        try:
            validate_condition_dates(onset_date, last_occurrence_date, today)
        except ValueError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if all(getattr(allergy, name) == value for name, value in changes.items()):
            return Err(AccountRuleError("NO_CHANGES", allergy.version))

        history_action = "updated"
    else:
        return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

    now = await clinical_server_time(db)

    allergy.updated_by_user_id = context.actor.user_id
    allergy = await dao_allergies.revise(db, allergy, changes, now)
    await record_allergy_history(db, context, allergy, history_action, operation_id)
    state = allergy_response(allergy)
    changes_list = [
        AccountChange(
            "patient_allergy_intolerance",
            str(allergy.id),
            state,
            state.version,
            "clinical_allergies",
        )
    ]
    changes_list.extend(
        await derive_allergy_review(db, context, allergy.patient_id, operation_id)
    )

    return Ok(AccountEffect(state, state.version, changes_list, False))


async def apply_allergy_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if (
        not isinstance(payload, SetPatientClinicalSectionReviewPayload)
        or payload.section != "allergies"
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if await lock_clinical_patient(db, context.account.id, patient_id) is Empty:
        return Err(AccountObjectNotFound())

    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, "allergies"
    )
    current_version = 0 if review is Empty else review.version

    if current_version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", current_version))

    pertinent = await dao_allergies.has_pertinent(db, context.account.id, patient_id)

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
            section="allergies",
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

    await record_allergy_review_history(
        db, context, patient_id, review, "set", operation_id
    )
    state = await allergy_review_response(db, context, patient_id)

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
                    "clinical_allergies",
                )
            ],
            False,
        )
    )


async def allergy_read_scope(
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
        or scope.value.clinical_permissions.allergies == "none"
    ):
        return Err(AccessDenied())

    return scope


async def read_allergies(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: AllergyQuery | PageQuery,
    allergy_id: UUID | None = None,
):
    async with transaction(db):
        scope = await allergy_read_scope(db, credential, account_id)

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if allergy_id is None:
            rows, total = await dao_allergies.page(db, account_id, patient_id, query)
            response = PaginatedResponse[PatientAllergyIntoleranceResponse](
                items=[allergy_response(row) for row in rows], total=total
            )
        else:
            allergy = await dao_allergies.scoped(db, account_id, allergy_id)

            if allergy is Empty or allergy.patient_id != patient_id:
                return Err(AccountObjectNotFound())

            response = allergy_response(allergy)

        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadPatientAllergies",
                object_type="patient_allergy_intolerance",
                object_key=str(allergy_id or patient_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)


async def read_allergy_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    allergy_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await allergy_read_scope(db, credential, account_id)

        if isinstance(scope, Err):
            return scope

        allergy = await dao_allergies.scoped(db, account_id, allergy_id)

        if allergy is Empty or allergy.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await dao_allergy_histories.page(
            db,
            account_id,
            allergy_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = PaginatedResponse[PatientAllergyIntoleranceHistoryResponse](
            items=[allergy_history_response(row) for row in rows], total=total
        )
        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadPatientAllergyHistory",
                object_type="patient_allergy_intolerance",
                object_key=str(allergy_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)


async def read_allergy_review(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: PageQuery | ClinicalHistoryQuery,
    history: bool = False,
):
    async with transaction(db):
        scope = await allergy_read_scope(db, credential, account_id)

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
                "allergies",
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
            response = await allergy_review_response(db, scope.value, patient_id)

        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=scope.value.actor.user_id,
                actor_device_id=scope.value.actor.device_id,
                action="ReadAllergySectionReview",
                object_type="patient_clinical_section_review",
                object_key=str(patient_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=await clinical_server_time(db),
            ),
        )

    return Ok(response)
