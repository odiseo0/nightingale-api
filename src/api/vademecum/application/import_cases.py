import hashlib
import json
from typing import TYPE_CHECKING
from uuid import uuid7

from pydantic import ValidationError

from src.api.vademecum.domain.catalog import (
    VademecumImportSummary,
    normalize_search_text,
)
from src.api.vademecum.domain.errors import VademecumImportError
from src.api.vademecum.domain.monographs import Monograph
from src.api.vademecum.domain.products import VademecumDataset, VademecumSourceProduct
from src.api.vademecum.repository.dao import dao_vademecum
from src.api.vademecum.repository.models import (
    VademecumMonograph,
    VademecumProduct,
    VademecumProductIngredient,
    VademecumProductMonograph,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.utils.utils import Empty, to_slug

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


IMPORT_BATCH_SIZE = 500


def monograph_search_text(monograph: Monograph) -> str:
    return normalize_search_text(
        " ".join([monograph.name, *monograph.sismed_aliases, monograph.atc.code])
    )


def product_search_text(
    product: VademecumSourceProduct, monographs: dict[str, Monograph]
) -> str:
    values = [
        product.name,
        product.registration_number,
        product.active_ingredient_text,
        *product.canonical_ingredient_ids,
    ]

    for monograph_id in product.monograph_ids:
        monograph = monographs[monograph_id]
        values.extend([monograph.name, *monograph.sismed_aliases, monograph.atc.code])

    return normalize_search_text(" ".join(values))


def validate_vademecum(content: bytes) -> VademecumDataset:
    try:
        dataset = VademecumDataset.model_validate(json.loads(content))
    except json.JSONDecodeError, UnicodeDecodeError, ValidationError:
        raise VademecumImportError("Invalid vademecum dataset") from None

    registrations = [product.registration_number for product in dataset.products]
    monograph_ids = [monograph.id for monograph in dataset.monographs]

    if len(registrations) != len(set(registrations)):
        raise VademecumImportError("Duplicate product registration")

    if len(monograph_ids) != len(set(monograph_ids)):
        raise VademecumImportError("Duplicate monograph ID")

    known_ids = set(monograph_ids)

    for product in dataset.products:
        references = set(product.monograph_ids) | set(product.combination_monograph_ids)

        if product.product_monograph_reference is not None:
            references |= set(product.product_monograph_reference.monograph_ids)

        if not references <= known_ids:
            raise VademecumImportError("Product references a missing monograph")

    products = dataset.products
    expected_statistics = {
        "products": len(products),
        "products_with_monograph": sum(bool(p.monograph_ids) for p in products),
        "products_without_monograph": sum(not p.monograph_ids for p in products),
        "products_without_active_ingredient": sum(
            not p.active_ingredient_text for p in products
        ),
        "distinct_active_ingredients": len(
            {
                to_slug(p.active_ingredient_text)
                for p in products
                if p.active_ingredient_text
            }
        ),
        "linked_active_ingredients": len(
            {
                to_slug(p.active_ingredient_text)
                for p in products
                if p.ingredient_link_status in {"complete", "partial"}
                and p.active_ingredient_text
            }
        ),
        "complete_ingredient_coverage": sum(
            p.ingredient_link_status == "complete" for p in products
        ),
        "partial_ingredient_coverage": sum(
            p.ingredient_link_status == "partial" for p in products
        ),
        "products_with_inferred_ingredients": sum(
            p.ingredient_resolution == "product_name_inference" for p in products
        ),
        "products_with_historical_matches": sum(
            p.ingredient_resolution == "historical_product_match" for p in products
        ),
        "products_with_supplementary_data": sum(
            bool(p.supplementary_ingredient_ids) for p in products
        ),
        "products_with_combination_monograph": sum(
            bool(p.combination_monograph_ids) for p in products
        ),
        "products_with_product_reference": sum(
            p.product_monograph_reference is not None for p in products
        ),
        "available_monographs": len(dataset.monographs),
        "linked_monographs": len(
            {id_ for p in products for id_ in p.monograph_ids}
            | {
                id_
                for product in dataset.historical_products
                for id_ in product.monograph_ids
            }
        ),
    }
    actual_statistics = dataset.statistics.model_dump()

    for field, expected in expected_statistics.items():
        if actual_statistics[field] != expected:
            raise VademecumImportError(f"Dataset statistic mismatch: {field}")

    return dataset


async def import_vademecum(
    db: AsyncSession, content: bytes
) -> Result[VademecumImportSummary, VademecumImportError]:
    try:
        dataset = validate_vademecum(content)
    except VademecumImportError as error:
        return Err(error)

    source_sha256 = hashlib.sha256(content).hexdigest()

    async with transaction(db):
        existing = await dao_vademecum.get_by(
            db, where={"source_sha256": source_sha256}
        )

        if existing is not Empty:
            return Ok(
                VademecumImportSummary(
                    dataset_id=existing.id,
                    source_sha256=source_sha256,
                    products=len(dataset.products),
                    monographs=len(dataset.monographs),
                    status="existing",
                )
            )

        dataset_id = uuid7()
        await dao_vademecum.insert_dataset(
            db,
            dataset_id,
            source_sha256,
            dataset.schema_version,
            dataset.registry_cutoff_date,
            dataset.medical_notice,
        )

        monographs = {monograph.id: monograph for monograph in dataset.monographs}
        product_rows = []
        ingredient_rows = []
        link_rows = []

        for product in dataset.products:
            product_rows.append(
                {
                    "dataset_id": dataset_id,
                    "registration_number": product.registration_number,
                    "name": product.name,
                    "active_ingredient_text": product.active_ingredient_text,
                    "approved_at": product.approved_at,
                    "valid_until": product.valid_until,
                    "representative": product.representative,
                    "manufacturer": product.manufacturer,
                    "ingredient_link_status": product.ingredient_link_status,
                    "ingredient_resolution": product.ingredient_resolution,
                    "product_reference": (
                        product.product_monograph_reference.model_dump(
                            mode="json", by_alias=True
                        )
                        if product.product_monograph_reference is not None
                        else None
                    ),
                    "search_text": product_search_text(product, monographs),
                }
            )
            ingredient_rows.extend(
                {
                    "dataset_id": dataset_id,
                    "registration_number": product.registration_number,
                    "ingredient_id": ingredient_id,
                }
                for ingredient_id in product.canonical_ingredient_ids
            )
            combination_ids = set(product.combination_monograph_ids)
            linked_ids = list(product.monograph_ids)
            linked_ids.extend(
                id_
                for id_ in product.combination_monograph_ids
                if id_ not in product.monograph_ids
            )
            link_rows.extend(
                {
                    "dataset_id": dataset_id,
                    "registration_number": product.registration_number,
                    "monograph_id": monograph_id,
                    "combination": monograph_id in combination_ids,
                }
                for monograph_id in linked_ids
            )

        monograph_rows = [
            {
                "dataset_id": dataset_id,
                "id": monograph.id,
                "name": monograph.name,
                "atc_code": monograph.atc.code,
                "document": monograph.model_dump(mode="json", by_alias=True),
                "search_text": monograph_search_text(monograph),
            }
            for monograph in dataset.monographs
        ]

        for model, rows in (
            (VademecumProduct, product_rows),
            (VademecumProductIngredient, ingredient_rows),
            (VademecumMonograph, monograph_rows),
            (VademecumProductMonograph, link_rows),
        ):
            for start in range(0, len(rows), IMPORT_BATCH_SIZE):
                await dao_vademecum.insert_batch(
                    db, model, rows[start : start + IMPORT_BATCH_SIZE]
                )

        await dao_vademecum.activate(db, dataset_id)

    return Ok(
        VademecumImportSummary(
            dataset_id=dataset_id,
            source_sha256=source_sha256,
            products=len(dataset.products),
            monographs=len(dataset.monographs),
            status="imported",
        )
    )
