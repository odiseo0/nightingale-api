from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.analytics.application.clinical_cases import read_series
from src.api.analytics.application.growth_cases import GrowthResponse, read_growth
from src.api.analytics.domain.references import Indicator
from src.api.analytics.domain.queries import SeriesQuery, SeriesResponse
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-analytics"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/analytics/series", operation_id="getPatientMeasurementSeries")
async def get_series(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[SeriesQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SeriesResponse:
    result = await read_series(
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


@router.get("/analytics/growth", operation_id="getPatientGrowth")
async def get_growth(
    account_id: UUID7,
    patient_id: UUID7,
    indicator: Indicator,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> GrowthResponse:
    result = await read_growth(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        indicator,
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
