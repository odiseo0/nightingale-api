import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from src.api.vademecum.domain.monographs import Monograph


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "vademecum/vademecum_venezuela_2026-11-03.json"


class VademecumMonographTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = json.loads(DATASET.read_text(encoding="utf-8"))["monographs"]
        cls.example = cls.documents[0]

    def test_all_authoritative_monographs_validate_and_round_trip(self):
        self.assertEqual(len(self.documents), 868)

        for document in self.documents:
            with self.subTest(monograph=document["id"]):
                monograph = Monograph.model_validate(document)
                self.assertEqual(
                    monograph.model_dump(mode="json", by_alias=True), document
                )

    def test_simple_complete_and_combination_documents_keep_all_content(self):
        selected = [
            min(self.documents, key=lambda item: len(json.dumps(item))),
            max(self.documents, key=lambda item: len(json.dumps(item))),
            next(item for item in self.documents if "-" in item["id"]),
        ]

        for document in selected:
            with self.subTest(monograph=document["id"]):
                self.assertEqual(
                    Monograph.model_validate(document).model_dump(
                        mode="json", by_alias=True
                    ),
                    document,
                )

    def test_invalid_identifier_and_schema_version_are_rejected(self):
        for field, value in (("id", "Invalid ID"), ("schemaVersion", "2.0.0")):
            document = copy.deepcopy(self.example)
            document[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Monograph.model_validate(document)

    def test_invalid_dates_and_uri_are_rejected(self):
        document = copy.deepcopy(self.example)
        document["sources"][0]["consultedOn"] = "2026-02-30"
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

        document = copy.deepcopy(self.example)
        document["sources"][0]["url"] = "not-a-uri"
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

        document = copy.deepcopy(self.example)
        document["review"]["date"] = "not-a-date"
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

    def test_closed_sets_are_rejected(self):
        mutations = [
            ("indications", 0, "type", "unknown"),
            ("alerts", 0, "severity", "fatal"),
            ("specialPopulations", "pregnancy", "status", "safe"),
            ("safety", "interactions", 0, "type", "unknown"),
            ("safety", "adverseEffects", 0, "frequency", "sometimes"),
        ]

        for path in mutations:
            document = copy.deepcopy(self.example)
            target = document
            for key in path[:-2]:
                target = target[key]
            target[path[-2]] = path[-1]
            with self.subTest(path=path), self.assertRaises(ValidationError):
                Monograph.model_validate(document)

    def test_extra_fields_and_unexpected_nulls_are_rejected(self):
        document = copy.deepcopy(self.example)
        document["unexpected"] = True
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

        document = copy.deepcopy(self.example)
        document["atc"]["unexpected"] = True
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

        document = copy.deepcopy(self.example)
        document["name"] = None
        with self.assertRaises(ValidationError):
            Monograph.model_validate(document)

    def test_unique_lists_reject_duplicates(self):
        for path in (
            ("sismedAliases",),
            ("safety", "precautions"),
            ("specialPopulations", "pregnancy", "trimesters"),
            ("therapeuticGroup", "associations"),
        ):
            document = copy.deepcopy(self.example)
            target = document
            for key in path[:-1]:
                target = target[key]
            values = target[path[-1]]
            if not values:
                values.append("1T" if path[-1] == "trimesters" else "duplicate")
            values.append(values[0])
            with self.subTest(path=path), self.assertRaises(ValidationError):
                Monograph.model_validate(document)


if __name__ == "__main__":
    unittest.main()
