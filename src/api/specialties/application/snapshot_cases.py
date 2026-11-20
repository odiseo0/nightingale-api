from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext
from src.api.specialties.application.odontogram_cases import (
    finding_response,
    treatment_response,
)
from src.api.specialties.application.template_cases import (
    record_response,
    template_response,
)
from src.api.specialties.repository.dao import (
    dao_specialty_records,
    dao_templates,
)
from src.api.specialties.repository.specialty_dao import (
    dao_dental_findings,
    dao_dental_treatments,
)
from src.api.sync.domain.downloads import SyncItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_specialty_templates(
    db: AsyncSession, context: AccountContext
) -> list[SyncItem]:
    account_id = context.account.id
    items: list[SyncItem] = []

    records = await dao_specialty_records.valid_snapshot(db, account_id)
    required = {(record.template_id, record.template_version) for record in records}
    for template in await dao_templates.for_snapshot(db, account_id, required):
        items.append(
            SyncItem(
                entity_type="specialty_template",
                entity_key={"templateId": template.id, "version": str(template.version)},
                entity_version=template.version,
                state=await template_response(db, template),
            )
        )

    for record in records:
        items.append(
            SyncItem(
                entity_type="specialty_record",
                entity_key=record.id,
                entity_version=record.version,
                state=await record_response(db, record),
            )
        )

    for finding in await dao_dental_findings.valid_snapshot(db, account_id):
        items.append(
            SyncItem(
                entity_type="dental_finding",
                entity_key=finding.id,
                entity_version=finding.version,
                state=finding_response(finding),
            )
        )

    for treatment in await dao_dental_treatments.valid_snapshot(db, account_id):
        items.append(
            SyncItem(
                entity_type="dental_treatment",
                entity_key=treatment.id,
                entity_version=treatment.version,
                state=treatment_response(treatment),
            )
        )

    return items
