from datetime import datetime
from typing import Literal, TypedDict
from uuid import UUID

from pydantic import UUID7, AwareDatetime, ConfigDict, Field

from src.api.services.domain.services import ServiceQuery
from src.core.schema import AdministrativeResponse, BaseModel


class OfferServicePayload(BaseModel):
    duration_minutes_override: int | None = Field(default=None, strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")


class UpdateServiceOfferPayload(BaseModel):
    duration_minutes_override: int | None = Field(strict=True, ge=1, le=1440)

    model_config = ConfigDict(extra="forbid")


class ServiceOfferQuery(ServiceQuery):
    professional_id: UUID7 | None = None


class ServiceOfferProjection(TypedDict):
    account_id: UUID
    professional_id: UUID
    service_id: UUID
    name: str
    default_duration_minutes: int
    duration_minutes_override: int | None
    effective_duration_minutes: int
    status: str
    service_status: str
    service_version: int
    created_at: datetime
    updated_at: datetime
    version: int


class ServiceOfferResponse(AdministrativeResponse):
    account_id: UUID7
    professional_id: UUID7
    service_id: UUID7
    name: str
    default_duration_minutes: int
    duration_minutes_override: int | None
    effective_duration_minutes: int
    status: Literal["active", "inactive"]
    service_status: Literal["active", "inactive"]
    service_version: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int
