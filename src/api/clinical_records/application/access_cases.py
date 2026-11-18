from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.domain.accounts import AccountContext, ClinicalSection
from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.accounts.domain.policies import clinical_level_allows, clinical_section_for_action
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.domain.conditions import (
    SetPatientClinicalSectionReviewPayload,
)
from src.api.patients.application.patients_cases import clinical_server_time
from src.core import Err, Result
from src.core.schema import BaseModel, PaginatedResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def clinical_result_section(
    action: str, payload: BaseModel | None
) -> ClinicalSection | None:
    section = payload.section if isinstance(payload, SetPatientClinicalSectionReviewPayload) else None
    return clinical_section_for_action(action, section)


def clinical_result_allowed(
    context: AccountContext, section: ClinicalSection | None
) -> bool:
    return clinical_level_allows(context, section, "read_write")


async def clinical_read_scope(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    section: ClinicalSection,
) -> Result[
    AccountContext,
    InvalidCredential | AccountNotFound | AccountObjectNotFound | AccessDenied,
]:
    identity = await authenticate(db, credential)

    if isinstance(identity, Err):
        return identity

    scope = await account_context(db, identity.value, account_id, require_device=True)

    if isinstance(scope, Err):
        return scope

    if (
        scope.value.account.status != "active"
        or not clinical_level_allows(scope.value, section, "read")
    ):
        return Err(AccessDenied())

    return scope


async def record_clinical_read(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    object_type: str,
    object_key: str,
) -> None:
    await record_control(
        db,
        ControlAudit(
            account_id=context.account.id,
            actor_user_id=context.actor.user_id,
            actor_device_id=context.actor.device_id,
            action=action,
            object_type=object_type,
            object_key=object_key,
            outcome="accepted",
            correlation_id=uuid7(),
            occurred_at=await clinical_server_time(db),
        ),
    )


def clinical_page[Row, Response: BaseModel](
    rows: Iterable[Row], total: int, project: Callable[[Row], Response]
) -> PaginatedResponse[Response]:
    return PaginatedResponse[Response](
        items=[project(row) for row in rows], total=total
    )
