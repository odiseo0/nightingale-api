from uuid import UUID

from sqlalchemy import delete, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel

from .models import (
    SpecialtyRecord,
    SpecialtyRecordHistory,
    SpecialtyRecordValueRow,
    SpecialtyTemplate,
    SpecialtyTemplateFieldRow,
    SpecialtyTemplateHistory,
)


class SpecialtyTemplateDAO(DAO[SpecialtyTemplate, BaseModel, BaseModel]):
    async def page(self, db, account_id: UUID, query):
        statement = select(self.model).where(self.model.account_id == account_id)

        if query.template_status is not None:
            statement = statement.where(
                self.model.template_status == query.template_status
            )

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.date_added, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def for_snapshot(
        self,
        db: AsyncSession,
        account_id: UUID,
        required: set[tuple[UUID, int]],
    ) -> list[SpecialtyTemplate | SpecialtyTemplateHistory]:
        current = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.template_status == "active",
            )
        )
        historical = await db.scalars(
            select(SpecialtyTemplateHistory).where(
                SpecialtyTemplateHistory.account_id == account_id,
                tuple_(SpecialtyTemplateHistory.id, SpecialtyTemplateHistory.version).in_(
                    required
                ),
            )
        )
        rows = {
            (row.id, row.version): row for row in [*current, *historical]
        }

        return [rows[key] for key in sorted(rows)]


class SpecialtyTemplateFieldDAO(
    DAO[SpecialtyTemplateFieldRow, BaseModel, BaseModel]
):
    async def for_version(
        self, db, account_id: UUID, template_id: UUID, template_version: int
    ) -> list[SpecialtyTemplateFieldRow]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.template_id == template_id,
                self.model.template_version == template_version,
            )
        )

        return list(rows)

    async def replace_for_version(
        self,
        db,
        account_id: UUID,
        template_id: UUID,
        template_version: int,
        fields: list[SpecialtyTemplateFieldRow],
    ) -> None:
        await db.execute(
            delete(self.model).where(
                self.model.account_id == account_id,
                self.model.template_id == template_id,
                self.model.template_version == template_version,
            )
        )
        for field in fields:
            await self.add(db, field)


class SpecialtyRecordDAO(DAO[SpecialtyRecord, BaseModel, BaseModel]):
    async def page(self, db, account_id: UUID, patient_id: UUID, query):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.template_id is not None:
            statement = statement.where(self.model.template_id == query.template_id)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.date_added, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(self, db, account_id: UUID) -> list[SpecialtyRecord]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class SpecialtyRecordValueDAO(DAO[SpecialtyRecordValueRow, BaseModel, BaseModel]):
    async def for_record_version(
        self, db, account_id: UUID, record_id: UUID, record_version: int
    ) -> list[SpecialtyRecordValueRow]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.record_id == record_id,
                self.model.record_version == record_version,
            )
        )

        return list(rows)

    async def replace_for_version(
        self,
        db,
        account_id: UUID,
        record_id: UUID,
        record_version: int,
        values: list[SpecialtyRecordValueRow],
    ) -> None:
        await db.execute(
            delete(self.model).where(
                self.model.account_id == account_id,
                self.model.record_id == record_id,
                self.model.record_version == record_version,
            )
        )
        for value in values:
            await self.add(db, value)


dao_templates = SpecialtyTemplateDAO(SpecialtyTemplate)
dao_template_histories = DAO(SpecialtyTemplateHistory)
dao_template_fields = SpecialtyTemplateFieldDAO(SpecialtyTemplateFieldRow)
dao_specialty_records = SpecialtyRecordDAO(SpecialtyRecord)
dao_specialty_record_histories = DAO(SpecialtyRecordHistory)
dao_specialty_record_values = SpecialtyRecordValueDAO(SpecialtyRecordValueRow)
