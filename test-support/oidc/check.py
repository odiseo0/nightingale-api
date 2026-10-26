import base64
import hashlib
import json
import secrets
import ssl
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

ISSUER = "https://127.0.0.1:18443/realms/nightingale-test"
CLIENT_ID = "nightingale-desktop-test"
REDIRECT_URI = "http://127.0.0.1:18765/callback"


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        if tag == "form" and attributes.get("id") == "kc-form-login":
            self.action = attributes.get("action")


def authorize(client, endpoint, user):
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = secrets.token_urlsafe(24)
    response = client.get(
        endpoint,
        params={
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "openid",
            "state": state,
            "nonce": secrets.token_urlsafe(24),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    if response.status_code == 200:
        form = LoginForm()
        form.feed(response.text)
        assert form.action, "Keycloak login form not found"
        assert urlparse(form.action).netloc == urlparse(ISSUER).netloc

        response = client.post(
            form.action,
            data={
                "username": user["username"],
                "password": user["credentials"][0]["value"],
            },
        )

    assert response.status_code in (302, 303), (
        f"Fixture login returned HTTP {response.status_code}"
    )

    location = urlparse(response.headers["location"])
    callback = urlparse(REDIRECT_URI)

    assert (location.scheme, location.netloc, location.path) == (
        callback.scheme,
        callback.netloc,
        callback.path,
    ), "Unexpected login redirect"
    query = parse_qs(location.query)
    assert query.get("state") == [state], "Authorization state changed"

    return query["code"][0], verifier


def exchange(client, endpoint, code, verifier):
    return client.post(
        endpoint,
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
    )


def main():
    # This checks the local provider flow. API signature validation belongs to T08.
    # https://www.keycloak.org/docs/latest/server_admin/index.html#_oidc_clients
    realm = json.loads(Path(__file__).with_name("realm.json").read_text())
    certificate = (
        Path(__file__).resolve().parents[2]
        / ".tmp/test-services/keycloak-test/keycloak-26.8.1/conf/fixture.pem"
    )
    tls = ssl.create_default_context(cafile=str(certificate))
    subjects = set()

    for user in realm["users"]:
        with httpx.Client(timeout=15, trust_env=False, verify=tls) as client:
            response = client.get(f"{ISSUER}/.well-known/openid-configuration")

            assert response.status_code == 200, "Test provider discovery failed"

            discovery = response.json()

            assert discovery["issuer"] == ISSUER

            authorization = discovery["authorization_endpoint"]
            token_endpoint = discovery["token_endpoint"]

            assert authorization.startswith(f"{ISSUER}/")
            assert token_endpoint.startswith(f"{ISSUER}/")

            code, verifier = authorize(client, authorization, user)
            response = exchange(client, token_endpoint, code, verifier)

            assert response.status_code == 200, "PKCE code exchange failed"

            token = response.json()["access_token"]
            payload = token.split(".")[1]
            claims = json.loads(
                base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
            )

            assert claims["iss"] == ISSUER
            audience = claims["aud"]

            assert "nightingale-api" in (
                audience if isinstance(audience, list) else [audience]
            )

            subjects.add(claims["sub"])

            response = exchange(client, token_endpoint, code, verifier)

            assert response.status_code == 400, "Provider accepted a reused code"

            code, verifier = authorize(client, authorization, user)
            response = exchange(client, token_endpoint, code, secrets.token_urlsafe(48))

            assert response.status_code == 400, "Provider accepted the wrong verifier"

    assert len(subjects) == len(realm["users"]), "Fixture users share a subject"

    with httpx.Client(timeout=15, trust_env=False, verify=tls) as client:
        response = client.get(
            authorization,
            params={
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": "openid",
            },
        )

        if response.status_code in (302, 303):
            error = parse_qs(urlparse(response.headers["location"]).query)
            assert error.get("error") == ["invalid_request"] and "code" not in error
        else:
            assert response.status_code == 400, "Provider accepted login without PKCE"

        response = client.post(
            token_endpoint,
            data={
                "client_id": CLIENT_ID,
                "grant_type": "password",
                "username": realm["users"][0]["username"],
                "password": realm["users"][0]["credentials"][0]["value"],
            },
        )

        assert response.status_code == 400, "Provider accepted a password grant"

    print(
        "PKCE S256 passed for three fixture users; reused codes, wrong verifiers, "
        "missing PKCE and password grants rejected."
    )


if __name__ == "__main__":
    main()
