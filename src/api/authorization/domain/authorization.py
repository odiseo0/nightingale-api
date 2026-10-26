from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
)

from src.core.schema import AdministrativeResponse, BaseModel


@dataclass(frozen=True, slots=True)
class ExternalIdentity:
    issuer: str
    subject: str
    display_name: str


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    user_id: UUID
    device_id: UUID
    token_id: UUID


class DeviceRegistrationRequest(BaseModel):
    device_name: str = Field(min_length=1)
    client_version: str = Field(min_length=1)
    local_schema_version: int = Field(strict=True, gt=0)

    model_config = ConfigDict(extra="forbid")


class TokenRotationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeviceTokenIssued(BaseModel):
    token_type: Literal["Bearer"] = "Bearer"
    access_token: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(repr=False)
    token_id: UUID7
    device_id: UUID7
    user_id: UUID7
    issued_at: AwareDatetime

    @field_serializer("issued_at")
    def serialize_issued_at(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class AuthConfigResponse(BaseModel):
    issuer: Annotated[str, StringConstraints(strip_whitespace=False)]
    public_client_id: Annotated[str, StringConstraints(strip_whitespace=False)]
    audience: Annotated[str, StringConstraints(strip_whitespace=False)]
    authorization_flow: Literal["authorization_code"] = "authorization_code"
    pkce_method: Literal["S256"] = "S256"


class UserIdentity(BaseModel):
    id: UUID7
    display_name: str
    status: Literal["active", "inactive"]
    oidc_issuer: Annotated[str, StringConstraints(strip_whitespace=False)]
    oidc_subject: Annotated[str, StringConstraints(strip_whitespace=False)]
    version: int


class DeviceResponse(AdministrativeResponse):
    id: UUID7
    user_id: UUID7
    display_name: str
    status: Literal["active", "revoked"]
    client_version: str
    local_schema_version: int
    last_seen_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int
