from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import AccountSyncHead, ChangeLog, OperationReceipt


class AccountSyncHeadDAO(DAO[AccountSyncHead, BaseModel, BaseModel]):
    async def advance(
        self,
        db: AsyncSession,
        head: AccountSyncHead,
        now: datetime,
        *,
        permission_changed: bool = True,
        commit: bool = True,
    ) -> int:
        head.last_sequence += 1
        head.permission_epoch += int(permission_changed)
        head.updated_at = now
        await self.flush(db)

        if commit:
            await db.commit()

        return head.last_sequence

    async def lock_account(
        self, db: AsyncSession, account_id: UUID
    ) -> AccountSyncHead | EmptyType:
        head = await db.scalar(
            select(self.model)
            .where(self.model.account_id == account_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return head if head is not None else Empty

    async def get_server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def get_for_account(
        self,
        db: AsyncSession,
        account_id: UUID,
    ) -> AccountSyncHead | EmptyType:
        return await self.get_by(
            db,
            where={"account_id": account_id},
            execution_options={"populate_existing": True},
        )

    async def create_head(
        self,
        db: AsyncSession,
        account_id: UUID,
        now: datetime,
        *,
        commit: bool = True,
    ) -> AccountSyncHead:
        head = await self.add(
            db,
            self.model(
                account_id=account_id,
                created_at=now,
                updated_at=now,
            ),
        )

        if commit:
            await db.commit()

        return head


class OperationReceiptDAO(DAO[OperationReceipt, BaseModel, BaseModel]):
    async def can_purge(self, db: AsyncSession) -> bool:
        return await db.scalar(
            text(
                "SELECT has_table_privilege(current_user,'nightingale.operation_receipts','UPDATE')"
            )
        )

    async def purge_expired(self, db: AsyncSession) -> int:
        statement = (
            update(self.model)
            .where(
                self.model.result_expires_at <= func.clock_timestamp(),
                self.model.result_json.is_not(None),
                self.model.purged_at.is_(None),
            )
            .values(result_json=None, purged_at=func.clock_timestamp())
            .returning(self.model.operation_id)
        )
        result = await db.scalars(statement)

        return len(result.all())

    async def record(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> OperationReceipt:
        receipt = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return receipt

    async def get_scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        actor_user_id: UUID,
        operation_id: UUID,
    ) -> OperationReceipt | EmptyType:
        return await self.get_by(
            db,
            where={
                "account_id": account_id,
                "actor_user_id": actor_user_id,
                "operation_id": operation_id,
            },
            execution_options={"populate_existing": True},
        )


class ChangeLogDAO(DAO[ChangeLog, BaseModel, BaseModel]):
    async def append(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> None:
        await self.add(db, self.model(**values))

        if commit:
            await db.commit()


dao_heads = AccountSyncHeadDAO(AccountSyncHead)
dao_receipts = OperationReceiptDAO(OperationReceipt)
dao_changes = ChangeLogDAO(ChangeLog)
