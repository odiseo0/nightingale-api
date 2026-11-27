from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.domain.errors import (
    AccessDenied,
    IdentityProviderUnavailable,
    InvalidCredential,
)
from src.api.subscriptions.application.operator_cases import (
    OperatorNotFound,
    OperatorRevoked,
    create_operator,
    issue_operator_credential,
    list_operators,
    recover_operator_credential,
    revoke_operator_by_id,
)
from src.api.subscriptions.domain.operators import (
    OperatorCreateRequest,
    OperatorPage,
    OperatorResponse,
    OperatorTokenIssued,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery

router = APIRouter(
    prefix="/v1/operator",
    tags=["operator-subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.post("/credentials", operation_id="issueOperatorCredential", status_code=201)
async def issue_credential(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorTokenIssued:
    result = await issue_operator_credential(
        db, authorization.credentials if authorization else None
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential() | OperatorRevoked()):
            raise HTTPException(401)
        case Err(OperatorNotFound()):
            raise HTTPException(404)
        case Err(IdentityProviderUnavailable()):
            raise HTTPException(503)
        case unexpected:
            assert_never(unexpected)


@router.get("/operators", operation_id="listPlatformOperators")
async def list_platform_operators(
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorPage:
    result = await list_operators(
        db, authorization.credentials if authorization else None, query.page, query.shows
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case unexpected:
            assert_never(unexpected)


@router.post("/operators", operation_id="createPlatformOperator", status_code=201)
async def create_platform_operator(
    payload: OperatorCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorResponse:
    result = await create_operator(
        db, authorization.credentials if authorization else None, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case unexpected:
            assert_never(unexpected)


@router.post("/operators/{operator_id}/revocation", operation_id="revokePlatformOperator")
async def revoke_platform_operator(
    operator_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorResponse:
    result = await revoke_operator_by_id(
        db, authorization.credentials if authorization else None, operator_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(OperatorNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/operators/{operator_id}/credential-recovery",
    operation_id="recoverPlatformOperatorCredential",
    status_code=201,
)
async def recover_platform_operator_credential(
    operator_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorTokenIssued:
    result = await recover_operator_credential(
        db, authorization.credentials if authorization else None, operator_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(OperatorNotFound()):
            raise HTTPException(404)
        case Err(OperatorRevoked()):
            raise HTTPException(409, detail="INVALID_STATE_TRANSITION")
        case unexpected:
            assert_never(unexpected)
