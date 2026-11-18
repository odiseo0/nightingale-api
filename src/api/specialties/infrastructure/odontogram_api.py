from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.errors import no_query_parameters
from src.api.specialties.application.odontogram_cases import (
    read_dental_finding_history,
    read_dental_findings,
    read_dental_treatment_for_patient,
    read_dental_treatment_history,
    read_dental_treatments,
)
from src.api.specialties.domain.odontogram import (
    DentalFindingHistoryResponse,
    DentalFindingQuery,
    DentalFindingResponse,
    DentalTreatmentHistoryResponse,
    DentalTreatmentResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-dental"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


def _raise(result):
    match result:
        case Ok(value):
            return value
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get("/dental-findings", operation_id="listDentalFindings")
async def list_findings(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[DentalFindingQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DentalFindingResponse]:
    return _raise(
        await read_dental_findings(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            query,
        )
    )


@router.get(
    "/dental-findings/{finding_id}",
    operation_id="getDentalFinding",
    dependencies=[Depends(no_query_parameters)],
)
async def get_finding(
    account_id: UUID7,
    patient_id: UUID7,
    finding_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> DentalFindingResponse:
    return _raise(
        await read_dental_findings(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            PageQuery(),
            finding_id,
        )
    )


@router.get("/dental-findings/{finding_id}/history", operation_id="listDentalFindingHistory")
async def list_finding_history(
    account_id: UUID7,
    patient_id: UUID7,
    finding_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DentalFindingHistoryResponse]:
    return _raise(
        await read_dental_finding_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            finding_id,
            query,
        )
    )


@router.get(
    "/dental-findings/{finding_id}/treatments",
    operation_id="listDentalTreatments",
    dependencies=[Depends(no_query_parameters)],
)
async def list_treatments(
    account_id: UUID7,
    patient_id: UUID7,
    finding_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DentalTreatmentResponse]:
    return _raise(
        await read_dental_treatments(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            finding_id,
        )
    )


@router.get(
    "/dental-treatments/{treatment_id}",
    operation_id="getDentalTreatment",
    dependencies=[Depends(no_query_parameters)],
)
async def get_treatment(
    account_id: UUID7,
    patient_id: UUID7,
    treatment_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> DentalTreatmentResponse:
    return _raise(
        await read_dental_treatment_for_patient(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            treatment_id,
        )
    )


@router.get(
    "/dental-treatments/{treatment_id}/history",
    operation_id="listDentalTreatmentHistory",
)
async def list_treatment_history(
    account_id: UUID7,
    patient_id: UUID7,
    treatment_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DentalTreatmentHistoryResponse]:
    return _raise(
        await read_dental_treatment_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            treatment_id,
            query,
        )
    )
