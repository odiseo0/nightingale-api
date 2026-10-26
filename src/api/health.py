import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings.db_settings import db_settings

router = APIRouter(prefix="/health", include_in_schema=False)


async def get_ready_db() -> AsyncIterator[AsyncSession | None]:
    if db_settings.SQLALCHEMY_DATABASE_URI is None:
        yield None
        return

    from src.core.db import get_db

    async with aclosing(get_db()) as sessions:
        async for db in sessions:
            yield db


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def ready(db: Annotated[AsyncSession | None, Depends(get_ready_db)]):
    if db is None:
        return JSONResponse(
            {"status": "not_ready", "database": "not_configured"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        async with asyncio.timeout(db_settings.pool_timeout):
            await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError):
        return JSONResponse(
            {"status": "not_ready", "database": "unavailable"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return {"status": "ready", "database": "available"}
