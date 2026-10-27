from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.core.schema import AdministrativeResponse, BaseModel, PageQuery


class ServiceFields(BaseModel):
    name: str = Field(min_length=1)
    default_duration_minutes: int = Field(strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")


class CreateServicePayload(ServiceFields):
    professional_id: UUID7


class ServicePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    default_duration_minutes: int | None = Field(
        default=None, strict=True, ge=1, le=1440
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("*")
    @classmethod
    def present_value(cls, value: str | int | None) -> str | int:
        if value is None:
            raise ValueError("El campo presente no puede ser nulo")

        return value

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class ServiceStatusPayload(BaseModel):
    status: Literal["active", "inactive"]

    model_config = ConfigDict(extra="forbid")


class ServiceQuery(PageQuery):
    q: str | None = Field(default=None, min_length=1, max_length=256)
    status: Literal["active", "inactive"] | None = None


class ServiceResponse(AdministrativeResponse):
    id: UUID7
    professional_id: UUID7
    name: str
    default_duration_minutes: int
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int
