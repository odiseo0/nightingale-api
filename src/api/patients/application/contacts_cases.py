from __future__ import annotations

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
from src.api.patients.application.patients_cases import profile_satisfies
from src.api.patients.domain.contacts import (
    ContactData,
    ContactPatch,
    ContactQuery,
    ContactResponse,
    PatientContactResponse,
    RelationshipData,
    RelationshipPatch,
    RelationshipQuery,
    RelationshipResponse,
)
from src.api.patients.domain.patients import (
    PatientProfileResponse,
    PatientStatusPayload,
)
from src.api.patients.repository.dao import (
    dao_contacts,
    dao_patients,
    dao_profiles,
    dao_relationships,
)
from src.core import Err, Ok
from src.core.db import transaction
from src.core.schema import PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


CONTACT_SCHEMAS = {
    "CreateContactPerson": ContactData,
    "UpdateContactPerson": ContactPatch,
    "SetContactPersonStatus": PatientStatusPayload,
    "CreatePatientContactRelationship": RelationshipData,
    "UpdatePatientContactRelationship": RelationshipPatch,
    "SetPatientContactRelationshipStatus": PatientStatusPayload,
}


def normalized_contact_payload(action: str, payload: dict) -> dict:
    schema = CONTACT_SCHEMAS.get(action)
    if schema is not None:
        try:
            return schema.model_validate(payload).model_dump(
                mode="json",
                by_alias=True,
                exclude_unset=action.startswith("Update"),
            )
        except ValidationError:
            pass
    return payload


async def apply_contact_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key,
    expected_version: int,
    payload: dict,
):
    relationship = "Relationship" in action
    if relationship:
        if not isinstance(entity_key, dict) or set(entity_key) != {
            "patientId",
            "contactPersonId",
        }:
            return Err(AccountRuleError("VALIDATION_ERROR"))
        patient_id, contact_id = entity_key["patientId"], entity_key["contactPersonId"]
        profile = await dao_profiles.scoped(db, context.account.id, patient_id)
        contact = await dao_contacts.scoped(db, context.account.id, contact_id)
        if profile is Empty or contact is Empty:
            return Err(AccountObjectNotFound())
        row = await dao_relationships.scoped(
            db, context.account.id, patient_id, contact_id
        )
    else:
        if not isinstance(entity_key, UUID):
            return Err(AccountRuleError("VALIDATION_ERROR"))
        if action == "CreateContactPerson":
            existing = await dao_contacts.lock_new_id(db, entity_key)
            if existing is not Empty and existing.account_id != context.account.id:
                return Err(AccountRuleError("INVALID_STATE_TRANSITION"))
        row = await dao_contacts.scoped(db, context.account.id, entity_key)

    creating = action.startswith("Create")
    if creating:
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))
        if row is not Empty:
            return Err(AccountRuleError("NO_CHANGES", row.version))
    else:
        if row is Empty:
            return Err(AccountObjectNotFound())
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))
    try:
        data = CONTACT_SCHEMAS[action].model_validate(payload)
        values = data.model_dump(exclude_unset=not creating)
        if action == "UpdateContactPerson":
            merged = ContactData.model_validate(
                {
                    **{name: getattr(row, name) for name in ContactData.model_fields},
                    **values,
                }
            )
            values = {name: getattr(merged, name) for name in values}
        if action == "UpdatePatientContactRelationship":
            RelationshipData.model_validate(
                {
                    **{
                        name: getattr(row, name)
                        for name in RelationshipData.model_fields
                    },
                    **values,
                }
            )
    except ValidationError:
        return Err(AccountRuleError("VALIDATION_ERROR"))
    now = await dao_patients.server_time(db)
    if not creating and all(
        getattr(row, name) == value for name, value in values.items()
    ):
        return Err(AccountRuleError("NO_CHANGES", row.version))
    if (
        relationship
        and (
            creating
            or (
                action == "SetPatientContactRelationshipStatus"
                and data.status == "active"
            )
        )
        and (contact.status != "active" or profile.status != "active")
    ):
        return Err(AccountRuleError("INVALID_STATE_TRANSITION"))
    if (
        action == "SetPatientContactRelationshipStatus"
        and data.status == "active"
        and (
            row.valid_from > now
            or (row.valid_until is not None and row.valid_until <= now)
        )
    ):
        return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

    if not creating:
        profiles = (
            [profile]
            if relationship
            else await dao_profiles.complete_for_contact(db, context.account.id, row.id)
        )
        for dependent in profiles:
            if dependent.completion_status != "complete":
                continue
            valid = await profile_satisfies(
                db,
                context,
                PatientProfileResponse.model_validate(dependent),
                now,
                contact_change=None if relationship else (row.id, values),
                relationship_change=(contact_id, values) if relationship else None,
            )
            if not valid:
                return Err(AccountRuleError("COMPLETENESS_CONFLICT", row.version))

    if creating:
        common = {
            **values,
            "account_id": context.account.id,
            "status": "active",
            "version": 1,
            "created_at": now,
            "updated_at": now,
        }
        if relationship:
            row = await dao_relationships.create_relationship(
                db,
                {
                    **common,
                    "patient_id": patient_id,
                    "contact_person_id": contact_id,
                    "representation_status": "unverified",
                    "verified_at": None,
                    "verified_by_user_id": None,
                },
                commit=False,
            )
        else:
            row = await dao_contacts.create(
                db, obj_in={**common, "id": entity_key}, commit=False
            )
    else:
        row = await (dao_relationships if relationship else dao_contacts).revise(
            db, row, values, now
        )

    if relationship:
        state = RelationshipResponse.model_validate(row)
        key = {"patientId": str(patient_id), "contactPersonId": str(contact_id)}
    else:
        state = ContactResponse.model_validate(row)
        key = str(entity_key)
    entity_type = "patient_contact" if relationship else "contact_person"
    return Ok(
        AccountEffect(
            state,
            state.version,
            [AccountChange(entity_type, key, state, state.version, "members")],
            False,
        )
    )


async def read_contacts(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: ContactQuery | RelationshipQuery,
    *,
    contact_id: UUID | None = None,
    patient_id: UUID | None = None,
    relationships: bool = False,
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

        if (
            patient_id is not None
            and await dao_profiles.scoped(db, account_id, patient_id) is Empty
        ):
            return Err(AccountObjectNotFound())

        if contact_id is not None:
            contact = await dao_contacts.scoped(db, account_id, contact_id)

            if contact is Empty:
                return Err(AccountObjectNotFound())

        if relationships:
            rows, total = await dao_relationships.page(
                db, account_id, query, patient_id=patient_id, contact_id=contact_id
            )
            response = PaginatedResponse[PatientContactResponse](
                items=[PatientContactResponse.model_validate(row) for row in rows],
                total=total,
            )
        elif contact_id is not None:
            response = ContactResponse.model_validate(contact)
        else:
            rows, total = await dao_contacts.page(db, account_id, query)
            response = PaginatedResponse[ContactResponse](
                items=[ContactResponse.model_validate(row) for row in rows], total=total
            )

    return Ok(response)
