import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schema.http import LiveResponse, ReadyResponse
from src.core.services.pg_notifications import notifications
from src.settings.db_settings import db_settings

router = APIRouter(prefix="/health", tags=["health"])


async def get_ready_db() -> AsyncIterator[AsyncSession | None]:
    if db_settings.SQLALCHEMY_DATABASE_URI is None:
        yield None
        return

    from src.core.db import get_db

    async with aclosing(get_db()) as sessions:
        async for db in sessions:
            yield db


@router.get("/live", operation_id="getLiveness", response_model=LiveResponse)
async def live() -> LiveResponse:
    return LiveResponse(status="alive")


@router.get(
    "/ready",
    operation_id="getReadiness",
    response_model=ReadyResponse,
    response_model_exclude_none=True,
    responses={503: {"model": ReadyResponse}},
)
async def ready(
    db: Annotated[AsyncSession | None, Depends(get_ready_db)],
) -> ReadyResponse | JSONResponse:
    if db is None:
        return JSONResponse(
            {"status": "not_ready", "database": "not_configured"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        async with asyncio.timeout(db_settings.pool_timeout):
            await db.execute(text("SELECT 1"))
    except SQLAlchemyError, OSError, TimeoutError:
        return JSONResponse(
            {"status": "not_ready", "database": "unavailable"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if not notifications.ready:
        return JSONResponse(
            {
                "status": "not_ready",
                "database": "available",
                "notifications": "unavailable",
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return ReadyResponse(
        status="ready", database="available", notifications="available"
    )
