from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

import pycountry
from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    field_validator,
)

from src.api.authorization.domain.authorization import AuthenticatedActor
from src.core.schema import (
    AdministrativeResponse,
    BaseModel,
    PageQuery,
    PaginatedResponse,
)
from src.core.schema.http import SerializedInstant


class AccountDetails(BaseModel):
    display_name: str = Field(min_length=1)
    time_zone: str = Field(min_length=1)
    location_name: str = Field(min_length=1)
    location_address: str = Field(min_length=1)
    location_country: str = Field(default="VE", pattern=r"^[A-Z]{2}$")
    location_state: str = Field(min_length=1)
    location_city: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @field_validator("location_country")
    @classmethod
    def assigned_country(cls, value: str) -> str:
        if pycountry.countries.get(alpha_2=value) is None:
            raise ValueError("El país no pertenece al catálogo ISO admitido")

        return value


class BootstrapPracticeInput(AccountDetails):
    owner_issuer: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=1)
    ]
    owner_subject: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=1)
    ]
    owner_name: str = Field(min_length=1)
    professional_name: str = Field(min_length=1)

    @field_validator("owner_issuer", "owner_subject")
    @classmethod
    def nonblank_identity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("La identidad externa no puede estar vacía")

        return value


class PracticeCreated(BaseModel):
    user_id: UUID7
    account_id: UUID7
    professional_id: UUID7


class AccountSummary(BaseModel):
    id: UUID7
    display_name: str
    status: Literal["active", "inactive"]
    role: Literal["owner", "assistant"]


class MeResponse(BaseModel):
    user_id: UUID7
    display_name: str
    status: Literal["active", "inactive"]
    oidc_issuer: Annotated[str, StringConstraints(strip_whitespace=False)]
    oidc_subject: Annotated[str, StringConstraints(strip_whitespace=False)]
    accounts: PaginatedResponse[AccountSummary]


class AccountResponse(AdministrativeResponse):
    id: UUID7
    kind: Literal["independent"]
    owner_user_id: UUID7
    display_name: str
    time_zone: str
    location_name: str
    location_address: str
    location_country: str
    location_state: str
    location_city: str
    status: Literal["active", "inactive"]
    no_show_grace_minutes: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class AccessResponse(BaseModel):
    account_id: UUID7
    user_id: UUID7
    device_id: UUID7
    role: Literal["owner", "assistant"]
    status: Literal["active", "registration_required", "revoked", "inactive"]
    permission_epoch: int
    allowed_actions: list[str]


class ProfessionalResponse(AdministrativeResponse):
    id: UUID7
    user_id: UUID7
    public_name: str
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class AccountDeviceResponse(AdministrativeResponse):
    device_id: UUID7
    display_name: str
    status: Literal["active", "revoked"]
    client_version: str
    local_schema_version: int
    last_seen_at: AwareDatetime | None
    version: int


class InvitationResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7
    invitee_user_id: UUID7
    created_by_user_id: UUID7
    status: Literal["pending", "accepted", "revoked", "expired"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    expires_at: AwareDatetime
    accepted_at: AwareDatetime | None
    version: int

    @field_serializer("expires_at", "accepted_at", when_used="unless-none")
    def serialize_invitation_instants(self, value: datetime) -> SerializedInstant:
        return self.serialize_instant(value)


class InvitationQuery(PageQuery):
    status: Literal["pending", "accepted", "revoked", "expired"] | None = None


class InvitationAcceptRequest(BaseModel):
    operation_id: UUID7

    model_config = ConfigDict(extra="forbid")


class InvitationAcceptanceResult(BaseModel):
    operation_id: UUID7
    status: Literal["accepted", "duplicate"]
    invitation_id: UUID7
    account_id: UUID7
    membership_version: int


class MemberResponse(AdministrativeResponse):
    user_id: UUID7
    display_name: str
    role: Literal["owner", "assistant"]
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class CreateInvitationPayload(BaseModel):
    invitee_user_id: UUID7

    model_config = ConfigDict(extra="forbid")


class MembershipStatusPayload(BaseModel):
    status: Literal["active", "inactive"]

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True, slots=True)
class AccountChange:
    entity_type: str
    entity_key: str | dict[str, str]
    state: BaseModel | Mapping[str, object]
    version: int
    audience: Literal["members", "owner"] = "owner"
    account_id: UUID | None = None
    previous_starts_at: datetime | None = None
    previous_ends_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AccountEffect:
    state: BaseModel | Mapping[str, object]
    version: int
    changes: list[AccountChange]
    permission_changed: bool


class AccountDetailsPatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    time_zone: str | None = Field(default=None, min_length=1)
    location_name: str | None = Field(default=None, min_length=1)
    location_address: str | None = Field(default=None, min_length=1)
    location_country: str | None = None
    location_state: str | None = Field(default=None, min_length=1)
    location_city: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("location_country")
    @classmethod
    def assigned_country(cls, value: str | None) -> str | None:
        return value if value is None else AccountDetails.assigned_country(value)

    @field_validator("*")
    @classmethod
    def present_value(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("El campo presente no puede ser nulo")

        return value


class AccountPolicyPayload(BaseModel):
    no_show_grace_minutes: int = Field(strict=True, ge=0, le=1440)

    model_config = ConfigDict(extra="forbid")


class ProfessionalPayload(BaseModel):
    public_name: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class ProfessionalQuery(PageQuery):
    status: Literal["active", "inactive"] | None = None


@dataclass(frozen=True, slots=True)
class AccountContext:
    actor: AuthenticatedActor
    account: AccountResponse
    device_status: str | None
    owner: bool
