from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, text, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import (
    AccountSyncHead,
    ChangeLog,
    OperationReceipt,
    SyncSnapshot,
    SyncSnapshotItem,
)


class AccountSyncHeadDAO(DAO[AccountSyncHead, BaseModel, BaseModel]):
    async def local_date(self, db: AsyncSession, zone: str, instant: datetime) -> date:
        return (
            await db.execute(
                text(
                    "SELECT CAST(timezone(:zone,CAST(:instant AS timestamptz)) AS date)"
                ),
                {"zone": zone, "instant": instant},
            )
        ).scalar_one()

    async def window_bounds(
        self, db: AsyncSession, start: date, end: date, zone: str
    ) -> tuple[datetime, datetime]:
        # Use the same ambiguous/nonexistent local-time rule as the table CHECK.
        # https://www.postgresql.org/docs/18/datetime-invalid-input.html
        row = (
            await db.execute(
                text("""
            SELECT CAST(CAST(:start AS date) AS timestamp) AT TIME ZONE :zone,
                   CAST(CAST(:end AS date) AS timestamp) AT TIME ZONE :zone
        """),
                {"start": start, "end": end, "zone": zone},
            )
        ).one()

        return row[0], row[1]

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
                "SELECT has_table_privilege(current_user,'nightingale.operation_receipts','UPDATE') "
                "AND has_table_privilege(current_user,'nightingale.change_log','DELETE') "
                "AND has_table_privilege(current_user,'nightingale.sync_snapshots','DELETE')"
            )
        )

    async def purge_expired(self, db: AsyncSession) -> int:
        keys = (
            select(
                self.model.account_id, self.model.actor_user_id, self.model.operation_id
            )
            .where(
                self.model.result_expires_at <= func.clock_timestamp(),
                self.model.result_json.is_not(None),
                self.model.purged_at.is_(None),
            )
            .order_by(
                self.model.result_expires_at,
                self.model.account_id,
                self.model.actor_user_id,
                self.model.operation_id,
            )
            .limit(500)
            .with_for_update(skip_locked=True)
        )
        statement = (
            update(self.model)
            .where(
                tuple_(
                    self.model.account_id,
                    self.model.actor_user_id,
                    self.model.operation_id,
                ).in_(keys),
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
    async def purge_expired(self, db: AsyncSession) -> int:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        cutoff = now - timedelta(days=90)
        head = await db.scalar(
            select(AccountSyncHead)
            .join(
                self.model,
                (
                    (self.model.account_id == AccountSyncHead.account_id)
                    & (self.model.sequence == AccountSyncHead.retained_from_sequence)
                    & (self.model.ordinal == 1)
                ),
            )
            .where(self.model.accepted_at <= cutoff)
            .order_by(AccountSyncHead.account_id)
            .limit(1)
            .with_for_update(skip_locked=True, of=AccountSyncHead)
            .execution_options(populate_existing=True)
        )

        if head is None:
            return 0

        groups = (
            await db.execute(
                select(self.model.sequence, func.max(self.model.accepted_at))
                .where(self.model.account_id == head.account_id)
                .group_by(self.model.sequence)
                .order_by(self.model.sequence)
                .limit(100)
            )
        ).all()
        retained_from = head.retained_from_sequence

        for sequence, accepted_at in groups:
            if accepted_at > cutoff:
                break
            retained_from = sequence + 1

        count = retained_from - head.retained_from_sequence
        await db.execute(
            delete(self.model).where(
                self.model.account_id == head.account_id,
                self.model.sequence < retained_from,
            )
        )
        head.retained_from_sequence = retained_from
        head.updated_at = now
        await self.flush(db)

        return count

    async def groups_after(
        self,
        db: AsyncSession,
        account_id: UUID,
        sequence: int,
        through: int,
        *,
        groups: int = 100,
    ) -> tuple[list[ChangeLog], bool]:
        sequences = list(
            await db.scalars(
                select(self.model.sequence)
                .where(
                    self.model.account_id == account_id,
                    self.model.sequence > sequence,
                    self.model.sequence <= through,
                )
                .distinct()
                .order_by(self.model.sequence)
                .limit(groups + 1)
            )
        )

        if not sequences:
            return [], False

        rows = list(
            await db.scalars(
                select(self.model)
                .where(
                    self.model.account_id == account_id,
                    self.model.sequence.in_(sequences[:groups]),
                )
                .order_by(self.model.sequence, self.model.ordinal)
            )
        )

        return rows, len(sequences) > groups

    async def append(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> None:
        await self.add(db, self.model(**values))

        if commit:
            await db.commit()


dao_heads = AccountSyncHeadDAO(AccountSyncHead)
dao_receipts = OperationReceiptDAO(OperationReceipt)
dao_changes = ChangeLogDAO(ChangeLog)


class SyncSnapshotDAO(DAO[SyncSnapshot, BaseModel, BaseModel]):
    async def purge_expired(self, db: AsyncSession) -> int:
        expired = (
            select(self.model.id)
            .where(self.model.expires_at <= func.clock_timestamp())
            .order_by(self.model.expires_at, self.model.id)
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        removed = await db.scalars(
            delete(self.model)
            .where(self.model.id.in_(expired))
            .returning(self.model.id)
        )

        return len(removed.all())

    async def release(self, db: AsyncSession, snapshot_id: UUID) -> None:
        await db.execute(delete(self.model).where(self.model.id == snapshot_id))


class SyncSnapshotItemDAO(DAO[SyncSnapshotItem, BaseModel, BaseModel]):
    async def record(
        self, db: AsyncSession, values: dict[str, object], *, commit: bool = True
    ) -> SyncSnapshotItem:
        row = await self.add(db, self.model(**values))

        if commit:
            await db.commit()

        return row

    async def page(
        self, db: AsyncSession, snapshot_id: UUID, offset: int, shows: int
    ) -> list[SyncSnapshotItem]:
        return list(
            await db.scalars(
                select(self.model)
                .where(self.model.snapshot_id == snapshot_id)
                .order_by(self.model.ordinal)
                .offset(offset)
                .limit(shows)
            )
        )


dao_snapshots = SyncSnapshotDAO(SyncSnapshot)
dao_snapshot_items = SyncSnapshotItemDAO(SyncSnapshotItem)
