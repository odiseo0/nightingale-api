from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, Field, field_serializer, model_validator

from src.api.accounts.domain.accounts import ClinicalSection
from src.core.schema import BaseModel, PageQuery
from src.core.schema.http import SerializedInstant

type ClinicalEntryType = Literal[
    "encounter",
    "note",
    "measurement",
    "immunization",
    "antecedent",
    "condition",
    "allergy_intolerance",
    "declared_medication",
    "care_plan",
    "diagnostic_report",
    "specialty_record",
]


class ClinicalHistoryQuery(PageQuery):
    sections: list[ClinicalSection] | None = None
    entry_types: list[ClinicalEntryType] | None = None
    record_status: Literal["valid", "entered-in-error"] | None = None
    from_: AwareDatetime | None = Field(default=None, alias="from")
    until: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_filters(self) -> Self:
        for values in (self.sections, self.entry_types):
            if values is not None and len(values) != len(set(values)):
                raise ValueError("Los filtros no admiten duplicados")

        if (
            self.from_ is not None
            and self.until is not None
            and self.from_ >= self.until
        ):
            raise ValueError("El rango debe tener inicio anterior al fin")

        return self


class ClinicalHistoryEntry(BaseModel):
    entry_type: ClinicalEntryType
    entry_id: UUID7
    source_section: ClinicalSection
    occurred_at: AwareDatetime | None
    occurrence_date: str | None
    date_precision: Literal["instant", "year", "month", "day", "reference"]
    accepted_at: AwareDatetime
    entity_version: int
    record_status: Literal["valid", "entered-in-error"]

    @field_serializer("occurred_at", "accepted_at", when_used="unless-none")
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
