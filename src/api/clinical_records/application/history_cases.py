from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.accounts_cases import (
    get_account_context,
    readable_clinical_sections,
)
from src.api.accounts.domain.errors import AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied
from src.api.clinical_records.application.access_cases import record_clinical_read
from src.api.clinical_records.domain.history import (
    ClinicalHistoryEntry,
    ClinicalHistoryQuery,
)
from src.api.clinical_records.repository.dao import dao_clinical_timeline
from src.api.patients.application.patients_cases import clinical_patient
from src.core import Err, Ok
from src.core.db import transaction
from src.core.schema import PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def read_clinical_history(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    patient_id: UUID,
    query: ClinicalHistoryQuery,
):
    async with transaction(db):
        scope = await get_account_context(db, credential, account_id, True)

        if isinstance(scope, Err):
            return scope

        if scope.value.account.status != "active":
            return Err(AccessDenied())

        if await clinical_patient(db, account_id, patient_id) is Empty:
            return Err(AccountObjectNotFound())

        allowed = readable_clinical_sections(scope.value)
        selected = (
            allowed
            if query.sections is None
            else [section for section in query.sections if section in allowed]
        )

        if selected:
            rows, total = await dao_clinical_timeline.page(
                db,
                account_id,
                patient_id,
                [str(section) for section in selected],
                query,
            )
        else:
            rows, total = [], 0

        response = PaginatedResponse[ClinicalHistoryEntry](
            items=[ClinicalHistoryEntry.model_validate(row) for row in rows],
            total=total,
        )
        await record_clinical_read(
            db,
            scope.value,
            "ReadPatientClinicalHistory",
            "patient_clinical_timeline",
            str(patient_id),
        )

    return Ok(response)
