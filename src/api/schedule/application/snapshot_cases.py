from __future__ import annotations

from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.schedule.application.blocks_cases import block_response
from src.api.schedule.domain.schedule import (
    ScheduleBlockQuery,
    ScheduleBlockResponse,
    ScheduleExceptionResponse,
    ScheduleRuleResponse,
)
from src.api.schedule.repository.dao import dao_blocks, dao_exceptions, dao_rules
from src.api.sync.domain.downloads import SyncItem, SyncWindow

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_schedule(
    db: AsyncSession, context: AccountContext, window: SyncWindow
) -> list[SyncItem]:
    account_id = context.account.id
    items: list[SyncItem] = []
    rules, _ = await dao_rules.get_multi(
        db, where={"account_id": account_id}, ordering=[("id", False)], shows=None
    )
    items.extend(
        SyncItem(
            entity_type="schedule_rule",
            entity_key=row.id,
            entity_version=row.version,
            state=ScheduleRuleResponse.model_validate(row),
        )
        for row in rules
        if row.valid_from < window.appointments_until
        and (row.valid_until is None or window.appointments_from <= row.valid_until)
    )
    exceptions, _ = await dao_exceptions.get_multi(
        db, where={"account_id": account_id}, ordering=[("id", False)], shows=None
    )
    items.extend(
        SyncItem(
            entity_type="schedule_exception",
            entity_key=row.id,
            entity_version=row.version,
            state=ScheduleExceptionResponse.model_validate(row),
        )
        for row in exceptions
        if window.appointments_from <= row.local_date < window.appointments_until
    )
    page = 1

    while True:
        query = ScheduleBlockQuery.model_validate(
            {
                "from": window.starts_at,
                "until": window.ends_at,
                "page": page,
                "shows": 500,
            }
        )
        blocks, total = await dao_blocks.page(db, account_id, query)
        items.extend(
            SyncItem(
                entity_type="schedule_block",
                entity_key=row.id,
                entity_version=row.version,
                state=ScheduleBlockResponse.model_validate(
                    block_response(row, reveal_reason=row.account_id == account_id)
                ),
            )
            for row in blocks
        )

        if page * query.shows >= total:
            break

        page += 1

    return items
