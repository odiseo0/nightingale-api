from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.clinical_records.application.access_cases import (
    clinical_page,
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.domain.allergies import (
    CreatePatientAllergyIntolerancePayload,
    InvalidatePatientAllergyIntolerancePayload,
    PatientAllergyIntoleranceResponse,
    UpdatePatientAllergyIntolerancePayload,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewHistoryResponse,
    ClinicalSectionReviewResponse,
    CreatePatientConditionPayload,
    InvalidatePatientConditionPayload,
    PatientConditionResponse,
    SetPatientClinicalSectionReviewPayload,
    UpdatePatientConditionPayload,
)
from src.api.clinical_records.repository.allergies import PatientAllergyIntolerance
from src.api.clinical_records.repository.conditions import (
    PatientClinicalSectionReview,
    PatientClinicalSectionReviewHistory,
    PatientCondition,
)
from src.api.clinical_records.repository.dao import (
    dao_allergies,
    dao_conditions,
    dao_section_review_histories,
    dao_section_reviews,
)
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    lock_clinical_patient,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel, PageQuery
from src.core.utils.utils import Empty, EmptyType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

type EntrySection = Literal["conditions", "allergies"]
type ClinicalEntry = PatientCondition | PatientAllergyIntolerance
type CreateEntryPayload = (
    CreatePatientConditionPayload | CreatePatientAllergyIntolerancePayload
)
type EntryPayload = (
    CreateEntryPayload
    | UpdatePatientConditionPayload
    | UpdatePatientAllergyIntolerancePayload
    | InvalidatePatientConditionPayload
    | InvalidatePatientAllergyIntolerancePayload
)
type EntryResponse = PatientConditionResponse | PatientAllergyIntoleranceResponse


@dataclass(frozen=True)
class EntryAdapter:
    scoped: Callable[[UUID], Awaitable[ClinicalEntry | EmptyType]]
    create: Callable[
        [AccountContext, UUID, CreateEntryPayload, datetime], Awaitable[ClinicalEntry]
    ]
    revise: Callable[
        [ClinicalEntry, dict[str, object], datetime], Awaitable[ClinicalEntry]
    ]
    response: Callable[[ClinicalEntry], EntryResponse]
    history: Callable[[AccountContext, ClinicalEntry, str, UUID], Awaitable[None]]
    valid: Callable[[EntryPayload, ClinicalEntry | EmptyType], bool]
    has_pertinent: Callable[[UUID], Awaitable[bool]]


def section_review_response(
    section: EntrySection,
    patient_id: UUID,
    review: PatientClinicalSectionReview | EmptyType,
    active_count: int,
) -> ClinicalSectionReviewResponse:
    if review is Empty:
        return ClinicalSectionReviewResponse(
            patient_id=patient_id,
            section=section,
            information_status="not_recorded",
            source_type=None,
            reviewed_by_user_id=None,
            reviewed_at=None,
            active_count=active_count,
            version=0,
        )

    return ClinicalSectionReviewResponse(
        patient_id=review.patient_id,
        section=section,
        information_status=review.information_status,
        source_type=review.source_type,
        reviewed_by_user_id=review.reviewed_by_user_id,
        reviewed_at=review.reviewed_at,
        active_count=active_count,
        version=review.version,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


async def current_section_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    section: EntrySection,
    active_count: int,
) -> ClinicalSectionReviewResponse:
    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, section
    )

    return section_review_response(section, patient_id, review, active_count)


async def record_section_history(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    section: EntrySection,
    review: PatientClinicalSectionReview,
    action: str,
    operation_id: UUID,
) -> None:
    await dao_section_review_histories.add(
        db,
        PatientClinicalSectionReviewHistory(
            account_id=context.account.id,
            patient_id=patient_id,
            section=section,
            version=review.version,
            information_status=review.information_status,
            source_type=review.source_type,
            action=action,
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=review.reviewed_at,
        ),
    )


