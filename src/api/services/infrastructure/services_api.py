from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.services.application.offers_cases import read_offers
from src.api.services.application.services_cases import read_catalog
from src.api.services.domain.offers import ServiceOfferQuery, ServiceOfferResponse
from src.api.services.domain.services import ServiceQuery, ServiceResponse
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    tags=["services"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/v1/me/services",
    operation_id="listOwnServices",
    response_model=PaginatedResponse[ServiceResponse],
)
async def list_own_services(
    query: Annotated[ServiceQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_catalog(
        db, authorization.credentials if authorization else None, query
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/services",
    operation_id="listServiceOffers",
    response_model=PaginatedResponse[ServiceOfferResponse],
)
async def list_service_offers(
    account_id: UUID7,
    query: Annotated[ServiceOfferQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_offers(
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
