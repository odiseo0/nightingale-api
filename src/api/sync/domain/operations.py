from datetime import UTC
from typing import Annotated, Literal, Self

from pydantic import (
    UUID7, AwareDatetime, ConfigDict, Field, JsonValue, StringConstraints,
    field_serializer, field_validator, model_validator,
)

from src.api.accounts.domain.accounts import AccountDeviceResponse, AccountResponse, InvitationAcceptanceResult, InvitationResponse, MemberResponse, ProfessionalResponse
from src.api.patients.domain.patients import PatientIdentifierResponse, PatientProfileResponse
from src.api.patients.domain.contacts import ContactResponse, RelationshipResponse
from src.core.schema import ApiError, BaseModel


class OperationEnvelope(BaseModel):
    operation_id: UUID7
    contract_version: int = Field(strict=True, ge=1, le=1)
    action: Annotated[str, StringConstraints(strip_whitespace=False, min_length=1)]
    entity_key: UUID7 | dict[str, UUID7]
    expected_version: int = Field(strict=True, ge=0)
    payload: dict[str, JsonValue]
    depends_on: list[UUID7] = Field(default_factory=list, max_length=8)
    occurred_at_local: AwareDatetime | None = None

    # An invalid payload is hashed as received. The shared base strips text,
    # which would otherwise merge two distinct rejected requests.
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=False)

    @field_validator("action")
    def nonblank_action(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("La acción no puede estar vacía")

        return value

    @field_validator("entity_key")
    def known_key(cls, value):
        if isinstance(value, dict) and set(value) not in (
            {"patientId", "contactPersonId"}, {"professionalId", "serviceId"},
        ):
            raise ValueError("La clave compuesta no pertenece al contrato")

        return value

    @field_serializer("occurred_at_local")
    def serialize_local_time(self, value):
        return None if value is None else value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class OperationBatch(BaseModel):
    operations: list[OperationEnvelope] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def ordered_dependencies(self) -> Self:
        positions = {item.operation_id: index for index, item in enumerate(self.operations)}
        if len(positions) != len(self.operations):
            raise ValueError("El lote repite una operación")
        for index, item in enumerate(self.operations):
            if len(set(item.depends_on)) != len(item.depends_on) or any(
                positions.get(dependency, -1) >= index for dependency in item.depends_on
            ):
                raise ValueError("Las dependencias del lote no tienen un orden válido")

        return self


class OperationRecord(BaseModel):
    operation_id: UUID7
    status: Literal["accepted", "conflict", "rejected", "retryable_failure"]
    entity_version: int | None
    state: AccountDeviceResponse | AccountResponse | InvitationResponse | InvitationAcceptanceResult | MemberResponse | ProfessionalResponse | PatientProfileResponse | PatientIdentifierResponse | ContactResponse | RelationshipResponse | None
    error: ApiError | None


class OperationResult(OperationRecord):
    status: Literal["accepted", "duplicate", "conflict", "rejected", "retryable_failure"]
    original_result: OperationRecord | None = None


class OperationBatchResult(BaseModel):
    results: list[OperationResult]
    correlation_id: UUID7
