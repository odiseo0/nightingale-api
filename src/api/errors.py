from uuid import UUID, uuid7

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


async def bounded_body(request: Request):
    if len(await request.body()) > 1024 * 1024:
        raise HTTPException(status_code=413)


async def request_correlation_id(request: Request):
    return request.state.correlation_id


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
    if error.status_code in (401, 403, 404) and request.url.path.startswith("/v1/"):
        from src.api.audit.application.controls_cases import record_http_denial
        from src.core.db.session import async_session_factory

        header = request.headers.get("Authorization", "")
        scheme, _, credential = header.partition(" ")
        raw_account = request.path_params.get("account_id")

        try:
            account_id = UUID(str(raw_account)) if raw_account is not None else None
        except ValueError:
            account_id = None

        try:
            async with async_session_factory() as db:
                await record_http_denial(
                    db,
                    credential if scheme.lower() == "bearer" else None,
                    account_id,
                    request.state.correlation_id,
                )
        except DAOError, SQLAlchemyError, OSError, TimeoutError:
            # A failed audit store cannot change a denial into access, or mask
            # the original HTTP result. Successful effects use atomic auditing.
            pass

    codes = {
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        409: "CONFLICT",
        410: "RESULT_EXPIRED",
        413: "REQUEST_TOO_LARGE",
        422: "VALIDATION_ERROR",
        503: "DEPENDENCY_UNAVAILABLE",
    }

    return error_response(
        request,
        error.status_code,
        error.detail
        if error.status_code == 409
        and error.detail
        in {
            "NO_CHANGES",
            "INVALID_STATE_TRANSITION",
            "IDEMPOTENCY_CONFLICT",
            "VERSION_CONFLICT",
        }
        else codes.get(error.status_code, "REQUEST_ERROR"),
        "No se puede completar la petición",
        headers=error.headers,
    )
