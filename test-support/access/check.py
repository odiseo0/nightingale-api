import asyncio
import base64
import hashlib
import json
import os
import runpy
import ssl
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid7

import httpx
from sqlalchemy import func, select, text


ROOT = Path(__file__).resolve().parents[2]
postgres = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/persistence/check.py")))
oidc = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/oidc/check.py")))
CERTIFICATE = ROOT / ".tmp/test-services/keycloak-test/keycloak-26.8.1/conf/fixture.pem"


def expect(response, status):
    assert response.status_code == status, f"Expected HTTP {status}, got {response.status_code}"
    assert response.headers.get("cache-control") == "no-store"
    assert UUID(response.headers["x-correlation-id"]).version == 7
    if status >= 400:
        assert response.json()["correlationId"] == response.headers["x-correlation-id"]


def provider_tokens(user):
    tls = ssl.create_default_context(cafile=str(CERTIFICATE))
    with httpx.Client(timeout=15, trust_env=False, verify=tls) as client:
        discovery = client.get(f"{oidc.ISSUER}/.well-known/openid-configuration").json()
        code, verifier = oidc.authorize(client, discovery["authorization_endpoint"], user)
        response = oidc.exchange(client, discovery["token_endpoint"], code, verifier)
        assert response.status_code == 200, "Fixture OIDC exchange failed"

        return response.json()


async def issue(client, token):
    response = await client.post(
        "/v1/auth/device-tokens", headers={"Authorization": f"Bearer {token}"},
        json={"deviceName": "Fixture Desktop", "clientVersion": "0.1.0", "localSchemaVersion": 1},
    )
    expect(response, 201)
    result = response.json()
    assert set(result) == {"tokenType", "accessToken", "tokenId", "deviceId", "userId", "issuedAt"}
    assert "expiresAt" not in result and "secretHash" not in result
    assert result["issuedAt"].endswith("Z")

    return result


def authorization(issued):
    return {"Authorization": f"Bearer {issued['accessToken']}"}


