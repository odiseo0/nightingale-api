from dataclasses import dataclass
from typing import Annotated, Literal

import pycountry
from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from src.api.authorization.domain.authorization import AuthenticatedActor
from src.core.schema import AdministrativeResponse, BaseModel, PaginatedResponse


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


@dataclass(frozen=True, slots=True)
class AccountContext:
    actor: AuthenticatedActor
    account: AccountResponse
    device_status: str | None
    owner: bool
