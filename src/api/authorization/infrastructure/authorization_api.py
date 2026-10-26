from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.application.authorization_cases import (
    get_config,
    get_devices,
    register_device,
    revoke_device,
    rotate_token,
)
from src.api.authorization.domain.authorization import (
    AuthConfigResponse,
    DeviceRegistrationRequest,
    DeviceResponse,
    DeviceTokenIssued,
    TokenRotationRequest,
)
from src.api.authorization.domain.errors import (
    AccessDenied,
    DeviceNotFound,
    IdentityProviderUnavailable,
    InvalidCredential,
)
from src.api.errors import no_query_parameters, request_correlation_id
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1",
    tags=["authorization"],
    responses={422: {"model": ApiError}},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/auth/config",
    dependencies=[Depends(no_query_parameters)],
    operation_id="getAuthConfig",
    summary="Consultar configuración de acceso",
    description="Devuelve el emisor y cliente OIDC públicos, sin secretos.",
    responses={503: {"model": ApiError}},
)
async def auth_config() -> AuthConfigResponse:
    result = get_config()

    match result:
        case Ok(config):
            return config
        case Err(IdentityProviderUnavailable()):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/auth/device-tokens",
    dependencies=[Depends(no_query_parameters)],
    status_code=status.HTTP_201_CREATED,
    operation_id="issueDeviceToken",
    summary="Emitir credencial de dispositivo",
    description="Valida el token OIDC y entrega una credencial nueva una sola vez.",
    responses={
        401: {"model": ApiError},
        403: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def issue_device_token(
    obj_in: DeviceRegistrationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    correlation_id: Annotated[UUID7, Depends(request_correlation_id)],
) -> DeviceTokenIssued:
    credential = authorization.credentials if authorization else None
    result = await register_device(db, credential=credential, obj_in=obj_in, correlation_id=correlation_id)

    match result:
        case Ok(issued):
            return issued
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case Err(IdentityProviderUnavailable()):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/me/devices/{device_id}/rotate-token",
    dependencies=[Depends(no_query_parameters)],
    status_code=status.HTTP_201_CREATED,
    operation_id="rotateDeviceToken",
    summary="Rotar la credencial propia",
    description="Revoca la credencial actual y crea su reemplazo en una transacción.",
    responses={
        401: {"model": ApiError},
        403: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def rotate_device_token(
    device_id: UUID7,
    obj_in: TokenRotationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    correlation_id: Annotated[UUID7, Depends(request_correlation_id)],
) -> DeviceTokenIssued:
    credential = authorization.credentials if authorization else None
    result = await rotate_token(db, credential=credential, device_id=device_id, correlation_id=correlation_id)

    match result:
        case Ok(issued):
            return issued
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(AccessDenied()):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/me/devices/{device_id}/revoke",
    dependencies=[Depends(no_query_parameters)],
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="revokeOwnDevice",
    summary="Revocar un dispositivo propio",
    description="Revoca la instalación y sus credenciales globales; conserva sus referencias.",
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def revoke_installation(
    device_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    correlation_id: Annotated[UUID7, Depends(request_correlation_id)],
) -> Response:
    credential = authorization.credentials if authorization else None
    result = await revoke_device(db, credential=credential, device_id=device_id, correlation_id=correlation_id)

    match result:
        case Ok():
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case Err(DeviceNotFound()):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/me/devices", operation_id="listOwnDevices",
    responses={401: {"model": ApiError}, 503: {"model": ApiError}},
)
async def read_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    query: Annotated[PageQuery, Query()],
) -> PaginatedResponse[DeviceResponse]:
    result = await get_devices(
        db, authorization.credentials if authorization else None,
        page=query.page, shows=query.shows,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        case unexpected:
            assert_never(unexpected)
