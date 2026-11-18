from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.diagnostic_results.application.report_cases import (
    attachment_response,
    report_response,
    result_response,
)
from src.api.diagnostic_results.repository.dao import (
    dao_report_attachments,
    dao_report_results,
    dao_reports,
)
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_diagnostic_reports(
    db: AsyncSession, context: AccountContext
) -> list[SyncItem]:
    account_id = context.account.id
    items: list[SyncItem] = []

    for report in await dao_reports.valid_snapshot(db, account_id):
        items.append(
            SyncItem(
                entity_type="diagnostic_report",
                entity_key=report.id,
                entity_version=report.version,
                state=report_response(report),
            )
        )
        for result in await dao_report_results.for_report(db, account_id, report.id):
            if result.record_status != "valid":
                continue
            items.append(
                SyncItem(
                    entity_type="diagnostic_report_result",
                    entity_key=result.id,
                    entity_version=result.version,
                    state=result_response(result),
                )
            )

    for attachment in await dao_report_attachments.valid_snapshot(db, account_id):
        items.append(
            SyncItem(
                entity_type="report_attachment",
                entity_key=attachment.id,
                entity_version=attachment.version,
                state=attachment_response(attachment),
            )
        )

    return items
