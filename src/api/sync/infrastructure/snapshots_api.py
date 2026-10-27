from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import bounded_body, no_query_parameters
from src.api.sync.application.snapshot_cases import create_snapshot, get_snapshot, release_snapshot, snapshot_page
from src.api.sync.domain.downloads import SnapshotRequest, SnapshotResponse, SyncItem
from src.api.sync.domain.errors import SyncReadError
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/sync/snapshots", tags=["sync"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 410, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)
error_statuses = {InvalidCredential: 401, AccessDenied: 403, AccountNotFound: 404, AccountObjectNotFound: 404}
sync_statuses = {"DEPENDENCY_UNAVAILABLE": 503, "VALIDATION_ERROR": 422}


@router.post("", operation_id="createSnapshot", status_code=201, response_model=SnapshotResponse,
             dependencies=[Depends(no_query_parameters), Depends(bounded_body)])
async def capture_snapshot(
    account_id: UUID7, obj_in: SnapshotRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SnapshotResponse:
    result = await create_snapshot(db, authorization.credentials if authorization else None, account_id, obj_in)
    match result:
        case Ok(response):
            return response
        case Err(SyncReadError(code)):
            raise HTTPException(sync_statuses.get(code, 410), detail=code)
        case Err(error):
            raise HTTPException(error_statuses[type(error)])
        case unexpected:
            assert_never(unexpected)


@router.get("/{snapshot_id}", operation_id="getSnapshot", response_model=SnapshotResponse,
            dependencies=[Depends(no_query_parameters)])
async def read_snapshot(
    account_id: UUID7, snapshot_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> SnapshotResponse:
    result = await get_snapshot(db, authorization.credentials if authorization else None, account_id, snapshot_id)
    match result:
        case Ok(response):
            return response
        case Err(SyncReadError(code)):
            raise HTTPException(sync_statuses.get(code, 410), detail=code)
        case Err(error):
            raise HTTPException(error_statuses[type(error)])
        case unexpected:
            assert_never(unexpected)


@router.get("/{snapshot_id}/items", operation_id="getSnapshotItems", response_model=PaginatedResponse[SyncItem])
async def read_snapshot_items(
    account_id: UUID7, snapshot_id: UUID7, query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[SyncItem]:
    result = await snapshot_page(db, authorization.credentials if authorization else None, account_id, snapshot_id, query)
    match result:
        case Ok(response):
            return response
        case Err(SyncReadError(code)):
            raise HTTPException(sync_statuses.get(code, 410), detail=code)
        case Err(error):
            raise HTTPException(error_statuses[type(error)])
        case unexpected:
            assert_never(unexpected)


@router.delete("/{snapshot_id}", operation_id="releaseSnapshot", status_code=204,
               dependencies=[Depends(no_query_parameters)])
async def delete_snapshot(
    account_id: UUID7, snapshot_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    result = await release_snapshot(db, authorization.credentials if authorization else None, account_id, snapshot_id)
    match result:
        case Ok():
            return Response(status_code=204)
        case Err(SyncReadError(code)):
            raise HTTPException(sync_statuses.get(code, 410), detail=code)
        case Err(error):
            raise HTTPException(error_statuses[type(error)])
        case unexpected:
            assert_never(unexpected)
