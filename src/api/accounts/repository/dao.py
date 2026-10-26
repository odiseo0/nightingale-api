from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import (
    Account,
    AccountDeviceAccess,
    AccountInvitation,
    AccountMembership,
    AccountProfessional,
    Professional,
)


class AccountDAO(DAO[Account, BaseModel, BaseModel]):
    async def revise(
        self, db: AsyncSession, account_id: UUID, changes: dict, now: datetime
    ):
        account = await self.get_for_update(
            db, account_id, execution_options={"populate_existing": True}
        )
        return await self.update(
            db,
            account_id,
            {**changes, "version": account.version + 1, "updated_at": now},
            commit=False,
        )

    async def can_bootstrap(self, db: AsyncSession) -> bool:
        return await db.scalar(
            text("SELECT has_schema_privilege(current_user,'nightingale','CREATE')")
        )

    async def get_server_time(self, db: AsyncSession) -> datetime:
        return await db.scalar(select(func.clock_timestamp()))

    async def is_known_time_zone(self, db: AsyncSession, name: str) -> bool:
        # Use the same catalog as the account constraint; no OS tzdata is needed.
        # https://www.postgresql.org/docs/18/view-pg-timezone-names.html
        return await db.scalar(
            text("SELECT EXISTS(SELECT FROM pg_timezone_names WHERE name=:name)"),
            {"name": name},
        )

    async def get_visible(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        offset: int = 0,
        shows: int = 100,
    ) -> tuple[list[Account], int]:
        statement = (
            select(self.model)
            .join(AccountMembership, AccountMembership.account_id == self.model.id)
            .where(
                AccountMembership.user_id == user_id,
                AccountMembership.status == "active",
                self.model.kind == "independent",
                or_(self.model.status == "active", self.model.owner_user_id == user_id),
            )
        )
        total = await self.count(db, statement)
        page = (
            statement.order_by(self.model.id)
            .offset(offset)
            .limit(shows)
            .with_for_update(read=True, of=[self.model, AccountMembership])
            .execution_options(populate_existing=True)
        )
        accounts = (await db.scalars(page)).all()

        return list(accounts), total

    async def get_for_member(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> tuple[Account, AccountMembership] | EmptyType:
        row = (
            await db.execute(
                select(self.model, AccountMembership)
                .join(AccountMembership, AccountMembership.account_id == self.model.id)
                .where(
                    self.model.id == account_id,
                    self.model.kind == "independent",
                    AccountMembership.user_id == user_id,
                    AccountMembership.status == "active",
                )
                .with_for_update(read=True, of=[self.model, AccountMembership])
                .execution_options(populate_existing=True)
            )
        ).one_or_none()

        return tuple(row) if row is not None else Empty


class AccountMembershipDAO(DAO[AccountMembership, BaseModel, BaseModel]):
    async def page(self, db: AsyncSession, account_id: UUID, offset: int, shows: int):
        statement = select(self.model).where(self.model.account_id == account_id)
        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.user_id).offset(offset).limit(shows)
            )
        ).all()

        return list(rows), total

    async def get_scoped(self, db: AsyncSession, account_id: UUID, user_id: UUID):
        row = await db.scalar(
            select(self.model)
            .where(self.model.account_id == account_id, self.model.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return row if row is not None else Empty

    async def set_status(
        self,
        db: AsyncSession,
        row: AccountMembership,
        status: str,
        now: datetime,
        *,
        commit: bool = True,
    ):
        row.status = status
        row.version += 1
        row.updated_at = now

        await self.flush(db)

        if commit:
            await db.commit()

        return row

    async def create_membership(
        self,
        db: AsyncSession,
        account_id: UUID,
        user_id: UUID,
        now: datetime,
        *,
        commit: bool = True,
    ) -> AccountMembership:
        membership = await self.add(
            db,
            self.model(
                account_id=account_id,
                user_id=user_id,
                created_at=now,
                updated_at=now,
            ),
        )

        if commit:
            await db.commit()

        return membership


class ProfessionalDAO(DAO[Professional, BaseModel, BaseModel]):
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        offset: int,
        shows: int,
        status: str | None = None,
    ):
        statement = (
            select(self.model)
            .join(
                AccountProfessional,
                AccountProfessional.professional_id == self.model.id,
            )
            .where(AccountProfessional.account_id == account_id)
        )

        if status is not None:
            statement = statement.where(self.model.status == status)

        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.id).offset(offset).limit(shows)
            )
        ).all()

        return list(rows), total

    async def lock_for_account(self, db: AsyncSession, account_id: UUID):
        await db.scalars(
            select(self.model)
            .join(
                AccountProfessional,
                AccountProfessional.professional_id == self.model.id,
            )
            .where(AccountProfessional.account_id == account_id)
            .order_by(self.model.id)
            .with_for_update(of=self.model)
        )

    async def rename(
        self, db: AsyncSession, professional_id: UUID, public_name: str, now: datetime
    ):
        professional = await self.get_for_update(
            db, professional_id, execution_options={"populate_existing": True}
        )

        return await self.update(
            db,
            professional_id,
            {
                "public_name": public_name,
                "version": professional.version + 1,
                "updated_at": now,
            },
            commit=False,
        )


