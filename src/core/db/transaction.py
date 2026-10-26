from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[None]:
    """Own one transaction on the given session; DAO calls must use commit=False."""
    # begin commits on success and rolls back on error; it rejects nested scopes.
    # https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.begin
    async with db.begin():
        yield
