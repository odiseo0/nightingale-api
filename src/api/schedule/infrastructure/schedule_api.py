from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.errors import no_query_parameters
from src.api.schedule.application.schedule_cases import read_rules
from src.api.schedule.domain.schedule import ScheduleRuleQuery, ScheduleRuleResponse
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/schedule/rules",
    tags=["schedule"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("", operation_id="listScheduleRules", response_model=PaginatedResponse[ScheduleRuleResponse])
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
    "/{rule_id}",
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
