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
    ClinicalPermissionsPayload,
    CreateInvitationPayload,
    InvitationAcceptanceResult,
    InvitationResponse,
    MemberClinicalPermissionsResponse,
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
from src.api.clinical_records.domain.allergies import (
    CreatePatientAllergyIntolerancePayload,
    InvalidatePatientAllergyIntolerancePayload,
    PatientAllergyIntoleranceResponse,
    UpdatePatientAllergyIntolerancePayload,
)
from src.api.clinical_records.domain.antecedents import (
    CreatePatientAntecedentPayload,
    InvalidatePatientAntecedentPayload,
    PatientAntecedentResponse,
    UpdatePatientAntecedentPayload,
)
from src.api.clinical_records.domain.clinical import (
    ClinicalProfileResponse,
    SetPatientSexAtBirthPayload,
)
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewResponse,
    CreatePatientConditionPayload,
    InvalidatePatientConditionPayload,
    PatientConditionResponse,
    SetPatientClinicalSectionReviewPayload,
    UpdatePatientConditionPayload,
)
from src.api.clinical_records.domain.immunizations import (
    InvalidatePatientImmunizationPayload,
    PatientImmunizationResponse,
    RecordPatientImmunizationPayload,
    UpdatePatientImmunizationPayload,
)
from src.api.clinical_records.domain.measurements import (
    CorrectPatientMeasurementPayload,
    InvalidatePatientMeasurementPayload,
    PatientMeasurementResponse,
    RecordPatientMeasurementPayload,
)
from src.api.clinical_records.domain.notes import (
    CreatePatientNotePayload,
    InvalidatePatientNotePayload,
    PatientNoteResponse,
    UpdatePatientNotePayload,)
from src.api.care_plans.domain.goals import (
    AddCarePlanActionPayload,
    AddCarePlanGoalPayload,
    AddCarePlanReviewPayload,
    CarePlanActionResponse,
    CarePlanGoalResponse,
    CarePlanReviewResponse,
    CompleteCarePlanActionPayload,
    EvaluateCarePlanGoalPayload,
    InvalidateCarePlanActionPayload,
    InvalidateCarePlanGoalPayload,
    InvalidateCarePlanReviewPayload,
    UpdateCarePlanActionPayload,
    UpdateCarePlanGoalPayload,
)
from src.api.care_plans.domain.plans import (
    CarePlanResponse,
    CreatePatientCarePlanPayload,
    InvalidatePatientCarePlanPayload,
    UpdatePatientCarePlanPayload,
)
from src.api.diagnostic_results.domain.reports import (
    CorrectDiagnosticReportPayload,
    CreateDiagnosticReportPayload,
    DiagnosticReportHistoryResponse,
    DiagnosticReportResponse,
    UpdateDiagnosticReportPayload,
)
from src.api.diagnostic_results.domain.results import (
    AddDiagnosticReportResultPayload,
    DiagnosticReportResultResponse,
    InvalidateDiagnosticReportResultPayload,
    InvalidateReportAttachmentPayload,
    ReportAttachmentResponse,
    UpdateDiagnosticReportResultPayload,
    UploadReportAttachmentPayload,
)
from src.api.specialties.domain.records import (
    CaptureSpecialtyRecordPayload,
    InvalidateSpecialtyRecordPayload,
    SpecialtyRecordHistoryResponse,
    SpecialtyRecordResponse,
    UpdateSpecialtyRecordPayload,
)
from src.api.specialties.domain.templates import (
    CreateSpecialtyTemplatePayload,
    RetireSpecialtyTemplatePayload,
    SpecialtyTemplateHistoryResponse,
    SpecialtyTemplateResponse,
    UpdateSpecialtyTemplatePayload,
)
from src.api.specialties.domain.odontogram import (
    AddDentalTreatmentPayload,
    DentalFindingHistoryResponse,
    DentalFindingResponse,
    DentalTreatmentHistoryResponse,
    DentalTreatmentResponse,
    InvalidateDentalFindingPayload,
    InvalidateDentalTreatmentPayload,
    RecordDentalFindingPayload,
    ResolveDentalFindingPayload,
    UpdateDentalFindingPayload,
    UpdateDentalTreatmentPayload,
)
from src.api.medications.domain.medications import (
    DeclaredMedicationResponse,
    DeclarePatientMedicationPayload,
    InvalidatePatientDeclaredMedicationPayload,
    UpdatePatientDeclaredMedicationPayload,
)
from src.api.medications.domain.reviews import ReviewPatientDeclaredMedicationPayload
from src.api.encounters.domain.encounters import (
    CreatePatientEncounterPayload,
    InvalidatePatientEncounterPayload,
    PatientEncounterResponse,
    UpdatePatientEncounterPayload,
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
ALLERGY_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientAllergyIntolerance": CreatePatientAllergyIntolerancePayload,
    "UpdatePatientAllergyIntolerance": UpdatePatientAllergyIntolerancePayload,
    "InvalidatePatientAllergyIntolerance": InvalidatePatientAllergyIntolerancePayload,
}


