from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.analytics.domain.growth import (
    GrowthInput,
    GrowthResult,
    compute_growth,
)
from src.api.analytics.domain.references import Indicator, Sex
from src.api.clinical_records.application.access_cases import (
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.repository.dao import (
    dao_clinical_profiles,
    dao_measurements,
)
from src.api.patients.application.patients_cases import clinical_patient
from src.core import Err, Ok
from src.core.db import transaction
from pydantic import ConfigDict

from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GrowthPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measured_at: str
    value: str
    age_months: int
    z_score: str | None = None
    limit_explanation: str | None = None
    source_measurement_id: str
    source_version: int


class GrowthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str
    indicator: Indicator
    reference_version: str | None = None
    points: list[GrowthPoint]


async def read_growth(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    indicator: Indicator,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "measurements")
        if isinstance(scope, Err):
            return scope

        patient = await clinical_patient(db, account_id, patient_id)
        if patient is Empty:
            return Err(AccountObjectNotFound())

        profile = await dao_clinical_profiles.scoped(db, account_id, patient_id)
        sex: Sex | None = None
        if profile is not Empty and profile.sex_at_birth in ("male", "female"):
            sex = profile.sex_at_birth

        rows = await dao_measurements.series_for_kind(db, account_id, patient_id, "weight")
        if indicator != "weight_for_age":
            rows = []

        points: list[GrowthPoint] = []
        reference_version: str | None = None

        for row in rows:
            if row.record_status != "valid" or row.value is None:
                continue
            measured_on = row.measured_at.date()
            age_months = None
            if patient.birth_date is not None:
                age_months = (measured_on.year - patient.birth_date.year) * 12 + (
                    measured_on.month - patient.birth_date.month
                )
                if measured_on.day < patient.birth_date.day:
                    age_months -= 1
            if age_months is None or age_months < 0 or sex is None:
                points.append(
                    GrowthPoint(
                        measured_at=measured_on.isoformat(),
                        value=str(row.value),
                        age_months=max(age_months or 0, 0),
                        limit_explanation="Falta nacimiento o sexo al nacer; no se aplica referencia.",
                        source_measurement_id=str(row.id),
                        source_version=row.version,
                    )
                )
                continue

            result = compute_growth(
                GrowthInput(
                    reference_code="who2006",
                    indicator=indicator,
                    sex=sex,
                    age_months=age_months,
                    value=row.value,
                )
            )
            if isinstance(result, GrowthResult):
                reference_version = result.reference_version
                points.append(
                    GrowthPoint(
                        measured_at=measured_on.isoformat(),
                        value=str(row.value),
                        age_months=age_months,
                        z_score=str(result.z_score),
                        source_measurement_id=str(row.id),
                        source_version=row.version,
                    )
                )
            else:
                points.append(
                    GrowthPoint(
                        measured_at=measured_on.isoformat(),
                        value=str(row.value),
                        age_months=age_months,
                        limit_explanation=result.limit_explanation,
                        source_measurement_id=str(row.id),
                        source_version=row.version,
                    )
                )

        response = GrowthResponse(
            patient_id=str(patient_id),
            indicator=indicator,
            reference_version=reference_version,
            points=points,
        )

        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientGrowth",
            "patient_measurement",
            str(patient_id),
        )

    return Ok(response)
