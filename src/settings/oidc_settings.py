from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.api_settings import api_settings


class OIDCSettings(BaseSettings):
    issuer: str | None = None
    jwks_uri: str | None = None
    public_client_id: str = "nightingale-desktop-test"
    audience: str = "nightingale-api"
    tls_ca_file: str | None = None

    @field_validator("issuer", "jwks_uri")
    def validate_endpoint(cls, value: str | None) -> str | None:
        if value is None:
            return None

        url = urlparse(value)

        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
            or (url.port is not None and not 1 <= url.port <= 65535)
        ):
            raise ValueError("El endpoint OIDC no es válido")

        if url.scheme == "http" and (
            api_settings.environment == "production"
            or url.hostname not in ("localhost", "127.0.0.1", "::1")
        ):
            raise ValueError("OIDC requiere HTTPS fuera de loopback local")

        return value

    model_config = SettingsConfigDict(
        env_prefix="OIDC_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )


oidc_settings = OIDCSettings()
