from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.settings.db_settings import DBSettings


def create_db_engine(settings: DBSettings) -> AsyncEngine | None:
    if settings.url is None:
        return None

    return create_async_engine(
        settings.url,
        pool_size=settings.pool_size,
        pool_timeout=settings.pool_timeout,
        pool_recycle=settings.pool_recycle,
        max_overflow=settings.pool_overflow,
        pool_pre_ping=True,
        connect_args={"server_settings": {"TimeZone": "UTC"}},
    )
