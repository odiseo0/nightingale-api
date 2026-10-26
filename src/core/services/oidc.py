import asyncio
import math
import ssl
import time
from enum import StrEnum

import httpx
import jwt

from src.core import Err, Ok, Result
from src.settings.oidc_settings import oidc_settings


class OIDCError(StrEnum):
    INVALID_TOKEN = "INVALID_TOKEN"
    UNAVAILABLE = "UNAVAILABLE"


_keys: dict[str, jwt.PyJWK] = {}
_expires_at = 0.0
_key_lock = asyncio.Lock()


async def load_keys() -> bool:
    global _keys, _expires_at

    try:
        tls = ssl.create_default_context(cafile=oidc_settings.tls_ca_file)

        async with httpx.AsyncClient(timeout=5, trust_env=False, verify=tls) as client:
            response = await client.get(oidc_settings.jwks_uri)
            response.raise_for_status()
            document = response.json()

        if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
            return False

        keys = {}

        for item in document["keys"]:
            if not isinstance(item, dict) or item.get("kty") != "RSA":
                continue

            if item.get("alg", "RS256") != "RS256" or item.get("use", "sig") != "sig":
                continue

            if "key_ops" in item and "verify" not in item["key_ops"]:
                continue

            kid = item.get("kid")

            if not isinstance(kid, str) or not kid or kid in keys:
                return False

            keys[kid] = jwt.PyJWK.from_dict(item, algorithm="RS256")

        if not keys:
            return False
    except httpx.HTTPError, OSError, ValueError, TypeError, jwt.PyJWTError:
        return False

    _keys = keys
    _expires_at = time.monotonic() + 300

    return True


async def verify_identity(token: str) -> Result[dict[str, str], OIDCError]:
    if not oidc_settings.issuer or not oidc_settings.jwks_uri:
        return Err(OIDCError.UNAVAILABLE)

    if len(token) > 8192:
        return Err(OIDCError.INVALID_TOKEN)

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError, OverflowError:
        return Err(OIDCError.INVALID_TOKEN)

    if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
        return Err(OIDCError.INVALID_TOKEN)

    # The endpoint comes only from settings; JWT header URLs never select keys.
    # https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode
    async with _key_lock:
        refreshed = False

        if time.monotonic() >= _expires_at:
            if not await load_keys():
                return Err(OIDCError.UNAVAILABLE)

            refreshed = True

        key = _keys.get(header["kid"])

        if key is None and not refreshed:
            if not await load_keys():
                return Err(OIDCError.UNAVAILABLE)

            key = _keys.get(header["kid"])

        if key is None:
            return Err(OIDCError.INVALID_TOKEN)

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=oidc_settings.audience,
            issuer=oidc_settings.issuer,
            options={"require": ["exp", "iss", "aud", "sub", "azp", "typ"]},
        )

        if claims["azp"] != oidc_settings.public_client_id or claims["typ"] != "Bearer":
            return Err(OIDCError.INVALID_TOKEN)

        if not isinstance(claims["sub"], str) or not claims["sub"].strip():
            return Err(OIDCError.INVALID_TOKEN)

        for name in ("exp", "nbf", "iat"):
            if name in claims and (
                type(claims[name]) not in (int, float)
                or not math.isfinite(claims[name])
            ):
                return Err(OIDCError.INVALID_TOKEN)
    except jwt.PyJWTError, OverflowError:
        return Err(OIDCError.INVALID_TOKEN)

    display_name = claims.get("name") or claims.get("preferred_username")

    if not isinstance(display_name, str) or not display_name.strip():
        display_name = claims["sub"]

    return Ok(
        {
            "issuer": claims["iss"],
            "subject": claims["sub"],
            "display_name": display_name.strip(),
        }
    )
