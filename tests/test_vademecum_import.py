import copy
import json
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid7

from src.api.vademecum.application.import_cases import (
    import_vademecum,
    validate_vademecum,
)
from src.api.vademecum.domain.catalog import normalize_search_text
from src.api.vademecum.domain.errors import VademecumImportError
from src.api.vademecum.repository.dao import dao_vademecum
from src.api.vademecum.repository.models import (
    VademecumDataset,
    VademecumMonograph,
    VademecumProduct,
    VademecumProductIngredient,
    VademecumProductMonograph,
)


ROOT = Path(__file__).resolve().parents[1]


class VademecumPersistenceTests(unittest.TestCase):
    def test_five_models_have_the_designed_keys_and_schema(self):
        models = (
            VademecumDataset,
            VademecumProduct,
            VademecumProductIngredient,
            VademecumMonograph,
            VademecumProductMonograph,
        )
        self.assertEqual(
            {model.__tablename__ for model in models},
            {
                "vademecum_datasets", "vademecum_products",
                "vademecum_product_ingredients", "vademecum_monographs",
                "vademecum_product_monographs",
            },
        )
        for model in models:
            self.assertEqual(model.__table__.schema, "nightingale")

        self.assertEqual(
            VademecumProduct.__table__.primary_key.columns.keys(),
            ["dataset_id", "registration_number"],
        )
        self.assertEqual(
            VademecumProductMonograph.__table__.primary_key.columns.keys(),
            ["dataset_id", "registration_number", "monograph_id"],
        )

    def test_migration_is_reversible_and_grants_only_select(self):
        migration = (
            ROOT / "migrations/versions/20261122_01_vademecum.py"
        ).read_text(encoding="utf-8")
        self.assertIn('down_revision = "20261120_01"', migration)
        self.assertIn("def downgrade():", migration)
        self.assertIn("GRANT SELECT ON", migration)
        self.assertNotIn("GRANT INSERT", migration)
        self.assertNotIn("GRANT UPDATE", migration)
        self.assertNotIn("GRANT DELETE", migration)
        self.assertIn("WHERE active", migration)


class VademecumImportValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = (ROOT / "vademecum/vademecum_venezuela_2026-11-03.json").read_bytes()
        cls.data = json.loads(cls.content)

    def test_authoritative_dataset_passes_all_current_statistics(self):
        dataset = validate_vademecum(self.content)
        self.assertEqual(len(dataset.products), 6264)
        self.assertEqual(len(dataset.monographs), 868)

    def test_duplicates_broken_references_and_statistics_are_rejected(self):
        mutations = []
        duplicate_product = copy.deepcopy(self.data)
        duplicate_product["products"][1]["ef"] = duplicate_product["products"][0]["ef"]
        mutations.append(duplicate_product)
        duplicate_monograph = copy.deepcopy(self.data)
        duplicate_monograph["monographs"][1]["id"] = duplicate_monograph["monographs"][0]["id"]
        mutations.append(duplicate_monograph)
        broken = copy.deepcopy(self.data)
        broken["products"][0]["monographIds"] = ["missing"]
        mutations.append(broken)
        statistics = copy.deepcopy(self.data)
        statistics["statistics"]["products"] += 1
        mutations.append(statistics)

        for data in mutations:
            with self.subTest(), self.assertRaises(VademecumImportError):
                validate_vademecum(json.dumps(data).encode())

    def test_invalid_json_and_content_are_rejected(self):
        for content in (b"not-json", b"{}"):
            with self.subTest(), self.assertRaises(VademecumImportError):
                validate_vademecum(content)

    def test_search_normalization_handles_accents_case_and_spaces(self):
        self.assertEqual(normalize_search_text("  Ácido   ACETILSALICÍLICO "), "acido acetilsalicilico")


class VademecumImportCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_content_does_not_open_a_transaction(self):
        with patch("src.api.vademecum.application.import_cases.transaction") as begin:
            result = await import_vademecum(Mock(), b"invalid")
        self.assertIsInstance(result.error, VademecumImportError)
        begin.assert_not_called()

    async def test_existing_hash_changes_no_data(self):
        existing = VademecumDataset(id=uuid7())

        @asynccontextmanager
        async def fake_transaction(db):
            yield

        with (
            patch("src.api.vademecum.application.import_cases.transaction", fake_transaction),
            patch.object(dao_vademecum, "get_by_source", new=AsyncMock(return_value=existing)),
            patch.object(dao_vademecum, "insert_dataset", new=AsyncMock()) as insert,
        ):
            result = await import_vademecum(
                Mock(), (ROOT / "vademecum/vademecum_venezuela_2026-11-03.json").read_bytes()
            )

        self.assertEqual(result.value.status, "existing")
        self.assertEqual(result.value.dataset_id, existing.id)
        insert.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
