from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.immunizations_cases import (
    read_immunization_history,
    read_immunizations,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.immunizations import (
    ImmunizationQuery,
    PatientImmunizationHistoryResponse,
    PatientImmunizationResponse,
)
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-immunizations"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/immunizations", operation_id="listPatientImmunizations")
async def list_immunizations(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[ImmunizationQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientImmunizationResponse]:
    result = await read_immunizations(
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
    "/immunizations/{immunization_id}",
    operation_id="getPatientImmunization",
    dependencies=[Depends(no_query_parameters)],
)
async def get_immunization(
    account_id: UUID7,
    patient_id: UUID7,
    immunization_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientImmunizationResponse:
    result = await read_immunizations(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        immunization_id,
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
    "/immunizations/{immunization_id}/history",
    operation_id="listPatientImmunizationHistory",
)
async def list_immunization_history(
    account_id: UUID7,
    patient_id: UUID7,
    immunization_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientImmunizationHistoryResponse]:
    result = await read_immunization_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        immunization_id,
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
