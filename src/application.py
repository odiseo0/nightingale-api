from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.api.health import router as health_router
from src.core.db.session import create_db_engine
from src.settings.api_settings import APISettings
from src.settings.db_settings import DBSettings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Own the pool per process lifecycle, not at module import.
    # https://fastapi.tiangolo.com/advanced/events/#lifespan
    app.state.api_settings = APISettings()
    app.state.db_settings = DBSettings()
    engine = create_db_engine(app.state.db_settings)
    app.state.engine = engine
    app.state.session_factory = (
        async_sessionmaker(engine, expire_on_commit=False) if engine else None
    )

    try:
        yield
    finally:
        app.state.session_factory = None
        app.state.engine = None

        if engine is not None:
            await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Nightingale API", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router)

    return app


app = create_app()


def main() -> None:
    uvicorn.run("src.application:app", host="127.0.0.1")


if __name__ == "__main__":
    main()
