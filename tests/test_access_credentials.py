import asyncio
import base64
import hashlib
import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from src.core import Err, Ok
from src.core.services.device_tokens import issue_token, parse_token


class OpaqueTokenTests(unittest.TestCase):
    def test_token_contains_a_uuid7_and_a_256_bit_secret_but_returns_only_its_hash(self):
        token_id, value, fingerprint = issue_token()
        secret = base64.urlsafe_b64decode(value.split(".")[1] + "=")

        self.assertEqual(token_id.version, 7)
        self.assertEqual(len(secret), 32)
        self.assertEqual(fingerprint, hashlib.sha256(secret).digest())
        self.assertEqual(parse_token(value), (token_id, fingerprint))
        self.assertNotEqual(issue_token()[1], value)

    def test_malformed_and_noncanonical_credentials_are_rejected(self):
        token_id, value, fingerprint = issue_token()
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        noncanonical = value[:-1] + alphabet[alphabet.index(value[-1]) + 1]

        for invalid in (
            "", value + "=", value.upper(), value.replace("ngt_", "Bearer "),
            value.replace(str(token_id), str(uuid4())), noncanonical,
        ):
            with self.subTest(kind=invalid[:4]):
                self.assertIsNone(parse_token(invalid))


class OIDCVerificationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory()
        cls.previous_directory = Path.cwd()
        os.chdir(cls.directory.name)
        environment = {
            key: value for key, value in os.environ.items()
            if not key.upper().startswith(("API_", "OIDC_"))
        }
        cls.environment = patch.dict(os.environ, environment, clear=True)
        cls.environment.start()

        from src.core.services import oidc
        from src.settings.oidc_settings import OIDCSettings

        cls.oidc = oidc
        cls.Settings = OIDCSettings
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(
            cls.private_key.public_key(), as_dict=True
        )
        cls.public_jwk.update({"kid": "fixture-key", "use": "sig", "alg": "RS256"})

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        os.chdir(cls.previous_directory)
        cls.directory.cleanup()

    def setUp(self):
        self.settings = self.Settings(
            _env_file=None, issuer="https://issuer.example.invalid/realm",
            jwks_uri="https://issuer.example.invalid/keys",
        )
        self.configuration = patch.object(self.oidc, "oidc_settings", self.settings)
        self.configuration.start()
        self.addCleanup(self.configuration.stop)
        self.oidc._keys = {}
        self.oidc._expires_at = 0
        self.oidc._key_lock = asyncio.Lock()
        self.requests = []
        self.document = {"keys": [dict(self.public_jwk)]}
        self.network_failure = False

        def respond(request):
            self.requests.append(str(request.url))
            if self.network_failure:
                raise httpx.ConnectError("fictional provider failure")
            return httpx.Response(200, json=self.document)

        client_type = httpx.AsyncClient
        self.clients = patch.object(
            self.oidc.httpx, "AsyncClient",
            side_effect=lambda **kwargs: client_type(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        )
        self.clients.start()
        self.addCleanup(self.clients.stop)

    def token(self, **changes):
        claims = {
            "iss": self.settings.issuer, "sub": "fixture-subject",
            "aud": self.settings.audience, "azp": self.settings.public_client_id,
            "typ": "Bearer", "exp": int(time.time()) + 300,
            "name": "Fixture Owner",
        }
        claims.update(changes)

        return jwt.encode(
            claims, self.private_key, algorithm="RS256", headers={"kid": "fixture-key"}
        )

    async def test_verified_identity_uses_a_cached_key_from_the_configured_endpoint(self):
        token = self.token()
        result = await self.oidc.verify_identity(token)

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value["subject"], "fixture-subject")
        self.assertEqual(result.value["display_name"], "Fixture Owner")
        self.assertEqual(await self.oidc.verify_identity(token), result)
        self.assertEqual(self.requests, [self.settings.jwks_uri])

    async def test_wrong_claims_and_id_tokens_are_rejected(self):
        for changes in (
            {"iss": "https://other.example.invalid"}, {"aud": "other-api"},
            {"azp": "other-client"}, {"typ": "ID"}, {"sub": ""}, {"sub": "   "},
            {"exp": int(time.time()) - 30}, {"exp": None},
            {"nbf": int(time.time()) + 300}, {"exp": str(int(time.time()) + 300)},
        ):
            with self.subTest(fields=list(changes)):
                result = await self.oidc.verify_identity(self.token(**changes))
                self.assertEqual(result, Err(self.oidc.OIDCError.INVALID_TOKEN))

    async def test_verified_subject_keeps_its_exact_value(self):
        result = await self.oidc.verify_identity(self.token(sub=" fixture-subject "))

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value["subject"], " fixture-subject ")

    async def test_wrong_signature_and_algorithm_are_rejected(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = jwt.decode(self.token(), options={"verify_signature": False})
        wrong_signature = jwt.encode(
            claims, other_key, algorithm="RS256", headers={"kid": "fixture-key"}
        )
        wrong_algorithm = jwt.encode(
            claims, "fictional-test-key-that-is-at-least-32-bytes",
            algorithm="HS256", headers={"kid": "fixture-key"},
        )

        self.assertEqual(
            await self.oidc.verify_identity(wrong_signature), Err(self.oidc.OIDCError.INVALID_TOKEN)
        )
        self.assertEqual(
            await self.oidc.verify_identity(wrong_algorithm), Err(self.oidc.OIDCError.INVALID_TOKEN)
        )

    async def test_unknown_kid_reloads_once_and_ignores_header_urls(self):
        self.assertIsInstance(await self.oidc.verify_identity(self.token()), Ok)
        claims = jwt.decode(self.token(), options={"verify_signature": False})
        token = jwt.encode(
            claims, self.private_key, algorithm="RS256",
            headers={"kid": "new-fixture-key", "jku": "https://untrusted.example.invalid/keys"},
        )
        rotated = dict(self.public_jwk, kid="new-fixture-key")
        self.document = {"keys": [rotated]}

        self.assertIsInstance(await self.oidc.verify_identity(token), Ok)
        self.assertEqual(self.requests, [self.settings.jwks_uri] * 2)

    async def test_expired_cache_fails_closed_when_provider_is_unavailable(self):
        self.assertIsInstance(await self.oidc.verify_identity(self.token()), Ok)
        self.oidc._expires_at = -1
        self.network_failure = True

        self.assertEqual(
            await self.oidc.verify_identity(self.token()), Err(self.oidc.OIDCError.UNAVAILABLE)
        )

    async def test_missing_configuration_and_invalid_key_sets_fail_closed(self):
        token = self.token()
        self.document = {"keys": []}
        self.assertEqual(
            await self.oidc.verify_identity(token), Err(self.oidc.OIDCError.UNAVAILABLE)
        )
        self.settings.issuer = None
        self.assertEqual(
            await self.oidc.verify_identity(token), Err(self.oidc.OIDCError.UNAVAILABLE)
        )

    def test_plain_http_is_limited_to_local_nonproduction_endpoints(self):
        from pydantic import ValidationError
        from src.settings.oidc_settings import api_settings

        self.Settings(_env_file=None, issuer="http://127.0.0.1:18080/realm")
        with self.assertRaises(ValidationError):
            self.Settings(_env_file=None, issuer="http://issuer.example.invalid/realm")
        with patch.object(api_settings, "environment", "production"):
            with self.assertRaises(ValidationError):
                self.Settings(_env_file=None, issuer="http://127.0.0.1:18080/realm")


if __name__ == "__main__":
    unittest.main()
