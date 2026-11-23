import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid7

import httpx
from fastapi import FastAPI

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.vademecum.domain.catalog import (
    VademecumCatalogContext,
    VademecumProductPage,
    VademecumProductResponse,
)
from src.api.vademecum.domain.errors import VademecumNotFound, VademecumUnavailable
from src.api.vademecum.domain.products import VademecumDataset
from src.api.vademecum.infrastructure.products_api import router
from src.core import Err, Ok


ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads(
    (ROOT / "vademecum/vademecum_venezuela_2026-11-03.json").read_text(encoding="utf-8")
)


class VademecumProductsApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.transport = httpx.ASGITransport(app=self.app)
        self.account_id = uuid7()
        self.base = f"/v1/accounts/{self.account_id}/vademecum/products"
        self.context = VademecumCatalogContext(
            schema_version="1.0.0", registry_cutoff_date=date(2026, 11, 3),
            medical_notice="Fixture warning", source_sha256="a" * 64,
        )
        dataset = VademecumDataset.model_validate(SOURCE)
        self.product = dataset.products[0].public()

    async def request(self, path, result):
        target = (
            "src.api.vademecum.infrastructure.products_api.read_products"
            if path == self.base else "src.api.vademecum.infrastructure.products_api.read_product"
        )
        with patch(target, new=AsyncMock(return_value=result)):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://fixture") as client:
                return await client.get(path)

    async def test_list_has_typed_context_items_and_total(self):
        response = await self.request(
            self.base, Ok(VademecumProductPage(
                catalog=self.context, items=[self.product], total=1
            ))
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["catalog"]["medicalNotice"], "Fixture warning")
        self.assertEqual(body["items"][0]["monographIds"], ["carbocisteina"])
        self.assertNotIn("oficios", response.text)
        self.assertNotIn("rifRepresentante", response.text)

    async def test_detail_has_product_and_context(self):
        response = await self.request(
            self.base + "/E.F.43.258",
            Ok(VademecumProductResponse(catalog=self.context, product=self.product)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["product"]["registrationNumber"], "E.F.43.258")

    async def test_detail_accepts_literal_and_encoded_slash_in_registration(self):
        registration = "P.B.1.289/12"
        product = self.product.model_copy(update={"registration_number": registration})
        result = Ok(VademecumProductResponse(catalog=self.context, product=product))

        for path in (registration, "P.B.1.289%2F12"):
            with self.subTest(path=path), patch(
                "src.api.vademecum.infrastructure.products_api.read_product",
                new=AsyncMock(return_value=result),
            ) as read:
                async with httpx.AsyncClient(
                    transport=self.transport, base_url="http://fixture"
                ) as client:
                    response = await client.get(self.base + "/" + path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["product"]["registrationNumber"], registration)
                self.assertEqual(read.await_args.args[-1], registration)

    async def test_errors_distinguish_access_missing_and_unavailable(self):
        cases = (
            (InvalidCredential(), 401), (AccessDenied(), 403),
            (AccountNotFound(uuid7()), 404), (VademecumUnavailable(), 503),
        )
        for error, status in cases:
            with self.subTest(status=status):
                response = await self.request(self.base, Err(error))
                self.assertEqual(response.status_code, status)

        response = await self.request(self.base + "/missing", Err(VademecumNotFound()))
        self.assertEqual(response.status_code, 404)

    async def test_unknown_and_invalid_query_parameters_are_rejected(self):
        async with httpx.AsyncClient(transport=self.transport, base_url="http://fixture") as client:
            for path in (
                self.base + "?unknown=1", self.base + "?shows=501",
                self.base + "/E.F.43.258?unknown=1",
            ):
                response = await client.get(path)
                self.assertEqual(response.status_code, 422)

    def test_openapi_uses_the_public_response_models(self):
        document = self.app.openapi()
        for path, model in (
            ("/v1/accounts/{account_id}/vademecum/products", "VademecumProductPage"),
            ("/v1/accounts/{account_id}/vademecum/products/{registration_number}", "VademecumProductResponse"),
        ):
            reference = document["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            self.assertEqual(reference, f"#/components/schemas/{model}")


if __name__ == "__main__":
    unittest.main()
