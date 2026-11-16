from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.measurements_cases import (
    read_measurement_history,
    read_measurement_summary,
    read_measurements,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.measurements import (
    MeasurementQuery,
    MeasurementSummaryResponse,
    PatientMeasurementHistoryResponse,
    PatientMeasurementResponse,
)
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-measurements"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/measurements", operation_id="listPatientMeasurements")
async def list_measurements(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[MeasurementQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientMeasurementResponse]:
    result = await read_measurements(
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
    "/measurements/summary",
    operation_id="getPatientMeasurementSummary",
    dependencies=[Depends(no_query_parameters)],
)
async def get_measurement_summary(
    account_id: UUID7,
    patient_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> MeasurementSummaryResponse:
    result = await read_measurement_summary(
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


@router.get(
    "/measurements/{measurement_id}",
    operation_id="getPatientMeasurement",
    dependencies=[Depends(no_query_parameters)],
)
async def get_measurement(
    account_id: UUID7,
    patient_id: UUID7,
    measurement_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientMeasurementResponse:
    result = await read_measurements(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        measurement_id,
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
    "/measurements/{measurement_id}/history",
    operation_id="listPatientMeasurementHistory",
)
async def list_measurement_history(
    account_id: UUID7,
    patient_id: UUID7,
    measurement_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientMeasurementHistoryResponse]:
    result = await read_measurement_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        measurement_id,
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
