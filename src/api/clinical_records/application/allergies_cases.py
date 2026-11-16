from __future__ import annotations

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
from src.api.clinical_records.application.conditions_cases import (
    validate_condition_dates,
)
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
    ClinicalSectionReviewResponse,
    SetPatientClinicalSectionReviewPayload,
)
from src.api.clinical_records.repository.allergies import (
    PatientAllergyIntolerance,
    PatientAllergyIntoleranceHistory,
)
from src.api.clinical_records.repository.dao import (
    dao_allergies,
    dao_allergy_histories,
)
from src.api.patients.application.patients_cases import clinical_today
from src.core import Err, Result
from src.core.schema import PageQuery
from src.core.utils.utils import EmptyType

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
    return await current_section_review(
        db,
        context,
        patient_id,
        "allergies",
        await dao_allergies.active_count(db, context.account.id, patient_id),
    )


async def derive_allergy_review(
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
        "allergies",
        operation_id,
        was_pertinent,
        await dao_allergies.has_pertinent(db, context.account.id, patient_id),
    )


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

    kind = {
        "CreatePatientAllergyIntolerance": "create",
        "UpdatePatientAllergyIntolerance": "update",
        "InvalidatePatientAllergyIntolerance": "invalidate",
    }.get(action)
    expected = {
        "create": CreatePatientAllergyIntolerancePayload,
        "update": UpdatePatientAllergyIntolerancePayload,
        "invalidate": InvalidatePatientAllergyIntolerancePayload,
    }

    if kind is None or not isinstance(payload, expected[kind]):
        return Err(
            AccountRuleError(
                "UNSUPPORTED_OPERATION" if kind is None else "VALIDATION_ERROR"
            )
        )

    today = await clinical_today(db, context.account.time_zone)

    def valid(
        data: CreatePatientAllergyIntolerancePayload
        | UpdatePatientAllergyIntolerancePayload
        | InvalidatePatientAllergyIntolerancePayload,
        entry: PatientAllergyIntolerance | EmptyType,
    ) -> bool:
        if isinstance(data, InvalidatePatientAllergyIntolerancePayload):
            return True

        values = data.model_dump(exclude_unset=True) if kind == "update" else {}

        try:
            validate_condition_dates(
                values.get("onset_date", getattr(entry, "onset_date", data.onset_date)),
                values.get(
                    "last_occurrence_date",
                    getattr(entry, "last_occurrence_date", data.last_occurrence_date),
                ),
                today,
            )
        except ValueError:
            return False

        return True

    async def create(
        ctx: AccountContext,
        key: UUID,
        data: CreatePatientAllergyIntolerancePayload,
        now: datetime,
    ) -> PatientAllergyIntolerance:
        allergy = PatientAllergyIntolerance(
            id=key,
            account_id=ctx.account.id,
            patient_id=data.patient_id,
            substance=data.substance,
            type=data.type,
            reaction_description=data.reaction_description,
            clinical_status=data.clinical_status,
            verification_status=data.verification_status,
            onset_date=data.onset_date,
            last_occurrence_date=data.last_occurrence_date,
            source_type=data.source_type,
            correction_reason=data.correction_reason,
            created_by_user_id=ctx.actor.user_id,
            updated_by_user_id=ctx.actor.user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await dao_allergies.add(db, allergy)

        return allergy

    return await apply_entry_write(
        db,
        context,
        "allergies",
        kind,
        entity_key,
        expected_version,
        payload,
        operation_id,
        EntryAdapter(
            scoped=lambda key: dao_allergies.scoped(db, context.account.id, key),
            create=create,
            revise=lambda entry, changes, now: dao_allergies.revise(
                db, entry, changes, now
            ),
            response=allergy_response,
            history=lambda ctx, entry, event, op: record_allergy_history(
                db, ctx, entry, event, op
            ),
            valid=valid,
            has_pertinent=lambda patient_id: dao_allergies.has_pertinent(
                db, context.account.id, patient_id
            ),
        ),
    )


async def apply_allergy_review(
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
        "allergies",
        expected_version,
        payload,
        operation_id,
        lambda: dao_allergies.has_pertinent(db, context.account.id, patient_id),
        lambda: dao_allergies.active_count(db, context.account.id, patient_id),
    )


async def read_allergies(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: AllergyQuery | PageQuery,
    allergy_id: UUID | None = None,
):
    return await read_entry(
        db,
        credential,
        account_id,
        patient_id,
        "allergies",
        allergy_id,
        query,
        lambda key: dao_allergies.scoped(db, account_id, key),
        lambda filters: dao_allergies.page(db, account_id, patient_id, filters),
        allergy_response,
        "ReadPatientAllergies",
        "patient_allergy_intolerance",
    )


async def read_allergy_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    allergy_id: UUID,
    query: ClinicalHistoryQuery,
):
    return await read_entry_history(
        db,
        credential,
        account_id,
        patient_id,
        "allergies",
        allergy_id,
        query,
        lambda key: dao_allergies.scoped(db, account_id, key),
        lambda offset, shows, after: dao_allergy_histories.page(
            db, account_id, allergy_id, offset, shows, after
        ),
        allergy_history_response,
        "ReadPatientAllergyHistory",
        "patient_allergy_intolerance",
    )


async def read_allergy_review(
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
        "allergies",
        query,
        history,
        "ReadAllergySectionReview",
        lambda: dao_allergies.active_count(db, account_id, patient_id),
    )
