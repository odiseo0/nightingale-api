from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class DBSettings(BaseSettings):
    DB_HOST: str | None = None
    DB_NAME: str | None = None
    DB_PORT: int | None = None
    DB_USERNAME: str | None = None
    DB_PASSWORD: str | None = Field(default=None, repr=False)

    SQLALCHEMY_DATABASE_URI: str | None = Field(default=None, repr=False)
    pool_size: int = 5
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_overflow: int = 10

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            fields = ("DB_HOST", "DB_NAME", "DB_USERNAME", "DB_PASSWORD")
            values = [info.data.get(field) for field in fields]

            if not any(value is not None for value in values):
                return None

            if not all(values):
                raise ValueError("Faltan datos de conexión a PostgreSQL")

            # URL.create conserva los caracteres especiales de la contraseña.
            # https://docs.sqlalchemy.org/en/21/core/engines.html#sqlalchemy.engine.URL.create
            v = URL.create(
                "postgresql+asyncpg",
                username=info.data["DB_USERNAME"],
                password=info.data["DB_PASSWORD"],
                host=info.data["DB_HOST"],
                port=info.data.get("DB_PORT") or 5432,
                database=info.data["DB_NAME"],
            ).render_as_string(hide_password=False)

        try:
            url = make_url(v)
        except ArgumentError, ValueError:
            raise ValueError("La conexión a PostgreSQL no es válida") from None

        if (
            url.drivername != "postgresql+asyncpg"
            or not all((url.host, url.database, url.username, url.password))
            or (url.port is not None and not 1 <= url.port <= 65535)
        ):
            raise ValueError("La conexión a PostgreSQL no es válida")

        return v

    @field_validator("DB_PORT")
    def validate_db_port(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535")

        return v

    @field_validator("pool_size", "pool_timeout")
    def validate_pool_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("El valor debe ser mayor que cero")

        return v

    @field_validator("pool_recycle", "pool_overflow")
    def validate_pool_limit(cls, v: int) -> int:
        if v < 0:
            raise ValueError("El valor no puede ser negativo")

        return v

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )


db_settings = DBSettings()
