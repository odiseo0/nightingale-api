from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.antecedents_cases import (
    read_antecedent_history,
    read_antecedents,
)
from src.api.clinical_records.domain.antecedents import (
    AntecedentQuery,
    PatientAntecedentHistoryResponse,
    PatientAntecedentResponse,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-antecedents"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/antecedents", operation_id="listPatientAntecedents")
async def list_antecedents(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[AntecedentQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientAntecedentResponse]:
    result = await read_antecedents(
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
    "/antecedents/{antecedent_id}",
    operation_id="getPatientAntecedent",
    dependencies=[Depends(no_query_parameters)],
)
async def get_antecedent(
    account_id: UUID7,
    patient_id: UUID7,
    antecedent_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientAntecedentResponse:
    result = await read_antecedents(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        antecedent_id,
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
    "/antecedents/{antecedent_id}/history", operation_id="listPatientAntecedentHistory"
)
async def list_antecedent_history(
    account_id: UUID7,
    patient_id: UUID7,
    antecedent_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientAntecedentHistoryResponse]:
    result = await read_antecedent_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        antecedent_id,
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
