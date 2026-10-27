from __future__ import annotations

from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import (
    AccountContext,
    AccountDeviceResponse,
    InvitationResponse,
    MemberResponse,
    ProfessionalResponse,
)
from src.api.accounts.repository.dao import (
    dao_account_devices,
    dao_account_professionals,
    dao_invitations,
    dao_memberships,
    dao_professionals,
)
from src.api.authorization.application.authorization_cases import (
    device_summaries,
    identified_users,
)
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_accounts(
    db: AsyncSession, context: AccountContext
) -> list[SyncItem]:
    """Read permitted account data inside the caller's coherent capture."""
    account = context.account
    items = [
        SyncItem(
            entity_type="account",
            entity_key=account.id,
            entity_version=account.version,
            state=account,
        )
    ]
    links, _ = await dao_account_professionals.get_multi(
        db,
        where={"account_id": account.id},
        ordering=[("professional_id", False)],
        shows=None,
    )
    professionals, _ = await dao_professionals.get_multi(
        db,
        where={"id": [link.professional_id for link in links]},
        ordering=[("id", False)],
        shows=None,
    )
    items.extend(
        SyncItem(
            entity_type="professional",
            entity_key=row.id,
            entity_version=row.version,
            state=ProfessionalResponse.model_validate(row),
        )
        for row in professionals
    )

    if not context.owner:
        return items

    members, _ = await dao_memberships.get_multi(
        db, where={"account_id": account.id}, ordering=[("user_id", False)], shows=None
    )
    users = await identified_users(db, [row.user_id for row in members])

    for row in members:
        state = MemberResponse(
            user_id=row.user_id,
            display_name=users[row.user_id].display_name,
            role="owner" if row.user_id == account.owner_user_id else "assistant",
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
        )
        items.append(
            SyncItem(
                entity_type="membership",
                entity_key=row.user_id,
                entity_version=row.version,
                state=state,
            )
        )

    devices, _ = await dao_account_devices.get_multi(
        db,
        where={"account_id": account.id},
        ordering=[("device_id", False)],
        shows=None,
    )
    details = await device_summaries(db, [row.device_id for row in devices])

    for row in devices:
        device = details[row.device_id]
        state = AccountDeviceResponse(
            device_id=row.device_id,
            display_name=device.display_name,
            status=row.status,
            client_version=device.client_version,
            local_schema_version=device.local_schema_version,
            last_seen_at=device.last_seen_at,
            version=row.version,
        )
        items.append(
            SyncItem(
                entity_type="account_device",
                entity_key=row.device_id,
                entity_version=row.version,
                state=state,
            )
        )

    invitations, _ = await dao_invitations.get_multi(
        db, where={"account_id": account.id}, ordering=[("id", False)], shows=None
    )
    items.extend(
        SyncItem(
            entity_type="invitation",
            entity_key=row.id,
            entity_version=row.version,
            state=InvitationResponse.model_validate(row),
        )
        for row in invitations
    )

    return items
