from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.exc import DBAPIError

from .dao import DAOError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[None]:
    """Own one transaction on the given session; DAO calls must use commit=False."""
    # begin commits on success and rolls back on error; it rejects nested scopes.
    # https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.begin
    try:
        async with db.begin():
            yield
    except DBAPIError as error:
        # Include failures at commit (for example, deferred constraints) in the
        # same technical error boundary as DAO calls, after begin rolls back.
        raise DAOError from error


@asynccontextmanager
async def savepoint(db: AsyncSession) -> AsyncGenerator[None]:
    """Revert a guarded effect without committing or replacing its transaction."""
    # Releasing a savepoint does not commit the outer operation.
    # https://docs.sqlalchemy.org/en/21/orm/session_transaction.html#using-savepoint
    async with db.begin_nested():
        yield
