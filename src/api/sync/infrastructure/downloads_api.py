from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.sync.application.download_cases import read_changes
from src.api.sync.domain.downloads import ChangePage, ChangeQuery
from src.api.sync.domain.errors import SyncReadError
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/accounts/{account_id}/sync", tags=["sync"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 410, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/changes", operation_id="getChanges", response_model=ChangePage)
async def download_changes(
    account_id: UUID7,
    query: Annotated[ChangeQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ChangePage:
    result = await read_changes(db, authorization.credentials if authorization else None, account_id, query.cursor)
    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(SyncReadError(code)):
            raise HTTPException(503 if code == "DEPENDENCY_UNAVAILABLE" else 410, detail=code)
        case unexpected:
            assert_never(unexpected)
