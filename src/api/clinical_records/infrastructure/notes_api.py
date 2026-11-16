from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.notes_cases import (
    read_note_history,
    read_notes,
)
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.clinical_records.domain.notes import (
    NoteQuery,
    PatientNoteHistoryResponse,
    PatientNoteResponse,
)
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-notes"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/notes", operation_id="listPatientNotes")
async def list_notes(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[NoteQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientNoteResponse]:
    result = await read_notes(
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
    "/notes/{note_id}",
    operation_id="getPatientNote",
    dependencies=[Depends(no_query_parameters)],
)
async def get_note(
    account_id: UUID7,
    patient_id: UUID7,
    note_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientNoteResponse:
    result = await read_notes(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        PageQuery(),
        note_id,
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


@router.get("/notes/{note_id}/history", operation_id="listPatientNoteHistory")
async def list_note_history(
    account_id: UUID7,
    patient_id: UUID7,
    note_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientNoteHistoryResponse]:
    result = await read_note_history(
        db,
        authorization.credentials if authorization else None,
        account_id,
        patient_id,
        note_id,
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
