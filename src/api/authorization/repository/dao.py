from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.domain.authorization import ExternalIdentity
from src.core.db import DAO, DAOError
from src.core.db.dao import catch_sqlalchemy_exception
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import AppUser, Device, DeviceToken


class AppUserDAO(DAO[AppUser, BaseModel, BaseModel]):
    async def lock_identified(self, db: AsyncSession, user_ids: list[UUID]) -> None:
        await db.scalars(
            select(self.model)
            .where(self.model.id.in_(user_ids))
            .order_by(self.model.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    async def get_identified(
        self, db: AsyncSession, user_ids: list[UUID]
    ) -> list[AppUser]:
        return list(
            (
                await db.scalars(select(self.model).where(self.model.id.in_(user_ids)))
            ).all()
        )

    async def get_server_time(self, db: AsyncSession) -> datetime:
        return (await db.execute(select(func.clock_timestamp()))).scalar_one()

    async def get_or_create(
        self,
        db: AsyncSession,
        identity: ExternalIdentity,
        now: datetime,
        *,
        commit: bool = True,
    ) -> AppUser:
        statement = (
            insert(self.model)
            .values(
                id=uuid7(),
                oidc_issuer=identity.issuer,
                oidc_subject=identity.subject,
                display_name=identity.display_name,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[self.model.oidc_issuer, self.model.oidc_subject]
            )
        )

        with catch_sqlalchemy_exception():
            await db.execute(statement)

            if commit:
                await db.commit()

        # Refresh after waiting for the identity lock; cached state can be revoked.
        # https://docs.sqlalchemy.org/en/21/orm/queryguide/api.html#populate-existing
        user = await db.scalar(
            select(self.model)
            .where(
                self.model.oidc_issuer == identity.issuer,
                self.model.oidc_subject == identity.subject,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if user is None:
            raise DAOError("La identidad creada no pudo recuperarse")

        return user


class DeviceDAO(DAO[Device, BaseModel, BaseModel]):
    async def get_identified(
        self, db: AsyncSession, device_ids: list[UUID]
    ) -> list[Device]:
        return list(
            (
                await db.scalars(
                    select(self.model).where(self.model.id.in_(device_ids))
                )
            ).all()
        )

    async def get_owned_for_update(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
    ) -> Device | EmptyType:
        device = await db.scalar(
            select(self.model)
            .where(self.model.id == device_id, self.model.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return device if device is not None else Empty


class DeviceTokenDAO(DAO[DeviceToken, BaseModel, BaseModel]):
    async def revoke_for_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        now: datetime,
        *,
        commit: bool = True,
    ) -> None:
        statement = (
            update(self.model)
            .where(self.model.device_id == device_id, self.model.revoked_at.is_(None))
            .values(revoked_at=now)
        )

        with catch_sqlalchemy_exception():
            await db.execute(statement)

            if commit:
                await db.commit()


dao_users = AppUserDAO(AppUser)
dao_devices = DeviceDAO(Device)
dao_device_tokens = DeviceTokenDAO(DeviceToken)
