import unittest
from datetime import UTC, datetime
from uuid import uuid7

from pydantic import ValidationError

from src.api.accounts.domain.accounts import (
    AccessResponse,
    AccountDetails,
    AccountResponse,
    BootstrapPracticeInput,
    MeResponse,
    PracticeCreated,
    ProfessionalResponse,
)
from src.core.schema import BaseModel, PageQuery


class AccountSchemaTests(unittest.TestCase):
    def details(self):
        return {
            "displayName": " Fixture Practice ",
            "timeZone": "America/Caracas",
            "locationName": "Fixture Office",
            "locationAddress": "Fictional address",
            "locationState": "Fixture State",
            "locationCity": "Fixture City",
        }

    def test_bootstrap_uses_base_aliases_without_changing_external_identity(self):
        data = BootstrapPracticeInput.model_validate({
            **self.details(),
            "ownerIssuer": "https://fixture.invalid/realm ",
            "ownerSubject": " fixture-subject ",
            "ownerName": " Fixture Owner ",
            "professionalName": " Fixture Professional ",
        })

        self.assertIsInstance(data, BaseModel)
        self.assertEqual(data.display_name, "Fixture Practice")
        self.assertEqual(data.owner_subject, " fixture-subject ")
        self.assertEqual(data.owner_issuer, "https://fixture.invalid/realm ")
        self.assertEqual(data.owner_name, "Fixture Owner")
        self.assertEqual(data.location_country, "VE")
        self.assertIn("ownerSubject", data.model_dump(by_alias=True))

    def test_details_reject_unknown_country_blank_zone_and_injected_fields(self):
        for change in (
            {"locationCountry": "ZZ"}, {"timeZone": " "},
            {"ownerUserId": str(uuid7())}, {"displayName": " "},
        ):
            with self.subTest(fields=list(change)):
                with self.assertRaises(ValidationError):
                    AccountDetails.model_validate({**self.details(), **change})

    def test_responses_use_the_base_and_explicit_utc_projection(self):
        for schema in (AccountResponse, ProfessionalResponse, AccessResponse, MeResponse, PracticeCreated):
            self.assertTrue(issubclass(schema, BaseModel))

        now = datetime(2026, 10, 26, 13, tzinfo=UTC)
        response = ProfessionalResponse(
            id=uuid7(), user_id=uuid7(), public_name="Fixture", status="active",
            created_at=now, updated_at=now, version=1,
        ).model_dump(mode="json", by_alias=True)

        self.assertEqual(response["createdAt"], "2026-10-26T13:00:00Z")
        self.assertNotIn("oidcSubject", response)
        self.assertNotIn("secretHash", response)

    def test_page_parameters_keep_existing_defaults_and_reject_old_cursor_fields(self):
        self.assertEqual(PageQuery().model_dump(), {"page": 1, "shows": 100})
        self.assertEqual(PageQuery(page=2, shows=500).page, 2)
        for fields in ({"page": 0}, {"shows": 0}, {"shows": 501}, {"cursor": "old"}, {"limit": 100}):
            with self.subTest(fields=list(fields)):
                with self.assertRaises(ValidationError):
                    PageQuery(**fields)


if __name__ == "__main__":
    unittest.main()
