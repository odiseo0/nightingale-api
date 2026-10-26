from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.application.invitations_cases import get_invitations
from src.api.accounts.domain.accounts import (
    InvitationAcceptanceResult,
    InvitationAcceptRequest,
    InvitationQuery,
    InvitationResponse,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
)
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters, request_correlation_id
from src.api.sync.application.operations_cases import accept_invitation
from src.api.sync.domain.errors import ResultExpired
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    prefix="/v1",
    tags=["invitations"],
    responses={
        code: {"model": ApiError} for code in (401, 403, 404, 409, 410, 422, 503)
    },
)
bearer = HTTPBearer(auto_error=False)


@router.get("/me/invitations", operation_id="listOwnInvitations")
async def read_own_invitations(
    query: Annotated[InvitationQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[InvitationResponse]:
    result = await get_invitations(
        db, authorization.credentials if authorization else None, query
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case unexpected:
            assert_never(unexpected)


@router.get("/accounts/{account_id}/invitations", operation_id="listAccountInvitations")
async def read_account_invitations(
    account_id: UUID7,
    query: Annotated[InvitationQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[InvitationResponse]:
    result = await get_invitations(
        db, authorization.credentials if authorization else None, query, account_id
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


@router.post(
    "/me/invitations/{invitation_id}/accept",
    operation_id="acceptInvitation",
    dependencies=[Depends(no_query_parameters)],
)
async def accept_own_invitation(
    invitation_id: UUID7,
    obj_in: InvitationAcceptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    correlation_id: Annotated[UUID7, Depends(request_correlation_id)],
) -> InvitationAcceptanceResult:
    result = await accept_invitation(
        db,
        authorization.credentials if authorization else None,
        invitation_id,
        obj_in.operation_id,
        correlation_id,
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
        case Err(ResultExpired()):
            raise HTTPException(410)
        case Err(AccountRuleError(code, _)):
            raise HTTPException(409, detail=code)
        case unexpected:
            assert_never(unexpected)
