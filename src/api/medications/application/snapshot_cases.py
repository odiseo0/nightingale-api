from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.medications.application.medication_cases import medication_response
from src.api.medications.repository.dao import dao_declared_medications
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_declared_medications(
    db: AsyncSession, context: AccountContext
) -> list[SyncItem]:
    rows = await dao_declared_medications.valid_snapshot(db, context.account.id)

    return [
        SyncItem(
            entity_type="declared_medication",
            entity_key=row.id,
            entity_version=row.version,
            state=medication_response(row),
        )
        for row in rows
    ]
