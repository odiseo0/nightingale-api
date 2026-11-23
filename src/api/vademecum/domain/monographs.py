from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, ConfigDict, Field

from src.core.schema import BaseModel


class MonographModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


def unique_strings(value: list[str]) -> list[str]:
    if len(value) != len(set(value)):
        raise ValueError("Duplicate values are not allowed")

    return value


def valid_uri(value: str) -> str:
    if not urlsplit(value).scheme:
        raise ValueError("An absolute URI is required")

    return value


NonEmptyString = Annotated[str, Field(min_length=1)]
Uri = Annotated[str, AfterValidator(valid_uri), Field(json_schema_extra={"format": "uri"})]
UniqueStrings = Annotated[list[str], AfterValidator(unique_strings)]
UniqueNonEmptyStrings = Annotated[
    list[NonEmptyString], AfterValidator(unique_strings)
]
MonographId = Annotated[
    str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
]

IndicationType = Literal["primary", "secondary", "off_label"]
AlertSeverity = Literal["informational", "important", "critical"]
InteractionType = Literal["drug", "food", "laboratory", "other"]
AdverseEffectType = Literal["systemic", "localized", "unspecified"]
AdverseEffectFrequency = Literal[
    "very_common", "common", "uncommon", "rare", "very_rare", "unknown"
]
PopulationStatus = Literal[
    "contraindicated",
    "not_recommended",
    "assess_risk_benefit",
    "dose_adjustment_required",
    "no_adjustment",
    "no_data",
    "review_required",
]
Trimester = Literal["1T", "2T", "3T"]
ExtractionMethod = Literal[
    "manual", "source_section", "source_summary", "automated_table_extraction"
]
ReviewStatus = Literal["pending_local_review", "reviewed"]


class MonographAtc(MonographModel):
    code: str
    description: str


class MonographIndication(MonographModel):
    name: str
    type: IndicationType


class MonographAlert(MonographModel):
    name: str
    description: str
    severity: AlertSeverity


class MonographPosology(MonographModel):
    indication: str
    route: str
    pharmaceutical_form: str
    specific_indication: str | None
    population: str
    usual_dose: str
    common_adjustments: str | None
    maximum_frequency: str | None
    monitoring: str | None


class MonographForm(MonographModel):
    substance: str
    concentration: str
    pharmaceutical_form: str


class MonographReferenceSpecialty(MonographModel):
    name: str
    concentration: str
    pharmaceutical_form: str
    country: str


class MonographPopulation(MonographModel):
    status: PopulationStatus
    label: str
    detail: str


class MonographPregnancyPopulation(MonographPopulation):
    trimesters: Annotated[list[Trimester], AfterValidator(unique_strings)]


class MonographContraindication(MonographModel):
    category: str
    title: str
    description: str


class MonographInteraction(MonographModel):
    type: InteractionType
    agent: str
    description: str


class MonographAdverseEffect(MonographModel):
    name: str
    system: str
    type: AdverseEffectType
    frequency: AdverseEffectFrequency
    critical: bool | None
    action: str | None


class MonographSafety(MonographModel):
    contraindications: list[MonographContraindication]
    precautions: UniqueStrings
    interactions: list[MonographInteraction]
    adverse_effects: list[MonographAdverseEffect]


class MonographPharmacologicalSection(MonographModel):
    summary: str
    detail: str


class MonographPharmacologicalProfile(MonographModel):
    administration_and_food: MonographPharmacologicalSection
    metabolism_and_activation: MonographPharmacologicalSection
    duration_and_half_life: MonographPharmacologicalSection
    elimination_and_excretion: MonographPharmacologicalSection


class MonographSpecialPopulations(MonographModel):
    renal_impairment: MonographPopulation
    hepatic_impairment: MonographPopulation
    older_adults: MonographPopulation
    pregnancy: MonographPregnancyPopulation
    breastfeeding: MonographPopulation
    pediatrics: MonographPopulation


class MonographTherapeuticGroup(MonographModel):
    atc_code: str
    associations: UniqueStrings


class MonographSource(MonographModel):
    id: NonEmptyString
    title: str
    url: Uri
    consulted_on: date
    revised_on: str | None
    updated_on: str | None


class MonographProvenance(MonographModel):
    path: Annotated[str, Field(pattern=r"^/")]
    source_id: str
    source_section: str | None
    extraction_method: ExtractionMethod


class MonographReview(MonographModel):
    status: ReviewStatus
    date: date | None
    reviewer: str | None


class Monograph(MonographModel):
    schema_version: Literal["1.0.0"]
    id: MonographId
    name: NonEmptyString
    sismed_aliases: UniqueNonEmptyStrings
    atc: MonographAtc
    therapeutic_overview: str
    mechanism_of_action: str
    indications: list[MonographIndication]
    alerts: list[MonographAlert]
    posology: list[MonographPosology]
    forms: list[MonographForm]
    reference_specialties: list[MonographReferenceSpecialty]
    special_populations: MonographSpecialPopulations
    safety: MonographSafety
    pharmacological_profile: MonographPharmacologicalProfile
    therapeutic_group: MonographTherapeuticGroup
    sources: Annotated[list[MonographSource], Field(min_length=1)]
    provenance: list[MonographProvenance]
    review: MonographReview
