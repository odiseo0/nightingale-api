from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.billing.domain.payments import EVIDENCE_MAX_BYTES
from src.api.billing.repository.dao import dao_evidence, dao_reports
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.services import report_storage
from src.core.services.private_evidence import EvidenceRejected, validate_capture
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class ReportNotFound:
    pass


@dataclass(frozen=True, slots=True)
class ReportNotPending:
    pass


@dataclass(frozen=True, slots=True)
class EvidenceAlreadyPresent:
    pass


@dataclass(frozen=True, slots=True)
class EvidenceNotFound:
    pass


StoreError = (
    ReportNotFound | ReportNotPending | EvidenceAlreadyPresent | EvidenceRejected
)


async def _report_state(
    db: AsyncSession, account_id: UUID, report_id: UUID, *, lock: bool
) -> Result[None, ReportNotFound | ReportNotPending | EvidenceAlreadyPresent]:
    report = (
        await dao_reports.by_id_for_update(db, report_id, account_id)
        if lock
        else await dao_reports.by_id_in_account(db, report_id, account_id)
    )

    if report is Empty:
        return Err(ReportNotFound())

    if report.status != "pending":
        return Err(ReportNotPending())

    if (await dao_evidence.by_report(db, report_id)) is not Empty:
        return Err(EvidenceAlreadyPresent())

    return Ok(None)


async def store_report_evidence(
    db: AsyncSession, account_id: UUID, report_id: UUID, content: bytes
) -> Result[UUID, StoreError]:
    """One capture per patient payment report (D28 reuses D24); bytes never enter
    the database, the journal or logs. The file is written before the metadata
    row, outside the transaction: a failed insert leaves an orphan file without
    any financial effect (§11.1)."""
    checked = validate_capture(content, EVIDENCE_MAX_BYTES)

    if isinstance(checked, Err):
        return checked

    content_type, digest = checked.value
    evidence_id = uuid7()
    storage_key = await report_storage.save(account_id, evidence_id, content)

    async with transaction(db):
        state = await _report_state(db, account_id, report_id, lock=True)

        if isinstance(state, Err):
            return state

        await dao_evidence.insert_evidence(
            db,
            {
                "id": evidence_id,
                "report_id": report_id,
                "storage_key": storage_key,
                "content_type": content_type,
                "size_bytes": len(content),
                "sha256": digest,
            },
        )

    return Ok(evidence_id)


async def read_report_evidence(
    db: AsyncSession, account_id: UUID, report_id: UUID
) -> Result[tuple[str, bytes], ReportNotFound | EvidenceNotFound]:
    """Download re-authorizes at the route; knowing the storage key grants nothing."""
    report = await dao_reports.by_id_in_account(db, report_id, account_id)

    if report is Empty:
        return Err(ReportNotFound())

    evidence = await dao_evidence.by_report(db, report_id)

    if evidence is Empty:
        return Err(EvidenceNotFound())

    try:
        content = await report_storage.fetch(evidence.storage_key)
    except report_storage.StorageError:
        return Err(EvidenceNotFound())

    return Ok((evidence.content_type, content))
