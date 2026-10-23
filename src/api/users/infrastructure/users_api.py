from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.users.application.users_cases import (
    create,
    get_multi,
    get_one,
    remove,
    update,
)
from src.api.users.domain import UserNotFound
from src.api.users.domain.users import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import VALIDATION_RESPONSE

router = APIRouter(tags=["users"])

type UserId = Annotated[
    int,
    Path(gt=0, description="Identificador positivo del usuario."),
]


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=UserListResponse,
    operation_id="listUsers",
    summary="Listar usuarios",
    description=(
        "Devuelve usuarios de todo Free Win con el total disponible. Requiere "
        "permiso global."
    ),
)
async def read_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[
        int, Query(ge=1, description="Página solicitada; comienza en 1.")
    ] = 1,
    shows: Annotated[
        int,
        Query(ge=1, le=100, description="Cantidad máxima de usuarios por página."),
    ] = 100,
) -> UserListResponse:
    result = await get_multi(db, page=page, shows=shows)

    match result:
        case Ok((users, total)):
            return UserListResponse(items=users, total=total)
        case Err(error):
            assert_never(error)


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    operation_id="getUser",
    summary="Consultar un usuario",
    description=(
        "Permite consultar el usuario propio con permiso personal o cualquier usuario "
        "con permiso global. La respuesta nunca incluye la contraseña."
    ),
)
async def read_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: UserId,
) -> UserResponse:
    result = await get_one(db, user_id)

    match result:
        case Ok(user):
            return user
        case Err(UserNotFound()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe",
            )
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    operation_id="createUser",
    summary="Crear un usuario",
    description=(
        "Registra un usuario con el tratamiento temporal actual de contraseña. La "
        "contraseña es solo de entrada y nunca forma parte de la respuesta."
    ),
    responses={422: VALIDATION_RESPONSE},
)
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)], user_in: UserCreate
) -> UserResponse:
    result = await create(db, obj_in=user_in)

    match result:
        case Ok(user):
            return user
        case Err(error):
            assert_never(error)


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    operation_id="updateUser",
    summary="Actualizar un usuario",
    description=(
        "Permite actualizar el perfil propio con permiso personal o cualquier perfil "
        "con permiso global. Una contraseña enviada nunca se devuelve."
    ),
)
async def update_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: UserId,
    user_in: UserUpdate,
) -> UserResponse:
    result = await update(db, user_id=user_id, obj_in=user_in)

    match result:
        case Ok(user):
            return user
        case Err(UserNotFound()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe",
            )
        case unexpected:
            assert_never(unexpected)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    operation_id="deleteUser",
    summary="Eliminar un usuario",
    description=("Elimina un usuario con permiso global y responde sin cuerpo."),
)
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)], user_id: UserId
) -> Response:
    result = await remove(db, user_id=user_id)

    match result:
        case Ok():
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        case Err(UserNotFound()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe",
            )
        case unexpected:
            assert_never(unexpected)