async def derive_section_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    section: EntrySection,
    operation_id: UUID,
    was_pertinent: bool,
    pertinent: bool,
) -> list[AccountChange]:
    if was_pertinent == pertinent:
        return []

    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, section
    )
    expected = "has_entries" if pertinent else "unknown"

    if review is not Empty and review.information_status == expected:
        return []

    now = await clinical_server_time(db)

    if review is Empty:
        review = PatientClinicalSectionReview(
            account_id=context.account.id,
            patient_id=patient_id,
            section=section,
            information_status=expected,
            source_type="unknown",
            reviewed_by_user_id=context.actor.user_id,
            reviewed_at=now,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_section_reviews.add(db, review)
    else:
        review.information_status = expected
        review.source_type = "unknown"
        review.reviewed_by_user_id = context.actor.user_id
        review.reviewed_at = now
        review.updated_at = now
        review.version += 1
        await dao_section_reviews.flush(db)

    await record_section_history(
        db, context, patient_id, section, review, "derived", operation_id
    )
    active_count = (
        await dao_conditions.active_count(db, context.account.id, patient_id)
        if section == "conditions"
        else await dao_allergies.active_count(db, context.account.id, patient_id)
    )
    state = section_review_response(section, patient_id, review, active_count)

    return [
        AccountChange(
            "patient_clinical_section_review",
            str(patient_id),
            state,
            state.version,
            f"clinical_{section}",
        )
    ]


async def apply_section_review(
    db: AsyncSession,
    context: AccountContext,
    patient_id: UUID,
    section: EntrySection,
    expected_version: int,
    payload: SetPatientClinicalSectionReviewPayload,
    operation_id: UUID,
    has_pertinent: Callable[[], Awaitable[bool]],
    active_count: Callable[[], Awaitable[int]],
) -> Result[AccountEffect, AccountObjectNotFound | AccountRuleError]:
    if payload.section != section:
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if await lock_clinical_patient(db, context.account.id, patient_id) is Empty:
        return Err(AccountObjectNotFound())

    review = await dao_section_reviews.scoped(
        db, context.account.id, patient_id, section
    )
    current_version = 0 if review is Empty else review.version

    if current_version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", current_version))

    pertinent = await has_pertinent()

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
            section=section,
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

    await record_section_history(
        db, context, patient_id, section, review, "set", operation_id
    )
    state = section_review_response(section, patient_id, review, await active_count())

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
                    f"clinical_{section}",
                )
            ],
            False,
        )
    )


async def read_section_review(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    section: EntrySection,
    query: PageQuery | ClinicalHistoryQuery,
    history: bool,
    audit_action: str,
    active_count: Callable[[], Awaitable[int]],
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, section)

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if history:
            rows, total = await dao_section_review_histories.page(
                db,
                account_id,
                patient_id,
                section,
                (query.page - 1) * query.shows,
                query.shows,
                query.after_version
                if isinstance(query, ClinicalHistoryQuery)
                else None,
            )
            response = clinical_page(
                rows, total, ClinicalSectionReviewHistoryResponse.model_validate
            )
        else:
            response = await current_section_review(
                db, scope.value, patient_id, section, await active_count()
            )

        await record_clinical_read(
            db,
            scope.value,
            audit_action,
            "patient_clinical_section_review",
            str(patient_id),
        )

    return Ok(response)


