from datetime import UTC, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)

from src.api.accounts.domain.accounts import (
    AccountDetailsPatch,
    AccountDeviceResponse,
    AccountPolicyPayload,
    AccountResponse,
    CreateInvitationPayload,
    InvitationAcceptanceResult,
    InvitationResponse,
    MemberResponse,
    MembershipStatusPayload,
    ProfessionalPayload,
    ProfessionalResponse,
)
from src.api.appointments.domain.appointments import (
    AppointmentInterval,
    AppointmentReasonPayload,
    AppointmentResponse,
    CreateAppointmentPayload,
    EmptyAppointmentPayload,
)
from src.api.patients.domain.contacts import (
    CONTACT_SCHEMAS,
    ContactResponse,
    RelationshipResponse,
)
from src.api.patients.domain.patients import (
    AddPatientIdentifierPayload,
    PatientCompletionPayload,
    PatientIdentifierResponse,
    PatientPatch,
    PatientProfileResponse,
    PatientStatusPayload,
    RegisterPatientPayload,
)
from src.api.schedule.domain.schedule import (
    CreateScheduleBlockPayload,
    CreateScheduleExceptionPayload,
    CreateScheduleRulePayload,
    ScheduleBlockPatch,
    ScheduleBlockResponse,
    ScheduleExceptionPatch,
    ScheduleExceptionResponse,
    ScheduleRulePatch,
    ScheduleRuleResponse,
    ScheduleRuleStatusPayload,
)
from src.api.services.domain.offers import (
    OfferServicePayload,
    ServiceOfferResponse,
    UpdateServiceOfferPayload,
)
from src.api.services.domain.services import (
    CreateServicePayload,
    ServicePatch,
    ServiceResponse,
    ServiceStatusPayload,
)
from src.core.schema import ApiError, BaseModel
from src.core.schema.http import SerializedInstant

SERVICE_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateService": CreateServicePayload,
    "UpdateService": ServicePatch,
    "SetServiceStatus": ServiceStatusPayload,
}
OFFER_SCHEMAS: dict[str, type[BaseModel]] = {
    "OfferService": OfferServicePayload,
    "UpdateServiceOffer": UpdateServiceOfferPayload,
    "SetServiceOfferStatus": ServiceStatusPayload,
}
RULE_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateScheduleRule": CreateScheduleRulePayload,
    "UpdateScheduleRule": ScheduleRulePatch,
    "SetScheduleRuleStatus": ScheduleRuleStatusPayload,
}
EXCEPTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateScheduleException": CreateScheduleExceptionPayload,
    "UpdateScheduleException": ScheduleExceptionPatch,
    "SetScheduleExceptionStatus": ScheduleRuleStatusPayload,
}
BLOCK_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateScheduleBlock": CreateScheduleBlockPayload,
    "UpdateScheduleBlock": ScheduleBlockPatch,
    "SetScheduleBlockStatus": ScheduleRuleStatusPayload,
}
APPOINTMENT_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateAppointment": CreateAppointmentPayload,
    "ConfirmAppointment": EmptyAppointmentPayload,
    "RescheduleAppointment": AppointmentInterval,
    "CancelAppointment": AppointmentReasonPayload,
    "CompleteAppointment": AppointmentReasonPayload,
    "MarkAppointmentNoShow": AppointmentReasonPayload,
}

OPERATION_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateInvitation": CreateInvitationPayload,
    "SetMembershipStatus": MembershipStatusPayload,
    "UpdateAccountDetails": AccountDetailsPatch,
    "UpdateAccountPolicy": AccountPolicyPayload,
    "SetAccountStatus": MembershipStatusPayload,
    "UpdateProfessionalProfile": ProfessionalPayload,
    "RegisterPatient": RegisterPatientPayload,
    "UpdatePatientProfile": PatientPatch,
    "SetPatientProfileStatus": PatientStatusPayload,
    "SetPatientCompletion": PatientCompletionPayload,
    "AddPatientIdentifier": AddPatientIdentifierPayload,
    **CONTACT_SCHEMAS,
    **SERVICE_SCHEMAS,
    **OFFER_SCHEMAS,
    **RULE_SCHEMAS,
    **EXCEPTION_SCHEMAS,
    **BLOCK_SCHEMAS,
    **APPOINTMENT_SCHEMAS,
}

