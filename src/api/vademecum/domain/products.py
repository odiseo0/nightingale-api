from datetime import UTC, date, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
)

from src.api.vademecum.domain.monographs import (
    Monograph,
    MonographId,
    Uri,
    unique_strings,
)
from src.core.schema import BaseModel
from src.core.schema.http import SerializedInstant


class ProductModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


def registry_instant(value: object) -> object:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo("America/Caracas"))

    return value


RegistryInstant = Annotated[AwareDatetime, BeforeValidator(registry_instant)]


def empty_manufacturer(value: str | None) -> str | None:
    return None if value is not None and not value.strip() else value


IngredientLinkStatus = Literal[
    "complete",
    "unlinked",
    "missing_ingredient",
    "historical_complete",
    "product_reference",
    "inferred_complete",
    "combination_only",
    "historical_partial",
    "inferred_partial",
    "partial",
]
IngredientResolution = Literal[
    "source_text",
    "historical_product_match",
    "unresolved",
    "product_name_inference",
    "product_reference",
]
UniqueMonographIds = Annotated[list[MonographId], AfterValidator(unique_strings)]


class VademecumReferenceSource(ProductModel):
    title: str
    url: Uri


class VademecumProductReference(ProductModel):
    scope: str
    monograph_ids: UniqueMonographIds
    sources: list[VademecumReferenceSource]
    match_note: str


class VademecumSourceProduct(ProductModel):
    registration_number: Annotated[str, Field(alias="ef", min_length=1)]
    sort_id: int
    id: int
    rif_representante: str | None
    active_ingredient_text: Annotated[str, Field(alias="principioActivo")]
    approved_at: Annotated[RegistryInstant, Field(alias="fechaAprobado")]
    valid_until: Annotated[RegistryInstant, Field(alias="fechaVigencia")]
    cancelled_at: Annotated[RegistryInstant | None, Field(alias="fechaCancelado")]
    name: Annotated[str, Field(alias="nombre", min_length=1)]
    representative: Annotated[str, Field(alias="representante", min_length=1)]
    manufacturer: Annotated[
        str | None, Field(alias="fabricante"), AfterValidator(empty_manufacturer)
    ]
    premium: bool
    sponsor: Annotated[str | None, Field(alias="patrocinante")]
    oficios: list[dict[str, object]]
    monograph_ids: UniqueMonographIds
    combination_monograph_ids: UniqueMonographIds
    ingredient_link_status: IngredientLinkStatus
    canonical_ingredient_ids: UniqueMonographIds
    supplementary_ingredient_ids: list[str]
    ingredient_resolution: IngredientResolution
    product_monograph_reference: VademecumProductReference | None = None

    def public(self) -> VademecumProduct:
        return VademecumProduct(
            registration_number=self.registration_number,
            name=self.name,
            active_ingredient_text=self.active_ingredient_text,
            approved_at=self.approved_at,
            valid_until=self.valid_until,
            representative=self.representative,
            manufacturer=self.manufacturer,
            monograph_ids=self.monograph_ids,
            combination_monograph_ids=self.combination_monograph_ids,
            canonical_ingredient_ids=self.canonical_ingredient_ids,
            ingredient_link_status=self.ingredient_link_status,
            ingredient_resolution=self.ingredient_resolution,
            product_reference=self.product_monograph_reference,
        )


class VademecumProduct(ProductModel):
    registration_number: str
    name: str
    active_ingredient_text: str
    approved_at: AwareDatetime
    valid_until: AwareDatetime
    representative: str
    manufacturer: str | None
    monograph_ids: list[MonographId]
    combination_monograph_ids: list[MonographId]
    canonical_ingredient_ids: list[MonographId]
    ingredient_link_status: IngredientLinkStatus
    ingredient_resolution: IngredientResolution
    product_reference: VademecumProductReference | None

    @field_serializer("approved_at", "valid_until")
    def serialize_instants(self, value: datetime) -> SerializedInstant:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class VademecumRegistrySource(ProductModel):
    name: str
    file: str


class VademecumHistoricalSource(ProductModel):
    file: str
    title: str
    country: str
    publication_date: str
    historical: Literal[True]
    evidence_of_current_approval: Literal[False]


class VademecumStatistics(ProductModel):
    products: Annotated[int, Field(ge=0)]
    products_with_monograph: Annotated[int, Field(ge=0)]
    products_without_monograph: Annotated[int, Field(ge=0)]
    products_without_active_ingredient: Annotated[int, Field(ge=0)]
    distinct_active_ingredients: Annotated[int, Field(ge=0)]
    linked_active_ingredients: Annotated[int, Field(ge=0)]
    complete_ingredient_coverage: Annotated[int, Field(ge=0)]
    partial_ingredient_coverage: Annotated[int, Field(ge=0)]
    products_with_inferred_ingredients: Annotated[int, Field(ge=0)]
    products_with_historical_matches: Annotated[int, Field(ge=0)]
    products_with_supplementary_data: Annotated[int, Field(ge=0)]
    products_with_combination_monograph: Annotated[int, Field(ge=0)]
    products_with_product_reference: Annotated[int, Field(ge=0)]
    historical_products: Annotated[int, Field(ge=0)]
    historical_products_with_monograph: Annotated[int, Field(ge=0)]
    historical_products_without_monograph: Annotated[int, Field(ge=0)]
    historical_products_without_active_ingredient: Annotated[int, Field(ge=0)]
    historical_distinct_active_ingredients: Annotated[int, Field(ge=0)]
    historical_linked_active_ingredients: Annotated[int, Field(ge=0)]
    historical_complete_ingredient_coverage: Annotated[int, Field(ge=0)]
    historical_partial_ingredient_coverage: Annotated[int, Field(ge=0)]
    historical_products_with_inferred_ingredients: Annotated[int, Field(ge=0)]
    historical_products_with_historical_matches: Annotated[int, Field(ge=0)]
    historical_products_with_supplementary_data: Annotated[int, Field(ge=0)]
    historical_products_with_combination_monograph: Annotated[int, Field(ge=0)]
    available_monographs: Annotated[int, Field(ge=0)]
    linked_monographs: Annotated[int, Field(ge=0)]


class VademecumHistoricalProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    monograph_ids: list[str]


class VademecumDataset(ProductModel):
    schema_version: Literal["1.0.0"]
    registry_cutoff_date: date
    registry_source: VademecumRegistrySource
    historical_source: VademecumHistoricalSource
    linking_method: str
    medical_notice: Annotated[str, Field(min_length=1)]
    statistics: VademecumStatistics
    monographs: list[Monograph]
    products: list[VademecumSourceProduct]
    historical_products: list[VademecumHistoricalProduct]
    supplementary_ingredients: list[dict[str, object]]
