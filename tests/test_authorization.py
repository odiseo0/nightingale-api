import unittest
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid7

import test_foundation as foundation
from pydantic import ValidationError

from src.api.authorization.domain.authorization import (
    AuthConfigResponse,
    DeviceRegistrationRequest,
    DeviceTokenIssued,
    ExternalIdentity,
    TokenRotationRequest,
)
from src.core.schema import BaseModel


class AuthorizationSchemaTests(unittest.TestCase):
    def test_registration_uses_the_project_base_and_public_aliases(self):
        data = DeviceRegistrationRequest.model_validate({
            "deviceName": " Fixture Desktop ",
            "clientVersion": " 0.1.0 ",
            "localSchemaVersion": 1,
        })

        self.assertIsInstance(data, BaseModel)
        self.assertEqual(
            data.model_dump(by_alias=True),
            {"deviceName": "Fixture Desktop", "clientVersion": "0.1.0", "localSchemaVersion": 1},
        )
        properties = DeviceRegistrationRequest.model_json_schema()["properties"]
        self.assertEqual(set(properties), {"deviceName", "clientVersion", "localSchemaVersion"})

    def test_registration_rejects_identity_fields_boolean_versions_and_blank_names(self):
        valid = {"deviceName": "Fixture", "clientVersion": "0.1.0", "localSchemaVersion": 1}
        for changes in ({"userId": str(uuid7())}, {"localSchemaVersion": True}, {"deviceName": " "}):
            with self.subTest(fields=list(changes)):
                with self.assertRaises(ValidationError):
                    DeviceRegistrationRequest.model_validate({**valid, **changes})

        with self.assertRaises(ValidationError):
            TokenRotationRequest.model_validate({"deviceId": str(uuid7())})

    def test_issued_token_has_an_explicit_projection_and_utc_time(self):
        token = " fixture-secret-with-spaces "
        issued = DeviceTokenIssued(
            access_token=token,
            token_id=uuid7(),
            device_id=uuid7(),
            user_id=uuid7(),
            issued_at=datetime(2026, 10, 26, 9, tzinfo=timezone(timedelta(hours=-4))),
        )
        value = issued.model_dump(mode="json", by_alias=True)

        self.assertEqual(
            set(value), {"tokenType", "accessToken", "tokenId", "deviceId", "userId", "issuedAt"}
        )
        self.assertEqual(value["accessToken"], token)
        self.assertEqual(value["issuedAt"], "2026-10-26T13:00:00Z")
        self.assertNotIn(token, repr(issued))
        self.assertEqual(issued.issued_at.astimezone(UTC).hour, 13)

    def test_external_identity_and_provider_settings_keep_their_exact_values(self):
        identity = ExternalIdentity("https://fixture.invalid/realm ", " subject ", "Fixture")
        config = AuthConfigResponse(
            issuer=identity.issuer, public_client_id=" desktop ", audience=" api ",
        )

        self.assertEqual(identity.subject, " subject ")
        self.assertEqual(config.issuer, identity.issuer)
        self.assertEqual(config.public_client_id, " desktop ")
        self.assertEqual(config.audience, " api ")
        self.assertEqual(config.authorization_flow, "authorization_code")
        self.assertIsInstance(config, BaseModel)


class AuthorizationEndpointTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_routes_publish_the_domain_schemas_and_use_the_common_error_handlers(self):
        result = self.run_python("""
            import asyncio
            from uuid import uuid7
            import httpx
            from src.application import app

            async def check():
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://fixture") as client:
                    responses = [
                        await client.get("/v1/auth/config"),
                        await client.get("/v1/auth/config?unknown=fixture"),
                        await client.post("/v1/auth/device-tokens", json={
                            "deviceName": "Fixture", "clientVersion": "0.1.0", "localSchemaVersion": 1,
                        }),
                        await client.post(f"/v1/me/devices/{uuid7()}/rotate-token", json={}),
                        await client.post(f"/v1/me/devices/{uuid7()}/revoke"),
                    ]
                schema = app.openapi()
                return {
                    "statuses": [response.status_code for response in responses],
                    "codes": [response.json()["code"] for response in responses],
                    "paths": [path for path in schema["paths"] if path.startswith(("/v1/auth/", "/v1/me/devices"))],
                    "input_fields": list(schema["components"]["schemas"]["DeviceRegistrationRequest"]["properties"]),
                    "output_fields": list(schema["components"]["schemas"]["DeviceTokenIssued"]["properties"]),
                }

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())

        self.assertEqual(result["statuses"], [503, 422, 401, 401, 401])
        self.assertEqual(result["codes"], [
            "DEPENDENCY_UNAVAILABLE", "VALIDATION_ERROR", "AUTHENTICATION_REQUIRED",
            "AUTHENTICATION_REQUIRED", "AUTHENTICATION_REQUIRED",
        ])
        self.assertEqual(set(result["paths"]), {
            "/v1/auth/config", "/v1/auth/device-tokens",
            "/v1/me/devices/{device_id}/rotate-token", "/v1/me/devices/{device_id}/revoke",
            "/v1/me/devices",
        })
        self.assertEqual(set(result["input_fields"]), {"deviceName", "clientVersion", "localSchemaVersion"})
        self.assertEqual(set(result["output_fields"]), {
            "tokenType", "accessToken", "tokenId", "deviceId", "userId", "issuedAt",
        })


if __name__ == "__main__":
    unittest.main()
