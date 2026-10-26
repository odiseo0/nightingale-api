from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.application.accounts_cases import (
    get_access,
    get_account,
    get_accounts,
    get_me,
    get_professional,
)
from src.api.accounts.application.management_cases import get_professionals, get_team
from src.api.accounts.domain.accounts import (
    AccessResponse,
    AccountDeviceResponse,
    AccountResponse,
    AccountSummary,
    MemberResponse,
    MeResponse,
    ProfessionalQuery,
    ProfessionalResponse,
)
from src.api.accounts.domain.errors import AccountNotFound, ProfessionalNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1",
    tags=["accounts"],
    responses={
        401: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
bearer = HTTPBearer(auto_error=False)


@router.get("/me", operation_id="getMe", dependencies=[Depends(no_query_parameters)])
async def read_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> MeResponse:
    result = await get_me(db, authorization.credentials if authorization else None)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/accounts/{account_id}/members",
    operation_id="listAccountMembers",
    responses={403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def read_members(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[MemberResponse]:
    result = await get_team(
        db, authorization.credentials if authorization else None, account_id, query
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/accounts/{account_id}/devices",
    operation_id="listAccountDevices",
    responses={403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def read_account_devices(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[AccountDeviceResponse]:
    result = await get_team(
        db,
        authorization.credentials if authorization else None,
        account_id,
        query,
        devices=True,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/accounts/{account_id}/professionals",
    operation_id="listAccountProfessionals",
    responses={403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def read_professionals(
    account_id: UUID7,
    query: Annotated[ProfessionalQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[ProfessionalResponse]:
    result = await get_professionals(
        db, authorization.credentials if authorization else None, account_id, query
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get("/accounts", operation_id="listAccounts")
async def read_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    query: Annotated[PageQuery, Query()],
) -> PaginatedResponse[AccountSummary]:
    result = await get_accounts(
        db,
        authorization.credentials if authorization else None,
        page=query.page,
        shows=query.shows,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/accounts/{account_id}",
    operation_id="getAccount",
    dependencies=[Depends(no_query_parameters)],
    responses={403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def read_account(
    account_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AccountResponse:
    result = await get_account(
        db, authorization.credentials if authorization else None, account_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case Err(AccountNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/accounts/{account_id}/access",
    operation_id="getAccountAccess",
    dependencies=[Depends(no_query_parameters)],
    responses={403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def read_access(
    account_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AccessResponse:
    result = await get_access(
        db, authorization.credentials if authorization else None, account_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case Err(AccountNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/me/professional",
    operation_id="getOwnProfessional",
    dependencies=[Depends(no_query_parameters)],
    responses={404: {"model": ApiError}},
)
async def read_professional(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ProfessionalResponse:
    result = await get_professional(
        db, authorization.credentials if authorization else None
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(ProfessionalNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case unexpected:
            assert_never(unexpected)