CONDITION_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientCondition": CreatePatientConditionPayload,
    "UpdatePatientCondition": UpdatePatientConditionPayload,
    "InvalidatePatientCondition": InvalidatePatientConditionPayload,
    "SetPatientClinicalSectionReview": SetPatientClinicalSectionReviewPayload,
}


ANTECEDENT_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientAntecedent": CreatePatientAntecedentPayload,
    "UpdatePatientAntecedent": UpdatePatientAntecedentPayload,
    "InvalidatePatientAntecedent": InvalidatePatientAntecedentPayload,
}


IMMUNIZATION_SCHEMAS: dict[str, type[BaseModel]] = {
    "RecordPatientImmunization": RecordPatientImmunizationPayload,
    "UpdatePatientImmunization": UpdatePatientImmunizationPayload,
    "InvalidatePatientImmunization": InvalidatePatientImmunizationPayload,
}


CARE_PLAN_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientCarePlan": CreatePatientCarePlanPayload,
    "UpdatePatientCarePlan": UpdatePatientCarePlanPayload,
    "InvalidatePatientCarePlan": InvalidatePatientCarePlanPayload,
    "AddCarePlanGoal": AddCarePlanGoalPayload,
    "UpdateCarePlanGoal": UpdateCarePlanGoalPayload,
    "EvaluateCarePlanGoal": EvaluateCarePlanGoalPayload,
    "InvalidateCarePlanGoal": InvalidateCarePlanGoalPayload,
    "AddCarePlanAction": AddCarePlanActionPayload,
    "UpdateCarePlanAction": UpdateCarePlanActionPayload,
    "CompleteCarePlanAction": CompleteCarePlanActionPayload,
    "InvalidateCarePlanAction": InvalidateCarePlanActionPayload,
    "AddCarePlanReview": AddCarePlanReviewPayload,
    "InvalidateCarePlanReview": InvalidateCarePlanReviewPayload,
}


DIAGNOSTIC_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateDiagnosticReport": CreateDiagnosticReportPayload,
    "UpdateDiagnosticReport": UpdateDiagnosticReportPayload,
    "CorrectDiagnosticReport": CorrectDiagnosticReportPayload,
    "AddDiagnosticReportResult": AddDiagnosticReportResultPayload,
    "UpdateDiagnosticReportResult": UpdateDiagnosticReportResultPayload,
    "InvalidateDiagnosticReportResult": InvalidateDiagnosticReportResultPayload,
    "UploadReportAttachment": UploadReportAttachmentPayload,
    "InvalidateReportAttachment": InvalidateReportAttachmentPayload,
}


SPECIALTY_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreateSpecialtyTemplate": CreateSpecialtyTemplatePayload,
    "UpdateSpecialtyTemplate": UpdateSpecialtyTemplatePayload,
    "RetireSpecialtyTemplate": RetireSpecialtyTemplatePayload,
    "CaptureSpecialtyRecord": CaptureSpecialtyRecordPayload,
    "UpdateSpecialtyRecord": UpdateSpecialtyRecordPayload,
    "InvalidateSpecialtyRecord": InvalidateSpecialtyRecordPayload,
}


