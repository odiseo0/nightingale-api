from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import EmptyType

from .models import AccountSyncHead


class AccountSyncHeadDAO(DAO[AccountSyncHead, BaseModel, BaseModel]):
    async def get_for_account(
        self, db: AsyncSession, account_id: UUID,
    ) -> AccountSyncHead | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id},
            execution_options={"populate_existing": True},
        )

    async def create_head(
        self, db: AsyncSession, account_id: UUID, now: datetime, *, commit: bool = True,
    ) -> AccountSyncHead:
        head = await self.add(db, self.model(
            account_id=account_id, created_at=now, updated_at=now,
        ))
        if commit:
            await db.commit()

        return head


dao_heads = AccountSyncHeadDAO(AccountSyncHead)