async def apply_entry_write(
    db: AsyncSession,
    context: AccountContext,
    section: EntrySection,
    kind: Literal["create", "update", "invalidate"],
    entity_key: UUID,
    expected_version: int,
    payload: EntryPayload,
    operation_id: UUID,
    adapter: EntryAdapter,
) -> Result[AccountEffect, AccountObjectNotFound | AccountRuleError]:
    async def finish(
        entry: ClinicalEntry, patient_id: UUID, was_pertinent: bool, event: str
    ) -> AccountEffect:
        await adapter.history(context, entry, event, operation_id)
        state = adapter.response(entry)
        entity_type = (
            "patient_condition"
            if section == "conditions"
            else "patient_allergy_intolerance"
        )
        changes_list = [
            AccountChange(
                entity_type, str(entry.id), state, entry.version, f"clinical_{section}"
            )
        ]
        changes_list.extend(
            await derive_section_review(
                db,
                context,
                patient_id,
                section,
                operation_id,
                was_pertinent,
                await adapter.has_pertinent(patient_id),
            )
        )

        return AccountEffect(state, entry.version, changes_list, False)

    if kind == "create":
        if expected_version != 0 or not isinstance(
            payload,
            CreatePatientConditionPayload | CreatePatientAllergyIntolerancePayload,
        ):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        patient_id = payload.patient_id

        if await lock_clinical_patient(db, context.account.id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if not adapter.valid(payload, Empty):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        was_pertinent = await adapter.has_pertinent(patient_id)
        entry = await adapter.create(
            context, entity_key, payload, await clinical_server_time(db)
        )
        return Ok(await finish(entry, patient_id, was_pertinent, "created"))

    entry = await adapter.scoped(entity_key)

    if entry is Empty:
        return Err(AccountObjectNotFound())

    patient_id = entry.patient_id

    if await lock_clinical_patient(db, context.account.id, patient_id) is Empty:
        return Err(AccountObjectNotFound())

    if entry.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", entry.version))

    if entry.verification_status == "entered-in-error":
        return Err(AccountRuleError("INVALID_STATE_TRANSITION", entry.version))

    if not adapter.valid(payload, entry):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    changes = (
        payload.model_dump(exclude_unset=True)
        if kind == "update"
        else {
            "verification_status": "entered-in-error",
            "correction_reason": payload.correction_reason,
        }
    )

    if all(getattr(entry, name) == value for name, value in changes.items()):
        return Err(AccountRuleError("NO_CHANGES", entry.version))

    was_pertinent = entry.verification_status not in ("refuted", "entered-in-error")
    entry.updated_by_user_id = context.actor.user_id
    entry = await adapter.revise(entry, changes, await clinical_server_time(db))

    return Ok(await finish(entry, patient_id, was_pertinent, kind + "d"))


class PatientEntry(Protocol):
    patient_id: UUID


async def read_entry[Entry: PatientEntry, Response: BaseModel](
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    section: EntrySection,
    entry_id: UUID | None,
    query: PageQuery,
    scoped: Callable[[UUID], Awaitable[Entry | EmptyType]],
    page: Callable[[PageQuery], Awaitable[tuple[list[Entry], int]]],
    response: Callable[[Entry], Response],
    audit_action: str,
    object_type: str,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, section)

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if entry_id is None:
            rows, total = await page(query)
            result = clinical_page(rows, total, response)
        else:
            entry = await scoped(entry_id)
            if entry is Empty or entry.patient_id != patient_id:
                return Err(AccountObjectNotFound())
            result = response(entry)

        await record_clinical_read(
            db, scope.value, audit_action, object_type, str(entry_id or patient_id)
        )

    return Ok(result)


async def read_entry_history[Entry: PatientEntry, Response: BaseModel](
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    section: EntrySection,
    entry_id: UUID,
    query: ClinicalHistoryQuery,
    scoped: Callable[[UUID], Awaitable[Entry | EmptyType]],
    page: Callable[[int, int, int | None], Awaitable[tuple[list[Entry], int]]],
    response: Callable[[Entry], Response],
    audit_action: str,
    object_type: str,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, section)

        if isinstance(scope, Err):
            return scope

        entry = await scoped(entry_id)

        if entry is Empty or entry.patient_id != patient_id:
            return Err(AccountObjectNotFound())

        rows, total = await page(
            (query.page - 1) * query.shows, query.shows, query.after_version
        )
        result = clinical_page(rows, total, response)
        await record_clinical_read(
            db, scope.value, audit_action, object_type, str(entry_id)
        )

    return Ok(result)
