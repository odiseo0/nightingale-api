from functools import partial
from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import ServerSentEvent
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.sync.application.events_cases import (
    close_events,
    open_events,
    stream_events,
)
from src.api.sync.domain.downloads import ChangeQuery
from src.api.sync.domain.errors import SyncReadError
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError
from src.core.services.sse import BoundedEventSourceResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/sync",
    tags=["sync"],
    responses={
        code: {"model": ApiError} for code in (401, 403, 404, 410, 422, 429, 503)
    },
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/events",
    operation_id="getSyncEvents",
    response_class=StreamingResponse,
    response_model=None,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def events(
    account_id: UUID7,
    query: Annotated[ChangeQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db, scope="function")],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> BoundedEventSourceResponse:
    credential = authorization.credentials if authorization else None
    result = await open_events(db, credential, account_id, query.cursor)

    match result:
        case Ok((connection, slot)):
            frames = (
                ServerSentEvent(
                    event=notice.event,
                    id=notice.event_id,
                    retry=3000,
                    raw_data=notice.data.model_dump_json(by_alias=True)
                    if notice.data is not None
                    else None,
                )
                async for notice in stream_events(credential, connection, slot)
            )
            return BoundedEventSourceResponse(
                frames, partial(close_events, connection, slot)
            )
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(SyncReadError(code)):
            raise HTTPException(
                503
                if code == "DEPENDENCY_UNAVAILABLE"
                else 429
                if code == "CONNECTION_LIMIT"
                else 410,
                detail=code,
            )
        case unexpected:
            assert_never(unexpected)
