from datetime import UTC, datetime
from typing import Annotated, TypeVar, overload

from pydantic import UUID7, ConfigDict, Field, WithJsonSchema, field_serializer

from .base import BaseModel

T = TypeVar("T")

# A string return annotation must retain the public date-time format.
# https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/json_schema.md#withjsonschema-annotation
SerializedInstant = Annotated[
    str, WithJsonSchema({"type": "string", "format": "date-time"})
]


class ErrorResponse(BaseModel):
    detail: str = Field(
        description="Mensaje comprensible que explica el error recuperable.",
        examples=["El recurso no existe"],
    )


class ValidationErrorDetail(BaseModel):
    type: str
    loc: list[str | int]
    msg: str
    input: object | None = None
    ctx: dict[str, object] | None = None


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorDetail]


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int = Field(ge=0)


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    shows: int = Field(default=100, ge=1, le=500)

    model_config = ConfigDict(extra="forbid")


class AdministrativeResponse(BaseModel):
    @overload
    def serialize_instant(self, value: datetime) -> str: ...

    @overload
    def serialize_instant(self, value: None) -> None: ...

    @field_serializer("created_at", "updated_at", "last_seen_at", check_fields=False)
    def serialize_instant(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class FieldError(BaseModel):
    loc: list[str | int]
    code: str


class ApiError(BaseModel):
    code: str
    message: str
    correlation_id: UUID7
    details: list[FieldError] = Field(default_factory=list)


UNAUTHORIZED_RESPONSE: dict[str, type[ErrorResponse] | str] = {
    "model": ErrorResponse,
    "description": "No existe una identidad autenticada válida.",
}
FORBIDDEN_RESPONSE: dict[str, type[ErrorResponse] | str] = {
    "model": ErrorResponse,
    "description": "La identidad no posee el permiso requerido.",
}
NOT_FOUND_RESPONSE: dict[str, type[ErrorResponse] | str] = {
    "model": ErrorResponse,
    "description": "El recurso solicitado no existe o no es visible.",
}
CONFLICT_RESPONSE: dict[str, type[ErrorResponse] | str] = {
    "model": ErrorResponse,
    "description": "La operación entra en conflicto con el estado actual del recurso.",
}
VALIDATION_RESPONSE: dict[str, type[ValidationErrorResponse] | str] = {
    "model": ValidationErrorResponse,
    "description": "La entrada no cumple el contrato de la operación.",
}