async def check_access(client, factory, tokens):
    from src.api.authorization.application import authorization_cases as cases
    from src.api.authorization.repository.models import AppUser, Device, DeviceToken

    owner, assistant, outsider = tokens
    registration = {"deviceName": "Fixture", "clientVersion": "0.1.0", "localSchemaVersion": 1}
    response = await client.get("/v1/auth/config")
    expect(response, 200)
    assert response.json()["issuer"] == oidc.ISSUER
    assert set(response.json()) == {"issuer", "publicClientId", "audience", "authorizationFlow", "pkceMethod"}
    assert response.json()["authorizationFlow"] == "authorization_code"
    expect(await client.get("/v1/auth/config?unexpected=fixture"), 422)
    expect(await client.post("/v1/auth/device-tokens", json=registration), 401)
    expect(await client.post(
        "/v1/auth/device-tokens", json=registration,
        headers={"Authorization": f"Bearer {owner['id_token']}"},
    ), 401)
    response = await client.post(
        "/v1/auth/device-tokens", json=dict(registration, userId="fixture-private-marker"),
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    expect(response, 422)
    assert "fixture-private-marker" not in response.text
    expect(await client.post(
        "/v1/auth/device-tokens", json=dict(registration, localSchemaVersion=True),
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    ), 422)

    primary = await issue(client, owner["access_token"])
    async with factory() as db:
        assert await db.scalar(select(func.count()).select_from(AppUser)) == 1
        assert await db.scalar(select(func.count()).select_from(Device)) == 1
        stored = await db.get(DeviceToken, UUID(primary["tokenId"]))
        secret = base64.urlsafe_b64decode(primary["accessToken"].split(".")[1] + "=")
        assert stored.secret_hash == hashlib.sha256(secret).digest()
        assert len(stored.secret_hash) == 32 and stored.revoked_at is None

    device_id = primary["deviceId"]
    responses = await asyncio.gather(*(
        client.post(f"/v1/me/devices/{device_id}/rotate-token", json={}, headers=authorization(primary))
        for _ in range(2)
    ))
    assert sorted(response.status_code for response in responses) == [201, 401]
    for response in responses:
        expect(response, response.status_code)
    winner = next(response.json() for response in responses if response.status_code == 201)
    expect(await client.post(
        f"/v1/me/devices/{device_id}/rotate-token", json={}, headers=authorization(primary),
    ), 401)
    primary = winner

    # Force a real CHECK failure after revoking the old credential. Both writes
    # must roll back, so the old credential remains usable.
    with patch.object(cases, "issue_token", return_value=(uuid7(), "fixture-not-issued", b"x" * 31)):
        response = await client.post(
            f"/v1/me/devices/{device_id}/rotate-token", json={}, headers=authorization(primary),
        )
        expect(response, 503)
        assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    response = await client.post(
        f"/v1/me/devices/{device_id}/rotate-token", json={}, headers=authorization(primary),
    )
    expect(response, 201)
    primary = response.json()

    async with factory() as db:
        before_users = await db.scalar(select(func.count()).select_from(AppUser))
        before_devices = await db.scalar(select(func.count()).select_from(Device))
    with patch.object(cases, "issue_token", return_value=(uuid7(), "fixture-not-issued", b"x" * 31)):
        response = await client.post(
            "/v1/auth/device-tokens", json=registration,
            headers={"Authorization": f"Bearer {outsider['access_token']}"},
        )
        expect(response, 503)
    async with factory() as db:
        assert await db.scalar(select(func.count()).select_from(AppUser)) == before_users
        assert await db.scalar(select(func.count()).select_from(Device)) == before_devices

    other_installation = await issue(client, owner["access_token"])
    foreign = await issue(client, assistant["access_token"])
    assert primary["userId"] == other_installation["userId"] != foreign["userId"]
    for target in (other_installation, foreign):
        expect(await client.post(
            f"/v1/me/devices/{target['deviceId']}/rotate-token", json={}, headers=authorization(primary),
        ), 403)
    expect(await client.post(
        f"/v1/me/devices/{foreign['deviceId']}/revoke", headers=authorization(primary),
    ), 404)

    target_id = other_installation["deviceId"]
    for _ in range(2):
        response = await client.post(
            f"/v1/me/devices/{target_id}/revoke", headers=authorization(primary),
        )
        expect(response, 204)
        assert response.content == b""
    expect(await client.post(
        f"/v1/me/devices/{target_id}/rotate-token", json={}, headers=authorization(other_installation),
    ), 401)

    from sqlalchemy.exc import IntegrityError
    async with factory() as db:
        async with db.begin():
            try:
                async with db.begin_nested():
                    await db.execute(text("UPDATE nightingale.devices SET status='active' WHERE id=:id"), {"id": UUID(target_id)})
            except IntegrityError as error:
                assert error.orig.sqlstate == "23514"
            else:
                raise AssertionError("Revoked installation was restored")

    racing = await issue(client, owner["access_token"])
    response_rotate, response_revoke = await asyncio.gather(
        client.post(f"/v1/me/devices/{racing['deviceId']}/rotate-token", json={}, headers=authorization(racing)),
        client.post(f"/v1/me/devices/{racing['deviceId']}/revoke", headers=authorization(primary)),
    )
    assert response_rotate.status_code in (201, 401)
    expect(response_revoke, 204)
    async with factory() as db:
        assert await db.scalar(select(func.count()).select_from(DeviceToken).where(
            DeviceToken.device_id == UUID(racing["deviceId"]), DeviceToken.revoked_at.is_(None),
        )) == 0

    expect(await client.post(
        f"/v1/me/devices/{device_id}/revoke", headers=authorization(primary),
    ), 204)
    expect(await client.post(
        f"/v1/me/devices/{device_id}/rotate-token", json={}, headers=authorization(primary),
    ), 401)


async def main():
    realm = json.loads((ROOT / "test-support/oidc/realm.json").read_text())
    tokens = [provider_tokens(user) for user in realm["users"]]
    try:
        await postgres.prepare_database()
        result = postgres.migrate("upgrade", "20261025_01")
        assert result.returncode == 0, "Access migrations failed"
        with TemporaryDirectory(prefix="access-", dir=ROOT / ".tmp") as temporary:
            directory = Path(temporary).resolve()
            assert directory.is_relative_to(ROOT / ".tmp")
            for name in list(os.environ):
                if name.upper().startswith(("API_", "OIDC_", "DB_", "POOL_")) or name.upper() == "SQLALCHEMY_DATABASE_URI":
                    del os.environ[name]
            os.environ.update({
                "API_ENVIRONMENT": "test",
                "SQLALCHEMY_DATABASE_URI": postgres.database_url("nightingale_app", postgres.APP_PASSWORD),
                "OIDC_ISSUER": oidc.ISSUER,
                "OIDC_JWKS_URI": f"{oidc.ISSUER}/protocol/openid-connect/certs",
                "OIDC_TLS_CA_FILE": str(CERTIFICATE),
            })
            sys.path.insert(0, str(ROOT))
            previous_directory = Path.cwd()
            os.chdir(directory)
            from src.application import app
            from src.core.db.session import async_session_factory, engine

            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://fixture") as client:
                    await check_access(client, async_session_factory, tokens)
            finally:
                await engine.dispose()
                os.chdir(previous_directory)
    finally:
        admin = await postgres.connect_admin()
        try:
            assert postgres.DATABASE.startswith("nightingale_test_") and len(postgres.DATABASE) == 49
            exists = await admin.fetchval("SELECT EXISTS(SELECT FROM pg_database WHERE datname=$1)", postgres.DATABASE)
            if exists:
                await admin.execute(f'DROP DATABASE "{postgres.DATABASE}" WITH (FORCE)')
        finally:
            await admin.close()

    print("Access checks passed: real Keycloak and PostgreSQL, hash-only storage, isolated devices, atomic rotation/revocation, concurrent rotation and rollback.")


if __name__ == "__main__":
    asyncio.run(main())
