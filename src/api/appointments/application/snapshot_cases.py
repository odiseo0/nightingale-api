from __future__ import annotations

from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.appointments.application.appointments_cases import (
    appointment_response,
    captured_history,
)
from src.api.appointments.domain.appointments import (
    AppointmentQuery,
    AppointmentResponse,
)
from src.api.appointments.repository.dao import dao_appointments
from src.api.sync.domain.downloads import SyncItem, SyncWindow

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_appointments(
    db: AsyncSession, context: AccountContext, window: SyncWindow
) -> list[SyncItem]:
    items: list[SyncItem] = []
    page = 1

    while True:
        query = AppointmentQuery.model_validate(
            {
                "from": window.starts_at,
                "until": window.ends_at,
                "page": page,
                "shows": 500,
            }
        )
        rows, total = await dao_appointments.page(db, context.account.id, query)

        for row in rows:
            state = AppointmentResponse.model_validate(appointment_response(row))
            history = await captured_history(db, state)
            items.append(
                SyncItem(
                    entity_type="appointment",
                    entity_key=row.id,
                    entity_version=row.version,
                    state=state,
                )
            )
            items.append(
                SyncItem(
                    entity_type="appointment_history",
                    entity_key=row.id,
                    entity_version=row.version,
                    state=history,
                )
            )

        if page * query.shows >= total:
            break

        page += 1

    return items
