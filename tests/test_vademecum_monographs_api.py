import json
import unittest
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid7

import httpx
from fastapi import FastAPI

from src.api.vademecum.application import read_cases
from src.api.vademecum.domain.catalog import (
    VademecumCatalogContext,
    VademecumMonographPage,
    VademecumMonographQuery,
    VademecumMonographResponse,
    VademecumMonographSummary,
)
from src.api.vademecum.domain.errors import VademecumNotFound, VademecumUnavailable
from src.api.vademecum.domain.monographs import Monograph
from src.api.vademecum.infrastructure.monographs_api import router
from src.api.vademecum.repository.dao import dao_vademecum
from src.api.vademecum.repository.models import VademecumDataset, VademecumMonograph
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
        registry_cutoff_date=date(2026, 11, 3), medical_notice="Fixture warning",
        active=True,
    )


def monograph_row(document):
    return VademecumMonograph(
        dataset_id=uuid7(), id=document["id"], name=document["name"],
        atc_code=document["atc"]["code"], document=document, search_text="fixture",
    )


class VademecumMonographReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_validates_documents_and_preserves_review(self):
        row = monograph_row(DATA["monographs"][0])
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "authorized_dataset", new=AsyncMock(return_value=Ok(active_dataset()))),
            patch.object(dao_vademecum, "monograph_page", new=AsyncMock(return_value=([row], 1))),
        ):
            result = await read_cases.read_monographs(
                Mock(), "fixture", uuid7(), VademecumMonographQuery(q="J05AF")
            )
        item = result.value.items[0]
        self.assertEqual(item.atc.code, "J05AF")
        self.assertEqual(item.review.status, "pending_local_review")
        self.assertEqual(item.sismed_aliases, DATA["monographs"][0]["sismedAliases"])

    async def test_detail_and_empty_atc_combination_keep_complete_document(self):
        document = next(item for item in DATA["monographs"] if not item["atc"]["code"])
        row = monograph_row(document)
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "authorized_dataset", new=AsyncMock(return_value=Ok(active_dataset()))),
            patch.object(dao_vademecum, "monograph_detail", new=AsyncMock(return_value=row)),
        ):
            result = await read_cases.read_monograph(
                Mock(), "fixture", uuid7(), document["id"]
            )
        self.assertEqual(result.value.monograph.atc.code, "")
        self.assertEqual(
            result.value.model_dump(mode="json", by_alias=True)["monograph"], document
        )

    async def test_missing_monograph_is_not_found(self):
        with (
            patch.object(read_cases, "transaction", fake_transaction),
            patch.object(read_cases, "authorized_dataset", new=AsyncMock(return_value=Ok(active_dataset()))),
            patch.object(dao_vademecum, "monograph_detail", new=AsyncMock(return_value=read_cases.Empty)),
        ):
            result = await read_cases.read_monograph(Mock(), "fixture", uuid7(), "missing")
        self.assertIsInstance(result.error, VademecumNotFound)


class VademecumMonographsHttpTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.transport = httpx.ASGITransport(app=self.app)
        self.base = f"/v1/accounts/{uuid7()}/vademecum/monographs"
        self.context = VademecumCatalogContext(
            schema_version="1.0.0", registry_cutoff_date=date(2026, 11, 3),
            medical_notice="Fixture warning", source_sha256="a" * 64,
        )
        self.document = DATA["monographs"][0]
        self.monograph = Monograph.model_validate(self.document)

    async def request(self, path, result):
        target = (
            "src.api.vademecum.infrastructure.monographs_api.read_monographs"
            if path == self.base else "src.api.vademecum.infrastructure.monographs_api.read_monograph"
        )
        with patch(target, new=AsyncMock(return_value=result)):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://fixture") as client:
                return await client.get(path)

    async def test_list_and_detail_response_models(self):
        summary = VademecumMonographSummary(
            id=self.monograph.id, name=self.monograph.name,
            sismed_aliases=self.monograph.sismed_aliases,
            atc=self.monograph.atc, review=self.monograph.review,
        )
        response = await self.request(
            self.base, Ok(VademecumMonographPage(
                catalog=self.context, items=[summary], total=1
            ))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["review"]["status"], "pending_local_review")

        response = await self.request(
            self.base + "/abacavir",
            Ok(VademecumMonographResponse(
                catalog=self.context, monograph=self.monograph
            )),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["monograph"], self.document)
        self.assertEqual(response.json()["catalog"]["medicalNotice"], "Fixture warning")

    async def test_http_errors_and_unknown_queries(self):
        response = await self.request(self.base, Err(VademecumUnavailable()))
        self.assertEqual(response.status_code, 503)
        response = await self.request(self.base + "/missing", Err(VademecumNotFound()))
        self.assertEqual(response.status_code, 404)

        async with httpx.AsyncClient(transport=self.transport, base_url="http://fixture") as client:
            self.assertEqual((await client.get(self.base + "?unknown=1")).status_code, 422)
            self.assertEqual((await client.get(self.base + "/abacavir?unknown=1")).status_code, 422)

    def test_openapi_response_models(self):
        paths = self.app.openapi()["paths"]
        self.assertEqual(
            paths["/v1/accounts/{account_id}/vademecum/monographs"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/VademecumMonographPage",
        )
        self.assertEqual(
            paths["/v1/accounts/{account_id}/vademecum/monographs/{monograph_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/VademecumMonographResponse",
        )


if __name__ == "__main__":
    unittest.main()
