from __future__ import annotations

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
from src.api.clinical_records.domain.clinical import (
    ClinicalHistoryQuery,
    ClinicalProfileHistoryResponse,
    ClinicalProfileResponse,
    SetPatientSexAtBirthPayload,
)
from src.api.clinical_records.repository.dao import (
    dao_clinical_profile_histories,
    dao_clinical_profiles,
)
from src.api.clinical_records.repository.models import (
    PatientClinicalProfile,
    PatientClinicalProfileHistory,
)
from src.api.patients.application.patients_cases import (
    clinical_patient,
    clinical_server_time,
    clinical_today,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def clinical_profile_response(
    profile: PatientClinicalProfile,
    patient,
    today,
) -> ClinicalProfileResponse:
    birth_date = patient.birth_date
    age_years = None

    if birth_date is not None:
        age_years = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )

    return ClinicalProfileResponse(
        patient_id=patient.patient_id,
        sex_at_birth=profile.sex_at_birth,
        source_type=profile.source_type,
        version=profile.version,
        birth_date=birth_date,
        patient_version=patient.version,
        age_years=age_years,
        age_as_of=today,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def apply_clinical_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if action != "SetPatientSexAtBirth":
        return Err(AccountRuleError("UNSUPPORTED_OPERATION"))

    if context.clinical_permissions.clinical_profile != "read_write":
        return Err(AccessDenied())

    if not isinstance(payload, SetPatientSexAtBirthPayload):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    patient = await clinical_patient(db, context.account.id, entity_key)

    if patient is Empty:
        return Err(AccountObjectNotFound())

    profile = await dao_clinical_profiles.scoped(db, context.account.id, entity_key)

    if profile is Empty:
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if payload.sex_at_birth is None:
            return Err(AccountRuleError("NO_CHANGES", 0))

        version = 1
    else:
        if profile.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", profile.version))

        if (
            profile.sex_at_birth == payload.sex_at_birth
            and profile.source_type == payload.source_type
        ):
            return Err(AccountRuleError("NO_CHANGES", profile.version))

        version = profile.version + 1

    now = await clinical_server_time(db)

    if profile is Empty:
        profile = PatientClinicalProfile(
            account_id=context.account.id,
            patient_id=entity_key,
            sex_at_birth=payload.sex_at_birth,
            source_type=payload.source_type,
            created_by_user_id=context.actor.user_id,
            updated_by_user_id=context.actor.user_id,
            created_at=now,
            updated_at=now,
            version=version,
        )
        await dao_clinical_profiles.add(db, profile)
    else:
        profile.sex_at_birth = payload.sex_at_birth
        profile.source_type = payload.source_type
        profile.updated_by_user_id = context.actor.user_id
        profile.updated_at = now
        profile.version = version
        await dao_clinical_profiles.flush(db)

    await dao_clinical_profile_histories.add(
        db,
        PatientClinicalProfileHistory(
            account_id=context.account.id,
            patient_id=entity_key,
            version=version,
            sex_at_birth=payload.sex_at_birth,
            source_type=payload.source_type,
            action="set",
            actor_user_id=context.actor.user_id,
            operation_id=operation_id,
            changed_at=now,
        ),
    )
    today = await clinical_today(db, context.account.time_zone)
    state = clinical_profile_response(profile, patient, today)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "patient_clinical_profile",
                    str(entity_key),
                    state,
                    state.version,
                    "clinical_profile",
                )
            ],
            False,
        )
    )


async def read_clinical_profile(
    db: AsyncSession, credential: str | None, account_id: UUID, patient_id: UUID
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "profile")

        if isinstance(scope, Err):
            return scope

        patient = await clinical_patient(db, account_id, patient_id)

        if patient is Empty:
            return Err(AccountObjectNotFound())

        profile = await dao_clinical_profiles.scoped(db, account_id, patient_id)
        today = await clinical_today(db, scope.value.account.time_zone)

        if profile is Empty:
            response = ClinicalProfileResponse(
                patient_id=patient_id,
                sex_at_birth=None,
                source_type=None,
                version=0,
                birth_date=patient.birth_date,
                patient_version=patient.version,
                age_years=None
                if patient.birth_date is None
                else today.year
                - patient.birth_date.year
                - (
                    (today.month, today.day)
                    < (patient.birth_date.month, patient.birth_date.day)
                ),
                age_as_of=today,
            )
        else:
            response = clinical_profile_response(profile, patient, today)

        await record_clinical_read(
            db,
            scope.value,
            "ReadClinicalProfile",
            "patient_clinical_profile",
            str(patient_id),
        )

    return Ok(response)


async def read_clinical_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "profile")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        rows, total = await dao_clinical_profile_histories.page(
            db,
            account_id,
            patient_id,
            (query.page - 1) * query.shows,
            query.shows,
            query.after_version,
        )
        response = clinical_page(
            rows, total, ClinicalProfileHistoryResponse.model_validate
        )
        await record_clinical_read(
            db,
            scope.value,
            "ReadClinicalProfileHistory",
            "patient_clinical_profile",
            str(patient_id),
        )

    return Ok(response)
