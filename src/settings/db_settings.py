from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class DBSettings(BaseSettings):
    DB_HOST: str | None = None
    DB_NAME: str | None = None
    DB_PORT: int = Field(default=5432, ge=1, le=65535)
    DB_USERNAME: str | None = None
    DB_PASSWORD: SecretStr | None = None

    SQLALCHEMY_DATABASE_URI: SecretStr | None = None
    pool_size: int = Field(default=5, gt=0)
    pool_timeout: float = Field(default=30, gt=0)
    pool_recycle: int = Field(default=1800, gt=0)
    pool_overflow: int = Field(default=10, ge=0)

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    @property
    def url(self) -> URL | None:
        if self.SQLALCHEMY_DATABASE_URI is not None:
            return make_url(self.SQLALCHEMY_DATABASE_URI.get_secret_value())

        if all(
            value is None
            for value in (self.DB_HOST, self.DB_NAME, self.DB_USERNAME, self.DB_PASSWORD)
        ):
            return None

        return URL.create(
            "postgresql+asyncpg",
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD.get_secret_value() if self.DB_PASSWORD else None,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    @model_validator(mode="after")
    def validate_connection(self) -> DBSettings:
        try:
            url = self.url
        except (ArgumentError, ValueError, TypeError):
            raise ValueError("Invalid PostgreSQL connection settings") from None

        if url is not None and (
            url.drivername != "postgresql+asyncpg"
            or not url.host
            or not url.database
            or not url.username
        ):
            raise ValueError("Use a complete PostgreSQL connection with asyncpg")

        return self
