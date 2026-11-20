from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.analytics.repository.dao import (
    dao_analytic_etl_state,
    dao_analytic_points,
)
from src.api.analytics.repository.models import AnalyticMeasurementPoint
from src.api.clinical_records.application.measurements_cases import (
    current_measurement_sources,
)
from src.core.utils.utils import Empty


async def run_etl(db: AsyncSession, account_id: UUID, batch_size: int = 500) -> int:
    """Project measurement changes after the durable cursor.

    Idempotent by (account, source measurement): a correction replaces its
    point in the same transaction that advances the cursor, so a crash before
    commit leaves the cursor unchanged and a retry converges to the same
    projection.
    """

    # The shared lock is sufficient for local batches; use per-account claims before production concurrency.
    await dao_analytic_etl_state.lock(db)
    state = await dao_analytic_etl_state.for_account(db, account_id)
    cursor = 0 if state is Empty else state.last_change_seq

    from src.api.sync.repository.models import ChangeLog

    rows = await db.scalars(
        select(ChangeLog)
        .where(
            ChangeLog.account_id == account_id,
            ChangeLog.entity_type == "patient_measurement",
            ChangeLog.sequence > cursor,
        )
        .order_by(ChangeLog.sequence)
        .limit(batch_size)
    )

    processed = 0
    max_seq = cursor

    for row in rows:
        projection = row.projection_json or {}
        measurement_id = projection.get("measurementId")

        if measurement_id is None:
            max_seq = max(max_seq, row.sequence)
            continue

        source_id = UUID(measurement_id)

        if projection.get("recordStatus") == "entered-in-error":
            await dao_analytic_points.delete_for_source(db, account_id, source_id)
        else:
            point = AnalyticMeasurementPoint(
                account_id=account_id,
                patient_id=projection["patientId"],
                measurement_kind=projection["kind"],
                measured_at=datetime.fromisoformat(str(projection["measuredAt"])),
                source_measurement_id=source_id,
                source_version=projection.get("version", 1),
                value=projection.get("value"),
                systolic_value=projection.get("systolicValue"),
                diastolic_value=projection.get("diastolicValue"),
                unit=projection["unit"],
                change_seq=row.sequence,
            )
            await dao_analytic_points.replace_for_source(
                db, account_id, source_id, point
            )

        processed += 1
        max_seq = max(max_seq, row.sequence)

    if max_seq > cursor:
        await dao_analytic_etl_state.advance(db, account_id, max_seq)

    return processed


async def rebuild_analytics(db: AsyncSession) -> int:
    await dao_analytic_etl_state.lock(db)
    await dao_analytic_points.clear(db)
    sources = await current_measurement_sources(db)

    for source in sources:
        point = AnalyticMeasurementPoint(
            account_id=source.account_id,
            patient_id=source.patient_id,
            measurement_kind=source.kind,
            measured_at=source.measured_at,
            source_measurement_id=source.measurement_id,
            source_version=source.version,
            value=source.value,
            systolic_value=source.systolic_value,
            diastolic_value=source.diastolic_value,
            unit=source.unit,
            change_seq=0,
        )
        await dao_analytic_points.replace_for_source(
            db, source.account_id, source.measurement_id, point
        )

    from src.api.sync.repository.models import ChangeLog

    for account_id in sorted({source.account_id for source in sources}):
        sequence = await db.scalar(
            select(func.max(ChangeLog.sequence)).where(
                ChangeLog.account_id == account_id
            )
        )
        await dao_analytic_etl_state.advance(db, account_id, sequence or 0)

    return len(sources)
