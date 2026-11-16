from typing import TYPE_CHECKING
from uuid import UUID

from src.api.clinical_records.repository.dao import dao_clinical_timeline
from src.api.encounters.domain.encounters import PatientEncounterResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def project_encounter(
    db: AsyncSession, account_id: UUID, encounter: PatientEncounterResponse
) -> None:
    await dao_clinical_timeline.project_encounter(db, account_id, encounter)
