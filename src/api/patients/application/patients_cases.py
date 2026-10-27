from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied
from src.api.patients.domain.patients import (
    AddPatientIdentifierPayload,
    PatientCompletionPayload,
    PatientFields,
    PatientIdentifierResponse,
    PatientPatch,
    PatientProfileResponse,
    PatientQuery,
    PatientStatusPayload,
    RegisterPatientPayload,
)
from src.api.patients.repository.dao import (
    dao_identifiers,
    dao_patients,
    dao_profiles,
    dao_relationships,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel, PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def profile_satisfies(
    db: AsyncSession,
    context: AccountContext,
    profile: PatientProfileResponse,
    instant: datetime,
    *,
    contact_change=None,
    relationship_change=None,
) -> bool:
    if not profile.full_name or profile.identification_basis is None:
        return False

    responsible = False

    for relationship, contact in await dao_relationships.candidates(
        db, context.account.id, profile.patient_id
    ):
        contact_values = (
            contact_change[1]
            if contact_change is not None and contact.id == contact_change[0]
            else {}
        )
        relation_values = (
            relationship_change[1]
            if relationship_change is not None
            and relationship.contact_person_id == relationship_change[0]
            else {}
        )
        start = relation_values.get("valid_from", relationship.valid_from)
        end = relation_values.get("valid_until", relationship.valid_until)

        if (
            relation_values.get("status", relationship.status) == "active"
            and relation_values.get(
                "is_responsible_contact", relationship.is_responsible_contact
            )
            and start <= instant
            and (end is None or instant < end)
            and contact_values.get("status", contact.status) == "active"
            and contact_values.get("phone_code", contact.phone_code) is not None
            and contact_values.get("phone", contact.phone) is not None
        ):
            responsible = True
            break

    if profile.identification_basis == "own_document":
        return await dao_identifiers.has_document(db, profile.patient_id) and (
            responsible
            or (profile.phone_code is not None and profile.phone is not None)
        )

    day = await dao_patients.local_date(db, context.account.time_zone, instant)

    return responsible and profile.is_minor_on(day)


async def booking_patient(
    db: AsyncSession, context: AccountContext, patient_id: UUID, starts_at: datetime
):
    """Called inside the authorized appointment transaction; recheck at its date."""
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        return Err(AccountRuleError("VALIDATION_ERROR"))

    row = await dao_profiles.scoped(db, context.account.id, patient_id)

    if row is Empty:
        return Err(AccountObjectNotFound())

    profile = PatientProfileResponse.model_validate(row)

    if (
        context.account.status != "active"
        or row.status != "active"
        or row.completion_status != "complete"
        or not await profile_satisfies(db, context, profile, starts_at)
    ):
        return Err(AccountRuleError("COMPLETENESS_CONFLICT", row.version))

    return Ok(profile)


async def apply_patient_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccountObjectNotFound | AccountRuleError]:
    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if action == "AddPatientIdentifier":
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if not isinstance(payload, AddPatientIdentifierPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        data = payload

        if await dao_profiles.scoped(db, context.account.id, data.patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if not await dao_identifiers.available_ids(db, [entity_key]):
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        now = await dao_patients.server_time(db)
        row = await dao_identifiers.create(
            db,
            obj_in={
                **data.model_dump(),
                "id": entity_key,
                "verification_status": "declared",
                "verified_at": None,
                "verified_by_user_id": None,
                "created_at": now,
                "updated_at": now,
                "version": 1,
            },
            commit=False,
        )
        state = PatientIdentifierResponse.model_validate(row)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [
                    AccountChange(
                        "patient_identifier",
                        str(entity_key),
                        state,
                        state.version,
                        "members",
                    )
                ],
                False,
            )
        )

    row = await dao_profiles.scoped(db, context.account.id, entity_key)

    if action == "RegisterPatient":
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("NO_CHANGES", row.version))

        if not isinstance(payload, RegisterPatientPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        data = payload

        today = await dao_patients.local_today(db, context.account.time_zone)

        if data.birth_date is not None and data.birth_date > today:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if not await dao_identifiers.available_ids(
            db, [item.id for item in data.identifiers]
        ):
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        if not await dao_patients.reserve_id(db, entity_key):
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        now = await dao_patients.server_time(db)
        row = await dao_profiles.create_profile(
            db,
            {
                **data.model_dump(exclude={"identifiers"}),
                "account_id": context.account.id,
                "patient_id": entity_key,
                "completion_status": "draft",
                "status": "active",
                "version": 1,
                "created_at": now,
                "updated_at": now,
            },
            commit=False,
        )
        changes = []

        for item in data.identifiers:
            document = await dao_identifiers.create(
                db,
                obj_in={
                    **item.model_dump(),
                    "patient_id": entity_key,
                    "verification_status": "declared",
                    "verified_at": None,
                    "verified_by_user_id": None,
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                },
                commit=False,
            )
            state = PatientIdentifierResponse.model_validate(document)
            changes.append(
                AccountChange(
                    "patient_identifier", str(state.id), state, state.version, "members"
                )
            )
    else:
        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        try:
            schema = {
                "UpdatePatientProfile": PatientPatch,
                "SetPatientCompletion": PatientCompletionPayload,
                "SetPatientProfileStatus": PatientStatusPayload,
            }[action]

            if payload is None or not isinstance(payload, schema):
                return Err(AccountRuleError("VALIDATION_ERROR"))

            data = payload
            values = data.model_dump(exclude_unset=True)

            if action == "UpdatePatientProfile":
                if not isinstance(data, PatientPatch):
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                PatientFields.model_validate(
                    {
                        **{
                            name: getattr(row, name)
                            for name in PatientFields.model_fields
                        },
                        **values,
                    }
                )

                if (
                    data.birth_date is not None
                    and data.birth_date
                    > await dao_patients.local_today(db, context.account.time_zone)
                ):
                    return Err(AccountRuleError("VALIDATION_ERROR"))
        except ValidationError:
            return Err(AccountRuleError("VALIDATION_ERROR"))

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        now = await dao_patients.server_time(db)
        proposed = PatientProfileResponse.model_validate(row).model_copy(update=values)

        if proposed.completion_status == "complete" and not await profile_satisfies(
            db, context, proposed, now
        ):
            return Err(AccountRuleError("COMPLETENESS_CONFLICT", row.version))

        row = await dao_profiles.revise(db, row, values, now)
        changes = []

    state = PatientProfileResponse.model_validate(row)
    changes.insert(
        0,
        AccountChange(
            "patient_profile", str(entity_key), state, state.version, "members"
        ),
    )

    return Ok(AccountEffect(state, state.version, changes, False))


async def read_patients(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: PatientQuery | PageQuery,
    patient_id: UUID | None = None,
    *,
    identifiers: bool = False,
):
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        scope = await account_context(
            db, identity.value, account_id, require_device=True
        )

        if isinstance(scope, Err):
            return scope

        if scope.value.account.status != "active":
            return Err(AccessDenied())

        if patient_id is None:
            rows, total = await dao_profiles.page(db, account_id, query)
            response = PaginatedResponse[PatientProfileResponse](
                items=[PatientProfileResponse.model_validate(row) for row in rows],
                total=total,
            )
        else:
            row = await dao_profiles.scoped(db, account_id, patient_id)

            if row is Empty:
                return Err(AccountObjectNotFound())

            if identifiers:
                rows, total = await dao_identifiers.page(
                    db, patient_id, (query.page - 1) * query.shows, query.shows
                )
                response = PaginatedResponse[PatientIdentifierResponse](
                    items=[
                        PatientIdentifierResponse.model_validate(item) for item in rows
                    ],
                    total=total,
                )
            else:
                response = PatientProfileResponse.model_validate(row)

    return Ok(response)
