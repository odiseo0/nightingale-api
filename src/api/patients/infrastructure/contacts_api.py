from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.api.patients.application.contacts_cases import read_contacts
from src.api.patients.domain.contacts import (
    ContactQuery,
    ContactResponse,
    PatientContactResponse,
    RelationshipQuery,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}",
    tags=["patients"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/contacts", operation_id="listContacts")
async def list_contacts(
    account_id: UUID7,
    query: Annotated[ContactQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[ContactResponse]:
    result = await read_contacts(
        db, authorization.credentials if authorization else None, account_id, query
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
    "/contacts/{contact_id}",
    operation_id="getContact",
    dependencies=[Depends(no_query_parameters)],
)
async def get_contact(
    account_id: UUID7,
    contact_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ContactResponse:
    result = await read_contacts(
        db,
        authorization.credentials if authorization else None,
        account_id,
        ContactQuery(),
        contact_id=contact_id,
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


@router.get("/contacts/{contact_id}/patients", operation_id="listContactPatients")
async def list_contact_patients(
    account_id: UUID7,
    contact_id: UUID7,
    query: Annotated[RelationshipQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientContactResponse]:
    result = await read_contacts(
        db,
        authorization.credentials if authorization else None,
        account_id,
        query,
        contact_id=contact_id,
        relationships=True,
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


@router.get("/patients/{patient_id}/contacts", operation_id="listPatientContacts")
async def list_patient_contacts(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[RelationshipQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[PatientContactResponse]:
    result = await read_contacts(
        db,
        authorization.credentials if authorization else None,
        account_id,
        query,
        patient_id=patient_id,
        relationships=True,
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
