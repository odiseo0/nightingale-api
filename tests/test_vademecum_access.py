import json
import unittest
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid7

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.vademecum.application import read_cases
from src.api.vademecum.domain.catalog import VademecumProductQuery
from src.api.vademecum.domain.errors import VademecumNotFound, VademecumUnavailable
from src.api.vademecum.repository.dao import dao_vademecum
from src.api.vademecum.repository.models import (
    VademecumDataset,
    VademecumProduct,
    VademecumProductIngredient,
    VademecumProductMonograph,
)
from src.core import Err, Ok


ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads(
    (ROOT / "vademecum/vademecum_venezuela_2026-11-03.json").read_text(encoding="utf-8")
)


@asynccontextmanager
async def fake_transaction(db):
    yield


def active_dataset():
    return VademecumDataset(
        id=uuid7(), source_sha256="a" * 64, schema_version="1.0.0",
        registry_cutoff_date=date(2026, 11, 3), medical_notice="Fixture notice",
        active=True,
    )


def product_row():
    source = DATA["products"][0]
    return VademecumProduct(
        dataset_id=uuid7(), registration_number=source["ef"], name=source["nombre"],
        active_ingredient_text=source["principioActivo"],
        approved_at=source["fechaAprobado"], valid_until=source["fechaVigencia"],
        representative=source["representante"], manufacturer=source["fabricante"],
        ingredient_link_status=source["ingredientLinkStatus"],
        ingredient_resolution=source["ingredientResolution"],
        product_reference=None, search_text="fixture",
    )


class VademecumAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_and_assistant_use_the_same_active_account_rule(self):
        for owner in (True, False):
            context = SimpleNamespace(
                owner=owner, account=SimpleNamespace(status="active")
            )
            with (
                patch.object(read_cases, "transaction", fake_transaction),
                patch.object(read_cases, "get_account_context", new=AsyncMock(return_value=Ok(context))),
                patch.object(dao_vademecum, "active_dataset", new=AsyncMock(return_value=active_dataset())),
                patch.object(dao_vademecum, "product_page", new=AsyncMock(return_value=([], [], [], 0))),
            ):
                result = await read_cases.read_products(
                    Mock(), "fixture", uuid7(), VademecumProductQuery()
                )
            self.assertEqual(result.value.total, 0)
            self.assertEqual(result.value.catalog.registry_cutoff_date, date(2026, 11, 3))

    async def test_invalid_outside_and_inactive_access_do_not_read_catalog(self):
        errors = (InvalidCredential(), AccountNotFound(uuid7()), AccessDenied())
        for error in errors:
            context = SimpleNamespace(account=SimpleNamespace(status="inactive"))
            returned = Err(error) if not isinstance(error, AccessDenied) else Ok(context)
            with (
                patch.object(read_cases, "transaction", fake_transaction),
                patch.object(read_cases, "get_account_context", new=AsyncMock(return_value=returned)),
                patch.object(dao_vademecum, "active_dataset", new=AsyncMock()) as read,
            ):
                result = await read_cases.read_products(
                    Mock(), "fixture", uuid7(), VademecumProductQuery()
                )
            if isinstance(error, AccessDenied):
                self.assertIsInstance(result.error, AccessDenied)
            else:
                self.assertIs(result.error, error)
            read.assert_not_awaited()

    async def test_missing_active_release_is_unavailable(self):
        context = SimpleNamespace(account=SimpleNamespace(status="active"))
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "get_account_context", new=AsyncMock(return_value=Ok(context))),
            patch.object(dao_vademecum, "active_dataset", new=AsyncMock(return_value=read_cases.Empty)),
        ):
            result = await read_cases.read_products(
                Mock(), "fixture", uuid7(), VademecumProductQuery()
            )
        self.assertIsInstance(result.error, VademecumUnavailable)

    async def test_product_projection_keeps_links_ingredients_and_context(self):
        row = product_row()
        link = VademecumProductMonograph(
            dataset_id=row.dataset_id, registration_number=row.registration_number,
            monograph_id="carbocisteina", combination=False,
        )
        ingredient = VademecumProductIngredient(
            dataset_id=row.dataset_id, registration_number=row.registration_number,
            ingredient_id="carbocisteina",
        )
        dataset = active_dataset()
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "get_account_context", new=AsyncMock(return_value=Ok(SimpleNamespace(account=SimpleNamespace(status="active"))))),
            patch.object(dao_vademecum, "active_dataset", new=AsyncMock(return_value=dataset)),
            patch.object(dao_vademecum, "product_detail", new=AsyncMock(return_value=(row, [link], [ingredient]))),
        ):
            result = await read_cases.read_product(
                Mock(), "fixture", uuid7(), row.registration_number
            )

        product = result.value.product
        self.assertEqual(product.monograph_ids, ["carbocisteina"])
        self.assertEqual(product.canonical_ingredient_ids, ["carbocisteina"])
        self.assertEqual(result.value.catalog.source_sha256, "a" * 64)

    async def test_missing_product_is_not_found_after_authorization(self):
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "get_account_context", new=AsyncMock(return_value=Ok(SimpleNamespace(account=SimpleNamespace(status="active"))))),
            patch.object(dao_vademecum, "active_dataset", new=AsyncMock(return_value=active_dataset())),
            patch.object(dao_vademecum, "product_detail", new=AsyncMock(return_value=read_cases.Empty)),
        ):
            result = await read_cases.read_product(Mock(), "fixture", uuid7(), "missing")
        self.assertIsInstance(result.error, VademecumNotFound)


if __name__ == "__main__":
    unittest.main()
