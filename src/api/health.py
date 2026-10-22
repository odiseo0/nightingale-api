from asyncio import timeout

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/health", include_in_schema=False)


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    engine = request.app.state.engine

    if engine is None:
        return JSONResponse(
            {"status": "not_ready", "database": "not_configured"}, status_code=503
        )

    try:
        async with timeout(request.app.state.db_settings.pool_timeout):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError):
        return JSONResponse(
            {"status": "not_ready", "database": "unavailable"}, status_code=503
        )

    return JSONResponse({"status": "ready", "database": "available"})
