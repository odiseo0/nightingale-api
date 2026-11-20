from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.analytics.domain.queries import (
    SeriesPointResponse,
    SeriesQuery,
    SeriesResponse,
)
from src.api.analytics.domain.series import SeriesEntry, select_valid_series
from src.api.clinical_records.application.access_cases import (
    clinical_read_scope,
    record_clinical_read,
)
from src.api.clinical_records.repository.dao import dao_measurements
from src.api.patients.application.patients_cases import clinical_patient
from src.core import Err, Ok
from src.core.db import transaction
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def read_series(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: SeriesQuery,
):
    async with transaction(db):
        scope = await clinical_read_scope(db, credential, account_id, "measurements")

        if isinstance(scope, Err):
            return scope

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        rows, total = await dao_measurements.page_for_kind(
            db,
            account_id,
            patient_id,
            query.kind,
            (query.page - 1) * query.shows,
            query.shows,
        )
        entries = [
            SeriesEntry(
                measurement_id=str(row.id),
                source_version=row.version,
                kind=row.kind,
                measured_at=row.measured_at.date(),
                value=row.value,
                systolic_value=row.systolic_value,
                diastolic_value=row.diastolic_value,
                unit=row.unit,
                record_status=row.record_status,
            )
            for row in rows
        ]
        selection = select_valid_series(entries, query.kind)

        response = SeriesResponse(
            patient_id=str(patient_id),
            measurement_kind=query.kind,
            total=total,
            points=[
                SeriesPointResponse(
                    measurement_kind=point.measurement_kind,
                    measured_at=point.measured_at,
                    value=point.value,
                    systolic_value=point.systolic_value,
                    diastolic_value=point.diastolic_value,
                    unit=point.unit,
                    source_measurement_id=point.source_measurement_id,
                    source_version=point.source_version,
                )
                for point in selection.points
            ],
        )

        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientMeasurementSeries",
            "patient_measurement",
            str(patient_id),
        )

    return Ok(response)
