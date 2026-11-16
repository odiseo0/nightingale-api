from typing import TYPE_CHECKING
from uuid import UUID

from src.api.clinical_records.domain.allergies import PatientAllergyIntoleranceResponse
from src.api.clinical_records.domain.antecedents import PatientAntecedentResponse
from src.api.clinical_records.domain.conditions import PatientConditionResponse
from src.api.clinical_records.domain.immunizations import PatientImmunizationResponse
from src.api.clinical_records.domain.measurements import PatientMeasurementResponse
from src.api.clinical_records.domain.notes import PatientNoteResponse
from src.api.clinical_records.repository.dao import dao_clinical_timeline
from src.api.encounters.domain.encounters import PatientEncounterResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def project_encounter(
    db: AsyncSession, account_id: UUID, encounter: PatientEncounterResponse
) -> None:
    await dao_clinical_timeline.project_encounter(db, account_id, encounter)


async def project_note(
    db: AsyncSession, account_id: UUID, note: PatientNoteResponse
) -> None:
    await dao_clinical_timeline.project_note(db, account_id, note)


async def project_measurement(
    db: AsyncSession, account_id: UUID, measurement: PatientMeasurementResponse
) -> None:
    await dao_clinical_timeline.project_measurement(db, account_id, measurement)


async def project_immunization(
    db: AsyncSession, account_id: UUID, immunization: PatientImmunizationResponse
) -> None:
    await dao_clinical_timeline.project_immunization(db, account_id, immunization)


async def project_antecedent(
    db: AsyncSession, account_id: UUID, antecedent: PatientAntecedentResponse
) -> None:
    await dao_clinical_timeline.project_antecedent(db, account_id, antecedent)


async def project_entry(
    db: AsyncSession,
    account_id: UUID,
    entry: PatientConditionResponse | PatientAllergyIntoleranceResponse,
) -> None:
    await dao_clinical_timeline.project_entry(db, account_id, entry)