class AccountProfessionalDAO(DAO[AccountProfessional, BaseModel, BaseModel]):
    async def link(
        self,
        db: AsyncSession,
        account_id: UUID,
        professional_id: UUID,
        user_id: UUID,
        now: datetime,
        *,
        commit: bool = True,
    ) -> AccountProfessional:
        link = await self.add(
            db,
            self.model(
                account_id=account_id,
                professional_id=professional_id,
                user_id=user_id,
                created_at=now,
                updated_at=now,
            ),
        )

        if commit:
            await db.commit()

        return link


class AccountDeviceAccessDAO(DAO[AccountDeviceAccess, BaseModel, BaseModel]):
    async def page(self, db: AsyncSession, account_id: UUID, offset: int, shows: int):
        statement = select(self.model).where(self.model.account_id == account_id)
        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.device_id).offset(offset).limit(shows)
            )
        ).all()

        return list(rows), total

    async def set_status(
        self,
        db: AsyncSession,
        row: AccountDeviceAccess,
        status: str,
        user_id: UUID,
        now: datetime,
    ):
        row.status = status
        row.changed_by_user_id = user_id
        row.updated_at = now
        row.version += 1

        await self.flush(db)

        return row

    async def register(
        self,
        db: AsyncSession,
        account_id: UUID,
        device_id: UUID,
        user_id: UUID,
        now: datetime,
        *,
        commit: bool = True,
    ) -> AccountDeviceAccess:
        access = await self.add(
            db,
            self.model(
                account_id=account_id,
                device_id=device_id,
                user_id=user_id,
                created_by_user_id=user_id,
                changed_by_user_id=user_id,
                created_at=now,
                updated_at=now,
            ),
        )

        if commit:
            await db.commit()

        return access

    async def get_scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        device_id: UUID,
    ) -> AccountDeviceAccess | EmptyType:
        device = await db.scalar(
            select(self.model)
            .where(
                self.model.account_id == account_id, self.model.device_id == device_id
            )
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )

        return device if device is not None else Empty


class AccountInvitationDAO(DAO[AccountInvitation, BaseModel, BaseModel]):
    async def get_scoped(self, db: AsyncSession, invitation_id: UUID, account_id: UUID):
        row = await db.scalar(
            select(self.model)
            .where(self.model.id == invitation_id, self.model.account_id == account_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return row if row is not None else Empty

    async def resolve(
        self,
        db: AsyncSession,
        row: AccountInvitation,
        now: datetime,
        *,
        accepted_operation_id: UUID | None = None,
        commit: bool = True,
    ):
        row.status = "accepted" if accepted_operation_id is not None else "revoked"
        row.accepted_at = now if accepted_operation_id is not None else None
        row.accepted_operation_id = accepted_operation_id
        row.updated_at = now
        row.version += 1

        await self.flush(db)

        if commit:
            await db.commit()

        return row

    async def page(
        self,
        db: AsyncSession,
        now: datetime,
        *,
        account_id: UUID | None = None,
        user_id: UUID | None = None,
        status: str | None = None,
        offset: int = 0,
        shows: int = 100,
    ):
        effective_status = case(
            (
                (self.model.status == "pending") & (self.model.expires_at <= now),
                "expired",
            ),
            else_=self.model.status,
        )
        statement = select(self.model)

        if account_id is not None:
            statement = statement.where(self.model.account_id == account_id)

        if user_id is not None:
            statement = statement.where(self.model.invitee_user_id == user_id)

        if status is not None:
            statement = statement.where(effective_status == status)

        total = await self.count(db, statement)
        rows = (
            await db.scalars(
                statement.order_by(self.model.id).offset(offset).limit(shows)
            )
        ).all()

        return list(rows), total


dao_accounts = AccountDAO(Account)
dao_memberships = AccountMembershipDAO(AccountMembership)
dao_professionals = ProfessionalDAO(Professional)
dao_account_professionals = AccountProfessionalDAO(AccountProfessional)
dao_account_devices = AccountDeviceAccessDAO(AccountDeviceAccess)
dao_invitations = AccountInvitationDAO(AccountInvitation)
