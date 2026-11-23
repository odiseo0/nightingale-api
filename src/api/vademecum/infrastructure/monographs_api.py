from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.api.vademecum.application.read_cases import read_monograph, read_monographs
from src.api.vademecum.domain.catalog import (
    VademecumMonographPage,
    VademecumMonographQuery,
    VademecumMonographResponse,
)
from src.api.vademecum.domain.errors import VademecumNotFound, VademecumUnavailable
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError

router = APIRouter(
    prefix="/v1/accounts/{account_id}/vademecum",
    tags=["vademecum"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("/monographs", operation_id="listVademecumMonographs")
async def list_monographs(
    account_id: UUID7,
    query: Annotated[VademecumMonographQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> VademecumMonographPage:
    result = await read_monographs(
        db,
        authorization.credentials if authorization else None,
        account_id,
        query,
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
        case Err(VademecumUnavailable()):
            raise HTTPException(503)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/monographs/{monograph_id}",
    operation_id="getVademecumMonograph",
    dependencies=[Depends(no_query_parameters)],
)
async def get_monograph(
    account_id: UUID7,
    monograph_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> VademecumMonographResponse:
    result = await read_monograph(
        db,
        authorization.credentials if authorization else None,
        account_id,
        monograph_id,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | VademecumNotFound()):
            raise HTTPException(404)
        case Err(VademecumUnavailable()):
            raise HTTPException(503)
        case unexpected:
            assert_never(unexpected)
