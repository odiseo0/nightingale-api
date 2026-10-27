from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import AccountContext
from src.api.patients.domain.contacts import ContactResponse, RelationshipResponse
from src.api.patients.domain.patients import (
    PatientIdentifierResponse,
    PatientProfileResponse,
)
from src.api.patients.repository.dao import (
    dao_contacts,
    dao_identifiers,
    dao_profiles,
    dao_relationships,
)
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_patients(
    db: AsyncSession,
    context: AccountContext,
    required_patients: set[UUID],
    required_contacts: set[UUID],
) -> list[SyncItem]:
    """Include account profiles and the references needed by captured appointments."""
    account_id = context.account.id
    rows, _ = await dao_profiles.get_multi(
        db,
        where={"account_id": account_id},
        ordering=[("patient_id", False)],
        shows=None,
    )
    profiles = [
        row
        for row in rows
        if row.status == "active"
        or row.completion_status == "draft"
        or row.patient_id in required_patients
    ]
    patients = [row.patient_id for row in profiles]
    items = [
        SyncItem(
            entity_type="patient_profile",
            entity_key=row.patient_id,
            entity_version=row.version,
            state=PatientProfileResponse.model_validate(row),
        )
        for row in profiles
    ]
    identifiers, _ = await dao_identifiers.get_multi(
        db, where={"patient_id": patients}, ordering=[("id", False)], shows=None
    )
    items.extend(
        SyncItem(
            entity_type="patient_identifier",
            entity_key=row.id,
            entity_version=row.version,
            state=PatientIdentifierResponse.model_validate(row),
        )
        for row in identifiers
    )
    relationships, _ = await dao_relationships.get_multi(
        db,
        where={"account_id": account_id, "patient_id": patients},
        ordering=[("patient_id", False), ("contact_person_id", False)],
        shows=None,
    )
    items.extend(
        SyncItem(
            entity_type="patient_contact",
            entity_key={
                "patientId": row.patient_id,
                "contactPersonId": row.contact_person_id,
            },
            entity_version=row.version,
            state=RelationshipResponse.model_validate(row),
        )
        for row in relationships
    )
    contacts, _ = await dao_contacts.get_multi(
        db, where={"account_id": account_id}, ordering=[("id", False)], shows=None
    )
    linked_contacts = required_contacts | {
        row.contact_person_id for row in relationships
    }
    items.extend(
        SyncItem(
            entity_type="contact_person",
            entity_key=row.id,
            entity_version=row.version,
            state=ContactResponse.model_validate(row),
        )
        for row in contacts
        if row.status == "active" or row.id in linked_contacts
    )

    return items
