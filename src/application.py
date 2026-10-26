from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from src.api.accounts.infrastructure.accounts_api import router as accounts_router
from src.api.accounts.infrastructure.invitations_api import router as invitations_router
from src.api.audit.infrastructure.audit_api import router as audit_router
from src.api.authorization.infrastructure.authorization_api import (
    router as authorization_router,
)
from src.api.errors import (
    correlate_request,
    database_error,
    http_error,
    validation_error,
)
from src.api.health import router as health_router
from src.api.patients.infrastructure.contacts_api import router as contacts_router
from src.api.patients.infrastructure.patients_api import router as patients_router
from src.api.sync.infrastructure.operations_api import router as operations_router
from src.core.db import DAOError
from src.settings.api_settings import api_settings

app = FastAPI(title="Nightingale API", version="0.1.0")
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
app.include_router(health_router)
app.include_router(authorization_router)
app.include_router(accounts_router)
app.include_router(invitations_router)
app.include_router(audit_router)
app.include_router(operations_router)
app.include_router(patients_router)
app.include_router(contacts_router)


@app.get("/")
async def welcome():
    return {"message": "Bienvenido a Nightingale API"}
