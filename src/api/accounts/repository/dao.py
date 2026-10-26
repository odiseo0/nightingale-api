from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import (
    Account,
    AccountDeviceAccess,
    AccountMembership,
    AccountProfessional,
    Professional,
)


class AccountDAO(DAO[Account, BaseModel, BaseModel]):
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
    pass


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


dao_accounts = AccountDAO(Account)
dao_memberships = AccountMembershipDAO(AccountMembership)
dao_professionals = ProfessionalDAO(Professional)
dao_account_professionals = AccountProfessionalDAO(AccountProfessional)
dao_account_devices = AccountDeviceAccessDAO(AccountDeviceAccess)
