from uuid import uuid7

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from src.core.db import DAOError
from src.core.schema import ApiError, FieldError


async def no_query_parameters(request: Request):
    if request.query_params:
        raise HTTPException(status_code=422)


def error_response(
    request: Request,
    status: int,
    code: str,
    message: str,
    details: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
):
    response_headers = dict(headers or {})
    if status == 401:
        response_headers.setdefault("WWW-Authenticate", "Bearer")

    error = ApiError(
        code=code,
        message=message,
        correlation_id=request.state.correlation_id,
        details=details or [],
    )

    # JSONResponse does not apply schema aliases; serialize them explicitly.
    # https://docs.pydantic.dev/latest/concepts/serialization/#python-mode
    return JSONResponse(
        error.model_dump(mode="json", by_alias=True),
        status_code=status,
        headers=response_headers,
    )


async def correlate_request(request: Request, call_next):
    request.state.correlation_id = uuid7()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = str(request.state.correlation_id)
    if request.url.path.startswith("/v1/"):
        response.headers["Cache-Control"] = "no-store"

    return response


async def validation_error(request: Request, error: RequestValidationError):
    details = []
    for item in error.errors():
        location = list(item["loc"])
        if item["type"] == "extra_forbidden":
            location = location[:-1]
        details.append(FieldError(loc=location, code=item["type"]))

    return error_response(
        request, 422, "VALIDATION_ERROR", "La entrada no es válida", details
    )


async def database_error(request: Request, error: SQLAlchemyError | DAOError):
    return error_response(
        request, 503, "DEPENDENCY_UNAVAILABLE", "El servicio no está disponible"
    )


async def http_error(request: Request, error: HTTPException):
    codes = {
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        503: "DEPENDENCY_UNAVAILABLE",
    }

    return error_response(
        request,
        error.status_code,
        codes.get(error.status_code, "REQUEST_ERROR"),
        "No se puede completar la petición",
        headers=error.headers,
    )
