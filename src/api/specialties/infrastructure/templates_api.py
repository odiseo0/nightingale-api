from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.errors import no_query_parameters
from src.api.specialties.application.template_cases import (
    read_specialty_record_history,
    read_specialty_records,
    read_template_history,
    read_templates,
)
from src.api.specialties.domain.records import (
    SpecialtyRecordHistoryResponse,
    SpecialtyRecordQuery,
    SpecialtyRecordResponse,
)
from src.api.specialties.domain.templates import (
    SpecialtyTemplateHistoryResponse,
    SpecialtyTemplateQuery,
    SpecialtyTemplateResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}",
    tags=["clinical-specialty-templates"],
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


@router.get("/specialty-templates", operation_id="listSpecialtyTemplates")
async def list_templates(
    account_id: UUID7,
    query: Annotated[SpecialtyTemplateQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[SpecialtyTemplateResponse]:
    return _raise(
        await read_templates(
            db,
            authorization.credentials if authorization else None,
            account_id,
            query,
        )
    )


@router.get(
    "/specialty-templates/{template_id}",
    operation_id="getSpecialtyTemplate",
    dependencies=[Depends(no_query_parameters)],
)
async def get_template(
    account_id: UUID7,
    template_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SpecialtyTemplateResponse:
    return _raise(
        await read_templates(
            db,
            authorization.credentials if authorization else None,
            account_id,
            PageQuery(),
            template_id,
        )
    )


@router.get(
    "/specialty-templates/{template_id}/history",
    operation_id="listSpecialtyTemplateHistory",
)
async def list_template_history(
    account_id: UUID7,
    template_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[SpecialtyTemplateHistoryResponse]:
    return _raise(
        await read_template_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            template_id,
            query,
        )
    )


@router.get(
    "/patients/{patient_id}/specialty-records",
    operation_id="listSpecialtyRecords",
)
async def list_records(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[SpecialtyRecordQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[SpecialtyRecordResponse]:
    return _raise(
        await read_specialty_records(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            query,
        )
    )


@router.get(
    "/patients/{patient_id}/specialty-records/{record_id}",
    operation_id="getSpecialtyRecord",
    dependencies=[Depends(no_query_parameters)],
)
async def get_record(
    account_id: UUID7,
    patient_id: UUID7,
    record_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SpecialtyRecordResponse:
    return _raise(
        await read_specialty_records(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            PageQuery(),
            record_id,
        )
    )


@router.get(
    "/patients/{patient_id}/specialty-records/{record_id}/history",
    operation_id="listSpecialtyRecordHistory",
)
async def list_record_history(
    account_id: UUID7,
    patient_id: UUID7,
    record_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[SpecialtyRecordHistoryResponse]:
    return _raise(
        await read_specialty_record_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            record_id,
            query,
        )
    )
