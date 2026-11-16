from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.allergies_cases import (
    read_allergies,
    read_allergy_history,
    read_allergy_review,
)
from src.api.clinical_records.domain.allergies import (
    AllergyQuery,
    PatientAllergyIntoleranceHistoryResponse,
    PatientAllergyIntoleranceResponse,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewHistoryResponse,
    ClinicalSectionReviewResponse,
)
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-allergies"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/allergy-intolerances", operation_id="listPatientAllergies")
async def list_allergies(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[AllergyQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientAllergyIntoleranceResponse]:
    result = await read_allergies(
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
    "/allergy-intolerances/{allergy_id}",
    operation_id="getPatientAllergy",
    dependencies=[Depends(no_query_parameters)],
)
async def get_allergy(
    account_id: UUID7,
    patient_id: UUID7,
    allergy_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientAllergyIntoleranceResponse:
    result = await read_allergies(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        allergy_id,
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
    "/allergy-intolerances/{allergy_id}/history",
    operation_id="listPatientAllergyHistory",
)
async def list_allergy_history(
    account_id: UUID7,
    patient_id: UUID7,
    allergy_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientAllergyIntoleranceHistoryResponse]:
    result = await read_allergy_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        allergy_id,
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
    "/clinical-sections/allergies",
    operation_id="getAllergySectionReview",
    dependencies=[Depends(no_query_parameters)],
)
async def get_allergy_section_review(
    account_id: UUID7,
    patient_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ClinicalSectionReviewResponse:
    result = await read_allergy_review(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
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
    "/clinical-sections/allergies/history",
    operation_id="listAllergySectionReviewHistory",
)
async def list_allergy_section_review_history(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[ClinicalSectionReviewHistoryResponse]:
    result = await read_allergy_review(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        query,
        history=True,
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
