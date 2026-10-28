from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import bounded_body, no_query_parameters, request_correlation_id
from src.api.sync.application.operations_cases import get_operation, submit_batch
from src.api.sync.domain.errors import OperationNotFound, ResultExpired
from src.api.sync.domain.operations import (
    OperationBatch,
    OperationBatchResult,
    OperationResult,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/accounts/{account_id}/sync",
    tags=["sync"],
    dependencies=[Depends(no_query_parameters)],
    responses={
        code: {"model": ApiError} for code in (401, 403, 404, 410, 413, 422, 503)
    },
)
bearer = HTTPBearer(auto_error=False)


@router.post(
    "/operations",
    operation_id="submitOperations",
    dependencies=[Depends(bounded_body)],
    response_model_exclude_unset=True,
)
async def accept_operations(
    account_id: UUID7,
    obj_in: OperationBatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    correlation_id: Annotated[UUID7, Depends(request_correlation_id)],
) -> OperationBatchResult:
    if any(
        len(item.model_dump_json(by_alias=True).encode("utf-8")) > 64 * 1024
        for item in obj_in.operations
    ):
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE)

    result = await submit_batch(
        db,
        authorization.credentials if authorization else None,
        account_id,
        obj_in,
        correlation_id,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case Err(ResultExpired()):
            raise HTTPException(status.HTTP_410_GONE)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/operations/{operation_id}",
    operation_id="getOperation",
    response_model_exclude_unset=True,
)
async def read_operation(
    account_id: UUID7,
    operation_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperationResult:
    result = await get_operation(
        db,
        authorization.credentials if authorization else None,
        account_id,
        operation_id,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case Err(AccountNotFound() | OperationNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case Err(ResultExpired()):
            raise HTTPException(status.HTTP_410_GONE)
        case unexpected:
            assert_never(unexpected)
