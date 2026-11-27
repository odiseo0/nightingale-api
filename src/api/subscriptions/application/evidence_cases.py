import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import get_account_context
from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.domain.reports import (
    EVIDENCE_MAX_BYTES,
    detect_content_type,
)
from src.api.subscriptions.repository.dao import (
    dao_payment_reports,
    dao_report_evidence,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.services import report_storage
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
class EvidenceRejected:
    reason: str


@dataclass(frozen=True, slots=True)
class EvidenceNotFound:
    pass


StoreError = (
    ReportNotFound | ReportNotPending | EvidenceAlreadyPresent | EvidenceRejected
)
UploadError = InvalidCredential | AccountNotFound | AccessDenied | StoreError


def _check_content(content: bytes) -> Result[tuple[str, str], EvidenceRejected]:
    if len(content) == 0 or len(content) > EVIDENCE_MAX_BYTES:
        return Err(EvidenceRejected("invalid_size"))

    content_type = detect_content_type(content)

    if content_type is None:
        return Err(EvidenceRejected("invalid_type"))

    return Ok((content_type, hashlib.sha256(content).hexdigest()))


async def _report_state(
    db: AsyncSession, account_id: UUID, report_id: UUID, *, lock: bool
) -> Result[None, ReportNotFound | ReportNotPending | EvidenceAlreadyPresent]:
    report = await dao_payment_reports.for_account(db, report_id, account_id, lock=lock)

    if report is Empty:
        return Err(ReportNotFound())

    if report.status != "pending":
        return Err(ReportNotPending())

    if (await dao_report_evidence.by_report(db, report_id)) is not Empty:
        return Err(EvidenceAlreadyPresent())

    return Ok(None)


async def _save_and_insert(
    db: AsyncSession,
    account_id: UUID,
    report_id: UUID,
    uploader_id: UUID,
    content: bytes,
) -> Result[UUID, StoreError]:
    checked = _check_content(content)

    match checked:
        case Err(error):
            return Err(error)
        case Ok((content_type, digest)):
            pass

    evidence_id = uuid7()
    # Storage happens before the metadata row and outside the transaction; a
    # failed insert leaves an orphan file without any commercial effect (§13.3).
    storage_key = await report_storage.save(account_id, evidence_id, content)

    async with transaction(db):
        state = await _report_state(db, account_id, report_id, lock=True)

        if isinstance(state, Err):
            return state

        await dao_report_evidence.create(
            db,
            commit=False,
            obj_in={
                "id": evidence_id,
                "report_id": report_id,
                "storage_key": storage_key,
                "content_type": content_type,
                "size_bytes": len(content),
                "sha256": digest,
                "uploaded_by": uploader_id,
            },
        )

    return Ok(evidence_id)


async def store_evidence(
    db: AsyncSession,
    account_id: UUID,
    report_id: UUID,
    uploader_id: UUID,
    content: bytes,
) -> Result[UUID, StoreError]:
    """Validate and store one capture per report (D24); bytes never enter the
    database, the journal or logs (§13)."""
    return await _save_and_insert(db, account_id, report_id, uploader_id, content)


async def upload_evidence(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    report_id: UUID,
    content: bytes,
) -> Result[UUID, UploadError]:
    # Authorization and the early check share one short transaction; the byte
    # write and the final insert follow the same rules as store_evidence.
    async with transaction(db):
        context = await get_account_context(
            db, credential, account_id, require_device=True
        )

        match context:
            case Err(error):
                return Err(error)
            case Ok(account):
                pass

        if not account.owner:
            return Err(AccessDenied())

        state = await _report_state(db, account_id, report_id, lock=False)

        if isinstance(state, Err):
            return state

    return await _save_and_insert(
        db, account_id, report_id, account.actor.user_id, content
    )


async def read_evidence(
    db: AsyncSession, account_id: UUID, report_id: UUID
) -> Result[tuple[str, bytes], ReportNotFound | EvidenceNotFound]:
    """Download re-authorizes at the route; knowing the storage key grants nothing (§13.2)."""
    report = await dao_payment_reports.for_account(db, report_id, account_id)

    if report is Empty:
        return Err(ReportNotFound())

    evidence = await dao_report_evidence.by_report(db, report_id)

    if evidence is Empty:
        return Err(EvidenceNotFound())

    try:
        content = await report_storage.fetch(evidence.storage_key)
    except report_storage.StorageError:
        return Err(EvidenceNotFound())

    return Ok((evidence.content_type, content))
