from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.analytics.repository.dao import (
    dao_analytic_etl_state,
    dao_analytic_points,
)
from src.api.analytics.repository.models import (
    AnalyticEtlState,
    AnalyticMeasurementPoint,
)
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    pass


async def _server_time(db: AsyncSession):
    from sqlalchemy import func

    return (await db.scalar(select(func.now())))


async def run_etl(db: AsyncSession, account_id: UUID, batch_size: int = 500) -> int:
    """Project measurement changes after the durable cursor.

    Idempotent by (account, source measurement): a correction replaces its
    point in the same transaction that advances the cursor, so a crash before
    commit leaves the cursor unchanged and a retry converges to the same
    projection.
    """

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

        point = AnalyticMeasurementPoint(
            account_id=account_id,
            patient_id=projection["patientId"],
            measurement_kind=projection["kind"],
            measured_at=datetime.fromisoformat(str(projection["measuredAt"]).replace("Z", "+00:00")),
            source_measurement_id=UUID(measurement_id),
            source_version=projection.get("version", 1),
            value=projection.get("value"),
            systolic_value=projection.get("systolicValue"),
            diastolic_value=projection.get("diastolicValue"),
            unit=projection["unit"],
            change_seq=row.sequence,
        )
        await dao_analytic_points.replace_for_source(
            db, account_id, point.source_measurement_id, point
        )
        processed += 1
        max_seq = max(max_seq, row.sequence)

    if max_seq > cursor:
        await dao_analytic_etl_state.advance(db, account_id, max_seq, await _server_time(db))

    return processed


async def rebuild_analytics(db: AsyncSession) -> int:
    """Rebuild projections from scratch; converges to the same result."""

    await dao_analytic_points.clear(db)
    await db.execute(AnalyticEtlState.__table__.delete())

    from src.api.sync.repository.models import ChangeLog

    account_rows = await db.scalars(select(ChangeLog.account_id).distinct())

    total = 0
    for account_id in account_rows:
        while True:
            processed = await run_etl(db, account_id)
            total += processed
            if processed < 500:
                break

    return total
