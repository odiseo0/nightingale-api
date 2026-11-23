from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.accounts_cases import get_account_context
from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.vademecum.domain.catalog import (
    VademecumCatalogContext,
    VademecumMonographPage,
    VademecumMonographQuery,
    VademecumMonographResponse,
    VademecumMonographSummary,
    VademecumProductPage,
    VademecumProductQuery,
    VademecumProductResponse,
)
from src.api.vademecum.domain.errors import VademecumNotFound, VademecumUnavailable
from src.api.vademecum.domain.monographs import Monograph
from src.api.vademecum.domain.products import (
    VademecumProduct,
    VademecumProductReference,
)
from src.api.vademecum.repository.dao import dao_vademecum
from src.api.vademecum.repository.models import (
    VademecumDataset,
    VademecumProductIngredient,
    VademecumProductMonograph,
)
from src.api.vademecum.repository.models import (
    VademecumMonograph as MonographRow,
)
from src.api.vademecum.repository.models import (
    VademecumProduct as ProductRow,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


ReadAccessError = InvalidCredential | AccountNotFound | AccessDenied


def catalog_context(dataset: VademecumDataset) -> VademecumCatalogContext:
    return VademecumCatalogContext(
        schema_version=dataset.schema_version,
        registry_cutoff_date=dataset.registry_cutoff_date,
        medical_notice=dataset.medical_notice,
        source_sha256=dataset.source_sha256,
    )


def product_projection(
    row: ProductRow,
    links: list[VademecumProductMonograph],
    ingredients: list[VademecumProductIngredient],
) -> VademecumProduct:
    return VademecumProduct(
        registration_number=row.registration_number,
        name=row.name,
        active_ingredient_text=row.active_ingredient_text,
        approved_at=row.approved_at,
        valid_until=row.valid_until,
        representative=row.representative,
        manufacturer=row.manufacturer,
        monograph_ids=sorted(link.monograph_id for link in links),
        combination_monograph_ids=sorted(
            link.monograph_id for link in links if link.combination
        ),
        canonical_ingredient_ids=sorted(
            ingredient.ingredient_id for ingredient in ingredients
        ),
        ingredient_link_status=row.ingredient_link_status,
        ingredient_resolution=row.ingredient_resolution,
        product_reference=(
            VademecumProductReference.model_validate(row.product_reference)
            if row.product_reference is not None
            else None
        ),
    )


async def authorized_dataset(
    db: AsyncSession, credential: str | None, account_id: UUID
) -> Result[VademecumDataset, ReadAccessError | VademecumUnavailable]:
    result = await get_account_context(db, credential, account_id, require_device=True)

    match result:
        case Ok(context):
            if context.account.status != "active":
                return Err(AccessDenied())
        case Err(error):
            return Err(error)

    dataset = await dao_vademecum.active_dataset(db)

    if dataset is Empty:
        return Err(VademecumUnavailable())

    return Ok(dataset)


async def read_products(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: VademecumProductQuery,
) -> Result[VademecumProductPage, ReadAccessError | VademecumUnavailable]:
    async with transaction(db):
        result = await authorized_dataset(db, credential, account_id)

        match result:
            case Ok(dataset):
                pass
            case Err(error):
                return Err(error)

        rows, links, ingredients, total = await dao_vademecum.product_page(
            db, dataset.id, query
        )
        links_by_product: dict[str, list[VademecumProductMonograph]] = {}
        ingredients_by_product: dict[str, list[VademecumProductIngredient]] = {}

        for link in links:
            links_by_product.setdefault(link.registration_number, []).append(link)

        for ingredient in ingredients:
            ingredients_by_product.setdefault(
                ingredient.registration_number, []
            ).append(ingredient)

        response = VademecumProductPage(
            catalog=catalog_context(dataset),
            items=[
                product_projection(
                    row,
                    links_by_product.get(row.registration_number, []),
                    ingredients_by_product.get(row.registration_number, []),
                )
                for row in rows
            ],
            total=total,
        )

    return Ok(response)


async def read_product(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    registration_number: str,
) -> Result[
    VademecumProductResponse,
    ReadAccessError | VademecumUnavailable | VademecumNotFound,
]:
    async with transaction(db):
        result = await authorized_dataset(db, credential, account_id)

        match result:
            case Ok(dataset):
                pass
            case Err(error):
                return Err(error)

        row = await dao_vademecum.product_detail(db, dataset.id, registration_number)

        if row is Empty:
            return Err(VademecumNotFound())

        product, links, ingredients = row
        response = VademecumProductResponse(
            catalog=catalog_context(dataset),
            product=product_projection(product, links, ingredients),
        )

    return Ok(response)


def monograph_summary(row: MonographRow) -> VademecumMonographSummary:
    document = Monograph.model_validate(row.document)

    return VademecumMonographSummary(
        id=document.id,
        name=document.name,
        sismed_aliases=document.sismed_aliases,
        atc=document.atc,
        review=document.review,
    )


async def read_monographs(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: VademecumMonographQuery,
) -> Result[VademecumMonographPage, ReadAccessError | VademecumUnavailable]:
    async with transaction(db):
        result = await authorized_dataset(db, credential, account_id)

        match result:
            case Ok(dataset):
                pass
            case Err(error):
                return Err(error)

        rows, total = await dao_vademecum.monograph_page(db, dataset.id, query)
        response = VademecumMonographPage(
            catalog=catalog_context(dataset),
            items=[monograph_summary(row) for row in rows],
            total=total,
        )

    return Ok(response)


async def read_monograph(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    monograph_id: str,
) -> Result[
    VademecumMonographResponse,
    ReadAccessError | VademecumUnavailable | VademecumNotFound,
]:
    async with transaction(db):
        result = await authorized_dataset(db, credential, account_id)

        match result:
            case Ok(dataset):
                pass
            case Err(error):
                return Err(error)

        row = await dao_vademecum.monograph_detail(db, dataset.id, monograph_id)

        if row is Empty:
            return Err(VademecumNotFound())

        response = VademecumMonographResponse(
            catalog=catalog_context(dataset),
            monograph=Monograph.model_validate(row.document),
        )

    return Ok(response)
