from datetime import date
from uuid import UUID

from sqlalchemy import insert, null, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.vademecum.domain.catalog import (
    VademecumMonographQuery,
    VademecumProductQuery,
    normalize_search_text,
)
from src.api.vademecum.repository.models import (
    VademecumDataset,
    VademecumMonograph,
    VademecumProduct,
    VademecumProductIngredient,
    VademecumProductMonograph,
)
from src.core.db import DAO
from src.core.db.model import Base
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType


class VademecumDAO(DAO[VademecumDataset, BaseModel, BaseModel]):
    async def insert_dataset(
        self,
        db: AsyncSession,
        dataset_id: UUID,
        source_sha256: str,
        schema_version: str,
        registry_cutoff_date: date,
        medical_notice: str,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": dataset_id,
                "source_sha256": source_sha256,
                "schema_version": schema_version,
                "registry_cutoff_date": registry_cutoff_date,
                "medical_notice": medical_notice,
                "active": False,
            },
        )

    async def insert_batch(
        self,
        db: AsyncSession,
        model: type[Base],
        rows: list[dict[str, object]],
    ) -> None:
        if model is VademecumProduct:
            rows = [
                {
                    **row,
                    "product_reference": (
                        null()
                        if row["product_reference"] is None
                        else row["product_reference"]
                    ),
                }
                for row in rows
            ]

        if rows:
            await db.execute(insert(model), rows)

    async def activate(self, db: AsyncSession, dataset_id: UUID) -> None:
        await db.execute(select(self.model).where(self.model.active).with_for_update())
        await db.execute(
            update(self.model).where(self.model.active).values(active=False)
        )
        await db.execute(
            update(self.model).where(self.model.id == dataset_id).values(active=True)
        )

    async def active_dataset(self, db: AsyncSession) -> VademecumDataset | EmptyType:
        dataset = await db.scalar(select(self.model).where(self.model.active))

        return Empty if dataset is None else dataset

    async def product_page(
        self, db: AsyncSession, dataset_id: UUID, query: VademecumProductQuery
    ) -> tuple[
        list[VademecumProduct],
        list[VademecumProductMonograph],
        list[VademecumProductIngredient],
        int,
    ]:
        statement = select(VademecumProduct).where(
            VademecumProduct.dataset_id == dataset_id
        )

        if query.q:
            statement = statement.where(
                VademecumProduct.search_text.contains(
                    normalize_search_text(query.q), autoescape=True
                )
            )

        if query.monograph_id is not None:
            linked = select(VademecumProductMonograph.registration_number).where(
                VademecumProductMonograph.dataset_id == dataset_id,
                VademecumProductMonograph.monograph_id == query.monograph_id,
            )
            statement = statement.where(
                VademecumProduct.registration_number.in_(linked)
            )

        total = await self.count(db, statement)
        products = list(
            await db.scalars(
                statement.order_by(
                    VademecumProduct.name, VademecumProduct.registration_number
                )
                .offset((query.page - 1) * query.shows)
                .limit(query.shows)
            )
        )
        registrations = [product.registration_number for product in products]
        links = await self.product_links(db, dataset_id, registrations)
        ingredients = await self.product_ingredients(db, dataset_id, registrations)

        return products, links, ingredients, total

    async def product_detail(
        self, db: AsyncSession, dataset_id: UUID, registration_number: str
    ) -> (
        tuple[
            VademecumProduct,
            list[VademecumProductMonograph],
            list[VademecumProductIngredient],
        ]
        | EmptyType
    ):
        product = await db.scalar(
            select(VademecumProduct).where(
                VademecumProduct.dataset_id == dataset_id,
                VademecumProduct.registration_number == registration_number,
            )
        )

        if product is None:
            return Empty

        links = await self.product_links(db, dataset_id, [registration_number])
        ingredients = await self.product_ingredients(
            db, dataset_id, [registration_number]
        )

        return product, links, ingredients

    async def product_links(
        self, db: AsyncSession, dataset_id: UUID, registrations: list[str]
    ) -> list[VademecumProductMonograph]:
        if not registrations:
            return []

        rows = await db.scalars(
            select(VademecumProductMonograph)
            .where(
                VademecumProductMonograph.dataset_id == dataset_id,
                VademecumProductMonograph.registration_number.in_(registrations),
            )
            .order_by(
                VademecumProductMonograph.registration_number,
                VademecumProductMonograph.monograph_id,
            )
        )

        return list(rows)

    async def product_ingredients(
        self, db: AsyncSession, dataset_id: UUID, registrations: list[str]
    ) -> list[VademecumProductIngredient]:
        if not registrations:
            return []

        rows = await db.scalars(
            select(VademecumProductIngredient)
            .where(
                VademecumProductIngredient.dataset_id == dataset_id,
                VademecumProductIngredient.registration_number.in_(registrations),
            )
            .order_by(
                VademecumProductIngredient.registration_number,
                VademecumProductIngredient.ingredient_id,
            )
        )

        return list(rows)

    async def monograph_page(
        self, db: AsyncSession, dataset_id: UUID, query: VademecumMonographQuery
    ) -> tuple[list[VademecumMonograph], int]:
        statement = select(VademecumMonograph).where(
            VademecumMonograph.dataset_id == dataset_id
        )

        if query.q:
            statement = statement.where(
                VademecumMonograph.search_text.contains(
                    normalize_search_text(query.q), autoescape=True
                )
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(VademecumMonograph.name, VademecumMonograph.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def monograph_detail(
        self, db: AsyncSession, dataset_id: UUID, monograph_id: str
    ) -> VademecumMonograph | EmptyType:
        row = await db.scalar(
            select(VademecumMonograph).where(
                VademecumMonograph.dataset_id == dataset_id,
                VademecumMonograph.id == monograph_id,
            )
        )

        return Empty if row is None else row


dao_vademecum = VademecumDAO(VademecumDataset)
