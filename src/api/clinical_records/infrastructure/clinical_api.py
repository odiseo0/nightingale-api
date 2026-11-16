from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.clinical_cases import (
    read_clinical_history,
    read_clinical_profile,
)
from src.api.clinical_records.domain.clinical import (
    ClinicalHistoryQuery,
    ClinicalProfileHistoryResponse,
    ClinicalProfileResponse,
)
from src.api.errors import no_query_parameters
from src.api.patients.application.patients_cases import read_birth_date_changes
from src.api.patients.domain.patients import PatientBirthDateChangeResponse
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-records"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/clinical-profile",
    operation_id="getClinicalProfile",
    dependencies=[Depends(no_query_parameters)],
)
async def get_clinical_profile(
    account_id: UUID7,
    patient_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ClinicalProfileResponse:
    result = await read_clinical_profile(
        db, authorization.credentials if authorization else None, account_id, patient_id
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


@router.get("/clinical-profile/history", operation_id="listClinicalProfileHistory")
async def list_clinical_profile_history(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[ClinicalProfileHistoryResponse]:
    result = await read_clinical_history(
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


@router.get("/birth-date-changes", operation_id="listBirthDateChanges")
async def list_birth_date_changes(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientBirthDateChangeResponse]:
    result = await read_birth_date_changes(
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
