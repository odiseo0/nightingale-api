from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.errors import no_query_parameters
from src.api.medications.application.medication_cases import (
    read_declared_medication_history,
    read_declared_medications,
)
from src.api.medications.domain.medications import (
    DeclaredMedicationHistoryResponse,
    DeclaredMedicationQuery,
    DeclaredMedicationResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-declared-medications"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/declared-medications", operation_id="listPatientDeclaredMedications")
async def list_declared_medications(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[DeclaredMedicationQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DeclaredMedicationResponse]:
    result = await read_declared_medications(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        query,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/declared-medications/{medication_id}",
    operation_id="getPatientDeclaredMedication",
    dependencies=[Depends(no_query_parameters)],
)
async def get_declared_medication(
    account_id: UUID7,
    patient_id: UUID7,
    medication_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> DeclaredMedicationResponse:
    result = await read_declared_medications(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        medication_id,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/declared-medications/{medication_id}/history",
    operation_id="listPatientDeclaredMedicationHistory",
)
async def list_declared_medication_history(
    account_id: UUID7,
    patient_id: UUID7,
    medication_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DeclaredMedicationHistoryResponse]:
    result = await read_declared_medication_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        medication_id,
        query,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
