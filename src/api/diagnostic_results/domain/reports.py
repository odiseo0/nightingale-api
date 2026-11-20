from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.api.clinical_records.domain.clinical import ClinicalSourceType
from src.api.clinical_records.domain.conditions import ClinicalDate
from src.api.diagnostic_results.domain.results import CorrectDiagnosticReportResultPayload
from src.core.schema import BaseModel, PageQuery

ReportKind = Literal["laboratory", "imaging", "pathology", "other"]
ReportStatus = Literal["preliminary", "final"]


class DiagnosticReportFields(BaseModel):
    source_name: str = Field(min_length=1)
    attachment_id: UUID7 | None = None
    source_type: ClinicalSourceType = "unknown"
    sample_date: ClinicalDate | None = None
    issued_date: ClinicalDate | None = None
    report_kind: ReportKind
    report_status: ReportStatus
    clinical_summary: str | None = Field(default=None, min_length=1)
    captured_at_local: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid", validate_default=True)


class CreateDiagnosticReportPayload(DiagnosticReportFields):
    patient_id: UUID7
    encounter_id: UUID7 | None = None


class UpdateDiagnosticReportPayload(DiagnosticReportFields):
    source_name: str | None = Field(default=None, min_length=1)
    report_kind: ReportKind | None = None
    report_status: ReportStatus | None = None
    correction_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        for name in ("source_name", "report_kind", "report_status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Un campo presente no puede ser nulo")

        return self


class CorrectDiagnosticReportPayload(BaseModel):
    correction_reason: str = Field(min_length=1)
    results: list[CorrectDiagnosticReportResultPayload]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def unique_result_ids(self) -> Self:
        ids = [result.result_id for result in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("Los resultados no pueden repetir resultId")
        return self


class DiagnosticReportResponse(DiagnosticReportFields):
    report_id: UUID7
    patient_id: UUID7
    encounter_id: UUID7 | None
    attachment_id: UUID7 | None
    record_status: Literal["valid", "entered-in-error"]
    correction_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class DiagnosticReportHistoryResponse(DiagnosticReportResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class DiagnosticReportQuery(PageQuery):
    report_kind: ReportKind | None = None
    report_status: ReportStatus | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None


__all__ = [
    "CorrectDiagnosticReportPayload",
    "CreateDiagnosticReportPayload",
    "DiagnosticReportFields",
    "DiagnosticReportHistoryResponse",
    "DiagnosticReportQuery",
    "DiagnosticReportResponse",
    "ReportKind",
    "ReportStatus",
    "UpdateDiagnosticReportPayload",
]
