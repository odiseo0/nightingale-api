from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.appointments.application.appointments_cases import read_appointments
from src.api.appointments.domain.appointments import (
    AppointmentHistoryQuery,
    AppointmentHistoryResponse,
    AppointmentQuery,
    AppointmentResponse,
)
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/appointments",
    tags=["appointments"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "",
    operation_id="listAppointments",
    response_model=PaginatedResponse[AppointmentResponse],
)
async def list_appointments(
    account_id: UUID7,
    query: Annotated[AppointmentQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_appointments(
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
    "/{appointment_id}",
    operation_id="getAppointment",
    response_model=AppointmentResponse,
    dependencies=[Depends(no_query_parameters)],
)
async def get_appointment(
    account_id: UUID7,
    appointment_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_appointments(
        db,
        authorization.credentials if authorization else None,
        account_id,
        appointment_id=appointment_id,
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
    "/{appointment_id}/history",
    operation_id="getAppointmentHistory",
    response_model=PaginatedResponse[AppointmentHistoryResponse],
)
async def get_appointment_history(
    account_id: UUID7,
    appointment_id: UUID7,
    query: Annotated[AppointmentHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_appointments(
        db,
        authorization.credentials if authorization else None,
        account_id,
        appointment_id=appointment_id,
        history_query=query,
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
