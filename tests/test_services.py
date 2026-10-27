import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.services.domain.services import CreateServicePayload, ServicePatch, ServiceQuery, ServiceStatusPayload
from src.api.services.domain.offers import OfferServicePayload, UpdateServiceOfferPayload


class ServiceSchemaTests(unittest.TestCase):
    def test_offer_null_uses_base_and_update_requires_explicit_value(self):
        self.assertIsNone(OfferServicePayload().duration_minutes_override)
        self.assertIsNone(UpdateServiceOfferPayload(durationMinutesOverride=None).duration_minutes_override)
        self.assertEqual(UpdateServiceOfferPayload(durationMinutesOverride=45).duration_minutes_override, 45)
        for payload in ({}, {"durationMinutesOverride": 0}, {"durationMinutesOverride": True}, {"durationMinutesOverride": 1441}, {"durationMinutesOverride": "30"}, {"status": "active"}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                UpdateServiceOfferPayload.model_validate(payload)

    def test_duration_is_an_integer_between_one_and_1440(self):
        for value in (1, 1440):
            self.assertEqual(CreateServicePayload(professional_id=uuid7(), name=" Fixture ", default_duration_minutes=value).name, "Fixture")
        for value in (0, 1441, True, 1.5, "30", None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                CreateServicePayload(professional_id=uuid7(), name="Fixture", default_duration_minutes=value)

    def test_patch_preserves_absence_and_rejects_null_and_ownership(self):
        self.assertEqual(ServicePatch(name="Fixture").model_dump(exclude_unset=True), {"name": "Fixture"})
        for payload in ({}, {"name": None}, {"name": " "}, {"defaultDurationMinutes": None}, {"professionalId": str(uuid7())}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ServicePatch.model_validate(payload)
        with self.assertRaises(ValidationError):
            ServiceStatusPayload(status="deleted")

    def test_query_bounds_and_public_names(self):
        self.assertEqual(ServiceQuery().shows, 100)
        for payload in ({"page": 0}, {"shows": 501}, {"other": 1}, {"status": "deleted"}, {"q": " "}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ServiceQuery.model_validate(payload)
