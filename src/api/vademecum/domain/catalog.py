from datetime import date
from typing import Annotated, Literal
from unicodedata import combining, normalize
from uuid import UUID

from pydantic import ConfigDict, Field

from src.api.vademecum.domain.monographs import (
    Monograph,
    MonographAtc,
    MonographId,
    MonographReview,
)
from src.api.vademecum.domain.products import VademecumProduct
from src.core.schema import BaseModel, PageQuery


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VademecumCatalogContext(CatalogModel):
    schema_version: str
    registry_cutoff_date: date
    medical_notice: str
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class VademecumImportSummary(CatalogModel):
    dataset_id: UUID
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    products: Annotated[int, Field(ge=0)]
    monographs: Annotated[int, Field(ge=0)]
    status: Literal["imported", "existing"]


def normalize_search_text(value: str) -> str:
    decomposed = normalize("NFKD", value)
    unaccented = "".join(char for char in decomposed if not combining(char))
    return " ".join(unaccented.lower().split())


class VademecumProductQuery(PageQuery):
    q: str | None = None
    monograph_id: MonographId | None = None


class VademecumMonographQuery(PageQuery):
    q: str | None = None


class VademecumProductPage(CatalogModel):
    catalog: VademecumCatalogContext
    items: list[VademecumProduct]
    total: Annotated[int, Field(ge=0)]


class VademecumProductResponse(CatalogModel):
    catalog: VademecumCatalogContext
    product: VademecumProduct


class VademecumMonographSummary(CatalogModel):
    id: MonographId
    name: str
    sismed_aliases: list[str]
    atc: MonographAtc
    review: MonographReview


class VademecumMonographPage(CatalogModel):
    catalog: VademecumCatalogContext
    items: list[VademecumMonographSummary]
    total: Annotated[int, Field(ge=0)]


class VademecumMonographResponse(CatalogModel):
    catalog: VademecumCatalogContext
    monograph: Monograph
