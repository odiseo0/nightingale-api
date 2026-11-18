from decimal import Decimal
from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.core.schema import BaseModel

ResultKind = Literal["numeric", "text"]


class DiagnosticReportResultFields(BaseModel):
    analyte_name: str = Field(min_length=1)
    result_kind: ResultKind
    value: Decimal | None = None
    text_value: str | None = Field(default=None, min_length=1)
    unit: str | None = Field(default=None, min_length=1)
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    reference_text: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def shape(self) -> Self:
        if self.result_kind is None:
            return self

        if self.result_kind == "numeric":
            if self.value is None or self.unit is None or self.text_value is not None:
                raise ValueError("El resultado numérico exige valor y unidad")
        elif self.text_value is None or self.value is not None or self.unit is not None:
            raise ValueError("El resultado textual exige texto sin valor ni unidad")

        has_interval = self.reference_low is not None or self.reference_high is not None
        if has_interval and self.reference_text is not None:
            raise ValueError("Una sola referencia por resultado")
        if (
            self.reference_low is not None
            and self.reference_high is not None
            and self.reference_high < self.reference_low
        ):
            raise ValueError("La referencia alta no puede ser menor")

        return self


class AddDiagnosticReportResultPayload(DiagnosticReportResultFields):
    report_id: UUID7
    patient_id: UUID7


class UpdateDiagnosticReportResultPayload(DiagnosticReportResultFields):
    analyte_name: str | None = Field(default=None, min_length=1)
    result_kind: ResultKind | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")
        return self


class InvalidateDiagnosticReportResultPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class DiagnosticReportResultResponse(DiagnosticReportResultFields):
    result_id: UUID7
    report_id: UUID7
    patient_id: UUID7
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class DiagnosticReportResultHistoryResponse(DiagnosticReportResultResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class ReportAttachmentResponse(BaseModel):
    attachment_id: UUID7
    report_id: UUID7 | None
    file_name: str
    content_type: str
    byte_size: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    uploaded_at: AwareDatetime
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    model_config = ConfigDict(extra="forbid", validate_default=True)


class UploadReportAttachmentPayload(BaseModel):
    patient_id: UUID7
    report_id: UUID7 | None = None
    file_name: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    byte_size: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    content_base64: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)


class InvalidateReportAttachmentPayload(BaseModel):
    correction_reason: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "AddDiagnosticReportResultPayload",
    "DiagnosticReportResultFields",
    "DiagnosticReportResultHistoryResponse",
    "DiagnosticReportResultResponse",
    "InvalidateDiagnosticReportResultPayload",
    "InvalidateReportAttachmentPayload",
    "ReportAttachmentResponse",
    "ResultKind",
    "UpdateDiagnosticReportResultPayload",
    "UploadReportAttachmentPayload",
]
