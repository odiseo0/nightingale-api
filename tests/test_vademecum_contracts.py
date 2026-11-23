import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from src.api.vademecum.domain.catalog import (
    VademecumCatalogContext,
    VademecumMonographQuery,
    VademecumMonographResponse,
    VademecumProductPage,
    VademecumProductQuery,
    VademecumProductResponse,
)
from src.api.vademecum.domain.monographs import Monograph
from src.api.vademecum.domain.products import (
    VademecumDataset,
    VademecumSourceProduct,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "vademecum/vademecum_venezuela_2026-11-03.json"
PUBLIC_FIELDS = {
    "registrationNumber",
    "name",
    "activeIngredientText",
    "approvedAt",
    "validUntil",
    "representative",
    "manufacturer",
    "monographIds",
    "combinationMonographIds",
    "canonicalIngredientIds",
    "ingredientLinkStatus",
    "ingredientResolution",
    "productReference",
}


class VademecumContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.dataset = VademecumDataset.model_validate(cls.data)
        cls.context = VademecumCatalogContext(
            schema_version=cls.dataset.schema_version,
            registry_cutoff_date=cls.dataset.registry_cutoff_date,
            medical_notice=cls.dataset.medical_notice,
            source_sha256="a" * 64,
        )

    def test_complete_authoritative_dataset_validates(self):
        self.assertEqual(len(self.dataset.products), 6264)
        self.assertEqual(len(self.dataset.monographs), 868)
        self.assertEqual(len(self.dataset.historical_products), 9036)
        self.assertEqual(len(self.dataset.supplementary_ingredients), 282)

    def test_public_products_have_only_selected_fields(self):
        for source in self.dataset.products:
            with self.subTest(registration=source.registration_number):
                public = source.public().model_dump(mode="json", by_alias=True)
                self.assertEqual(set(public), PUBLIC_FIELDS)
                self.assertEqual(public["registrationNumber"], source.registration_number)
                self.assertEqual(public["name"], source.name)
                self.assertTrue(public["approvedAt"].endswith("Z"))
                self.assertTrue(public["validUntil"].endswith("Z"))

    def test_linked_empty_and_combination_reference_products(self):
        linked = self.dataset.products[0].public()
        empty = next(
            product
            for product in self.dataset.products
            if not product.monograph_ids and not product.active_ingredient_text
        ).public()
        reference = next(
            product for product in self.dataset.products if product.product_monograph_reference
        ).public()

        self.assertEqual(linked.monograph_ids, ["carbocisteina"])
        self.assertEqual(empty.active_ingredient_text, "")
        self.assertEqual(empty.monograph_ids, [])
        self.assertIsNotNone(reference.product_reference)
        self.assertTrue(reference.combination_monograph_ids)
        self.assertEqual(
            reference.product_reference.scope,
            "fixed_combination",
        )

    def test_reference_sources_and_link_states_remain_explicit(self):
        reference = next(
            product for product in self.dataset.products if product.product_monograph_reference
        ).public()
        self.assertTrue(reference.product_reference.sources[0].url.startswith("https://"))
        self.assertEqual(
            {product.ingredient_link_status for product in self.dataset.products},
            {
                "complete", "unlinked", "missing_ingredient", "historical_complete",
                "product_reference", "inferred_complete", "combination_only",
                "historical_partial", "inferred_partial", "partial",
            },
        )
        self.assertEqual(
            {product.ingredient_resolution for product in self.dataset.products},
            {
                "source_text", "historical_product_match", "unresolved",
                "product_name_inference", "product_reference",
            },
        )

    def test_invalid_link_state_is_rejected_and_naive_registry_date_is_localized(self):
        source = copy.deepcopy(self.data["products"][0])
        source["ingredientLinkStatus"] = "approved"
        with self.assertRaises(ValidationError):
            VademecumSourceProduct.model_validate(source)

        source = copy.deepcopy(self.data["products"][0])
        source["fechaAprobado"] = "2023-02-24T00:00:00"
        product = VademecumSourceProduct.model_validate(source).public()
        self.assertEqual(
            product.model_dump(mode="json", by_alias=True)["approvedAt"],
            "2023-02-24T04:00:00Z",
        )

    def test_product_responses_include_catalog_and_pagination(self):
        product = self.dataset.products[0].public()
        page = VademecumProductPage(
            catalog=self.context, items=[product], total=1
        )
        detail = VademecumProductResponse(catalog=self.context, product=product)

        self.assertEqual(page.model_dump(by_alias=True)["total"], 1)
        self.assertEqual(detail.product.registration_number, product.registration_number)
        self.assertEqual(detail.catalog.source_sha256, "a" * 64)

    def test_monograph_response_preserves_the_complete_document(self):
        document = self.data["monographs"][0]
        response = VademecumMonographResponse(
            catalog=self.context,
            monograph=Monograph.model_validate(document),
        )
        self.assertEqual(
            response.model_dump(mode="json", by_alias=True)["monograph"], document
        )

    def test_queries_reject_unknown_fields_and_enforce_page_limits(self):
        with self.assertRaises(ValidationError):
            VademecumProductQuery.model_validate({"unknown": "value"})
        with self.assertRaises(ValidationError):
            VademecumMonographQuery(shows=501)
        self.assertEqual(VademecumProductQuery().shows, 100)
        self.assertEqual(VademecumMonographQuery().page, 1)


if __name__ == "__main__":
    unittest.main()
