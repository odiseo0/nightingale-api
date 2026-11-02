from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from src.api.api import router
from src.api.errors import (
    correlate_request,
    database_error,
    http_error,
    validation_error,
)
from src.core.db import DAOError
from src.core.services.pg_notifications import notifications
from src.settings.api_settings import api_settings
from src.settings.db_settings import db_settings


@asynccontextmanager
async def listener_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    uri = db_settings.SQLALCHEMY_DATABASE_URI

    if uri is not None:
        await notifications.start(uri)

    try:
        yield
    finally:
        await notifications.stop()


app = FastAPI(
    title="Nightingale API",
    version="0.1.0",
    lifespan=listener_lifespan,
    openapi_url="/openapi.json" if api_settings.environment != "production" else None,
    docs_url="/docs" if api_settings.environment != "production" else None,
    redoc_url="/redoc" if api_settings.environment != "production" else None,
)
app.include_router(router)
app.middleware("http")(correlate_request)
app.add_exception_handler(RequestValidationError, validation_error)
app.add_exception_handler(SQLAlchemyError, database_error)
app.add_exception_handler(DAOError, database_error)
app.add_exception_handler(HTTPException, http_error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def welcome():
    return {"message": "Bienvenido a Nightingale API"}
