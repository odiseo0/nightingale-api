from typing import TYPE_CHECKING
from uuid import UUID

from src.api.encounters.application.encounters_cases import encounter_response
from src.api.encounters.repository.dao import dao_encounters
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_encounters(db: AsyncSession, account_id: UUID) -> list[SyncItem]:
    return [
        SyncItem(
            entity_type="clinical_encounter",
            entity_key=row.id,
            entity_version=row.version,
            state=encounter_response(row),
        )
        for row in await dao_encounters.valid_snapshot(db, account_id)
    ]