EMPTY_PAYLOAD_ACTIONS = {
    "AcceptInvitation",
    "RegisterAccountDevice",
    "RestoreAccountDevice",
    "RevokeAccountDevice",
    "RevokeInvitation",
}


class OperationEnvelope(BaseModel):
    operation_id: UUID7
    contract_version: int = Field(strict=True, ge=1, le=1)
    action: Annotated[str, StringConstraints(strip_whitespace=False, min_length=1)]
    entity_key: UUID7 | dict[str, UUID7]
    expected_version: int = Field(strict=True, ge=0)
    payload: dict[str, JsonValue]
    depends_on: list[UUID7] = Field(default_factory=list, max_length=8)
    occurred_at_local: AwareDatetime | None = Field(
        default=None, json_schema_extra={"default": None}
    )

    # An invalid payload is hashed as received. The shared base strips text,
    # which would otherwise merge two distinct rejected requests.
    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False, str_strip_whitespace=False
    )

    def validated_payload(self) -> BaseModel | None:
        schema = OPERATION_SCHEMAS.get(self.action)

        if schema is None:
            return (
                BaseModel()
                if self.action in EMPTY_PAYLOAD_ACTIONS and not self.payload
                else None
            )

        try:
            return schema.model_validate(self.payload)
        except ValidationError:
            return None

    @field_validator("action")
    @classmethod
    def nonblank_action(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("La acción no puede estar vacía")

        return value

    @field_validator("entity_key")
    @classmethod
    def known_key(cls, value: UUID | dict[str, UUID]) -> UUID | dict[str, UUID]:
        if isinstance(value, dict) and set(value) not in (
            {"patientId", "contactPersonId"},
            {"professionalId", "serviceId"},
        ):
            raise ValueError("La clave compuesta no pertenece al contrato")

        return value

    @field_serializer("occurred_at_local")
    def serialize_local_time(self, value: datetime | None) -> SerializedInstant | None:
        return (
            None
            if value is None
            else value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )


class OperationBatch(BaseModel):
    operations: list[OperationEnvelope] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def ordered_dependencies(self) -> Self:
        positions = {
            item.operation_id: index for index, item in enumerate(self.operations)
        }
        if len(positions) != len(self.operations):
            raise ValueError("El lote repite una operación")

        for index, item in enumerate(self.operations):
            if len(set(item.depends_on)) != len(item.depends_on) or any(
                positions.get(dependency, -1) >= index for dependency in item.depends_on
            ):
                raise ValueError("Las dependencias del lote no tienen un orden válido")

        return self


type OperationState = (
    AccountDeviceResponse
    | AccountResponse
    | InvitationResponse
    | InvitationAcceptanceResult
    | MemberResponse
    | ProfessionalResponse
    | PatientProfileResponse
    | PatientIdentifierResponse
    | ContactResponse
    | RelationshipResponse
    | ServiceResponse
    | ServiceOfferResponse
    | ScheduleRuleResponse
    | ScheduleExceptionResponse
    | ScheduleBlockResponse
    | AppointmentResponse
)


class OperationRecord(BaseModel):
    operation_id: UUID7
    status: Literal["accepted", "conflict", "rejected", "retryable_failure"]
    entity_version: int | None
    state: OperationState | None
    error: ApiError | None


class OperationResult(OperationRecord):
    status: Literal[
        "accepted", "duplicate", "conflict", "rejected", "retryable_failure"
    ]
    original_result: OperationRecord | None = None


class OperationBatchResult(BaseModel):
    results: list[OperationResult]
    correlation_id: UUID7
