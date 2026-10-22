from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory

    if factory is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    async with factory() as db:
        yield db


@asynccontextmanager
async def session(factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    """Open a session without choosing when the caller commits."""
    async with factory() as db:
        yield db
