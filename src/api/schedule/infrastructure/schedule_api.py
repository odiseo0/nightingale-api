from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
)
from src.api.appointments.application.appointments_cases import read_availability
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.api.schedule.application.blocks_cases import read_blocks
from src.api.schedule.application.exceptions_cases import read_exceptions
from src.api.schedule.application.schedule_cases import read_rules
from src.api.schedule.domain.schedule import (
    AvailabilityQuery,
    AvailabilityResponse,
    ScheduleBlockQuery,
    ScheduleBlockResponse,
    ScheduleExceptionQuery,
    ScheduleExceptionResponse,
    ScheduleRuleQuery,
    ScheduleRuleResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}",
    tags=["schedule"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/schedule/rules",
    operation_id="listScheduleRules",
    response_model=PaginatedResponse[ScheduleRuleResponse],
)
async def list_schedule_rules(
    account_id: UUID7,
    query: Annotated[ScheduleRuleQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_rules(
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


@router.get(
    "/schedule/rules/{rule_id}",
    operation_id="getScheduleRule",
    response_model=ScheduleRuleResponse,
    dependencies=[Depends(no_query_parameters)],
)
async def get_schedule_rule(
    account_id: UUID7,
    rule_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_rules(
        db,
        authorization.credentials if authorization else None,
        account_id,
        ScheduleRuleQuery(),
        rule_id,
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


@router.get(
    "/schedule/exceptions",
    operation_id="listScheduleExceptions",
    response_model=PaginatedResponse[ScheduleExceptionResponse],
)
async def list_schedule_exceptions(
    account_id: UUID7,
    query: Annotated[ScheduleExceptionQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_exceptions(
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


@router.get(
    "/schedule/exceptions/{exception_id}",
    operation_id="getScheduleException",
    response_model=ScheduleExceptionResponse,
    dependencies=[Depends(no_query_parameters)],
)
async def get_schedule_exception(
    account_id: UUID7,
    exception_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_exceptions(
        db,
        authorization.credentials if authorization else None,
        account_id,
        exception_id=exception_id,
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


@router.get(
    "/schedule/blocks",
    operation_id="listScheduleBlocks",
    response_model=PaginatedResponse[ScheduleBlockResponse],
)
async def list_schedule_blocks(
    account_id: UUID7,
    query: Annotated[ScheduleBlockQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_blocks(
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


@router.get(
    "/schedule/blocks/{block_id}",
    operation_id="getScheduleBlock",
    response_model=ScheduleBlockResponse,
    dependencies=[Depends(no_query_parameters)],
)
async def get_schedule_block(
    account_id: UUID7,
    block_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_blocks(
        db,
        authorization.credentials if authorization else None,
        account_id,
        block_id=block_id,
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


@router.get(
    "/availability", operation_id="getAvailability", response_model=AvailabilityResponse
)
async def get_availability(
    account_id: UUID7,
    query: Annotated[AvailabilityQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await read_availability(
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
        case Err(AccountRuleError()):
            raise HTTPException(422)
        case unexpected:
            assert_never(unexpected)