DENTAL_SCHEMAS: dict[str, type[BaseModel]] = {
    "RecordDentalFinding": RecordDentalFindingPayload,
    "UpdateDentalFinding": UpdateDentalFindingPayload,
    "ResolveDentalFinding": ResolveDentalFindingPayload,
    "InvalidateDentalFinding": InvalidateDentalFindingPayload,
    "AddDentalTreatment": AddDentalTreatmentPayload,
    "UpdateDentalTreatment": UpdateDentalTreatmentPayload,
    "InvalidateDentalTreatment": InvalidateDentalTreatmentPayload,
}


MEDICATION_SCHEMAS: dict[str, type[BaseModel]] = {
    "DeclarePatientMedication": DeclarePatientMedicationPayload,
    "UpdatePatientDeclaredMedication": UpdatePatientDeclaredMedicationPayload,
    "ReviewPatientDeclaredMedication": ReviewPatientDeclaredMedicationPayload,
    "InvalidatePatientDeclaredMedication": InvalidatePatientDeclaredMedicationPayload,
}


MEASUREMENT_SCHEMAS: dict[str, type[BaseModel]] = {
    "RecordPatientMeasurement": RecordPatientMeasurementPayload,
    "CorrectPatientMeasurement": CorrectPatientMeasurementPayload,
    "InvalidatePatientMeasurement": InvalidatePatientMeasurementPayload,
}


NOTE_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientNote": CreatePatientNotePayload,
    "UpdatePatientNote": UpdatePatientNotePayload,
    "InvalidatePatientNote": InvalidatePatientNotePayload,
}


ENCOUNTER_SCHEMAS: dict[str, type[BaseModel]] = {
    "CreatePatientEncounter": CreatePatientEncounterPayload,
    "UpdatePatientEncounter": UpdatePatientEncounterPayload,
    "InvalidatePatientEncounter": InvalidatePatientEncounterPayload,
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
    "SetMemberClinicalPermissions": ClinicalPermissionsPayload,
    "UpdateAccountDetails": AccountDetailsPatch,
    "UpdateAccountPolicy": AccountPolicyPayload,
    "SetAccountStatus": MembershipStatusPayload,
    "UpdateProfessionalProfile": ProfessionalPayload,
    "RegisterPatient": RegisterPatientPayload,
    "UpdatePatientProfile": PatientPatch,
    "SetPatientProfileStatus": PatientStatusPayload,
    "SetPatientCompletion": PatientCompletionPayload,
    "AddPatientIdentifier": AddPatientIdentifierPayload,
    "SetPatientSexAtBirth": SetPatientSexAtBirthPayload,
    **CONDITION_SCHEMAS,
    **ALLERGY_SCHEMAS,
    **ENCOUNTER_SCHEMAS,
    **NOTE_SCHEMAS,
    **MEASUREMENT_SCHEMAS,
    **IMMUNIZATION_SCHEMAS,
    **ANTECEDENT_SCHEMAS,
    **MEDICATION_SCHEMAS,
    **CARE_PLAN_SCHEMAS,
    **DIAGNOSTIC_SCHEMAS,
    **SPECIALTY_SCHEMAS,
    **DENTAL_SCHEMAS,
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
    | MemberClinicalPermissionsResponse
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
    | ClinicalProfileResponse
    | PatientConditionResponse
    | ClinicalSectionReviewResponse
    | PatientAllergyIntoleranceResponse
    | PatientEncounterResponse
    | PatientNoteResponse
    | PatientMeasurementResponse
    | PatientImmunizationResponse
    | PatientAntecedentResponse
    | DeclaredMedicationResponse
    | CarePlanResponse
    | CarePlanGoalResponse
    | CarePlanActionResponse
    | CarePlanReviewResponse
    | DiagnosticReportResponse
    | DiagnosticReportResultResponse
    | ReportAttachmentResponse
    | SpecialtyTemplateResponse
    | SpecialtyRecordResponse
    | DentalFindingResponse
    | DentalTreatmentResponse
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
