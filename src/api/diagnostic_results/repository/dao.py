from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType

from .models import (
    DiagnosticReport,
    DiagnosticReportHistory,
    DiagnosticReportResult,
    DiagnosticReportResultHistory,
    ReportAttachment,
    ReportAttachmentHistory,
)


class _Scoped:
    async def scoped(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        *,
        lock: bool = False,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if lock:
            statement = statement.with_for_update()

        row = await db.scalar(statement.execution_options(populate_existing=True))

        return Empty if row is None else row


class _HistoryPage:
    async def page(
        self,
        db: AsyncSession,
        account_id: UUID,
        entity_id: UUID,
        offset: int,
        shows: int,
        after_version: int | None,
    ):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.id == entity_id
        )

        if after_version is not None:
            statement = statement.where(self.model.version > after_version)

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.version).offset(offset).limit(shows)
        )

        return list(rows), total


class DiagnosticReportDAO(_Scoped, DAO[DiagnosticReport, BaseModel, BaseModel]):
    async def page(self, db, account_id: UUID, patient_id: UUID, query):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )

        if query.report_kind is not None:
            statement = statement.where(self.model.report_kind == query.report_kind)

        if query.report_status is not None:
            statement = statement.where(self.model.report_status == query.report_status)

        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.sample_date, self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total

    async def valid_snapshot(self, db, account_id: UUID) -> list[DiagnosticReport]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)


class DiagnosticReportHistoryDAO(
    _HistoryPage, DAO[DiagnosticReportHistory, BaseModel, BaseModel]
):
    pass


class DiagnosticReportResultDAO(
    _Scoped, DAO[DiagnosticReportResult, BaseModel, BaseModel]
):
    async def for_report(
        self, db, account_id: UUID, report_id: UUID
    ) -> list[DiagnosticReportResult]:
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id,
                self.model.report_id == report_id,
            )
        )

        return list(rows)


class DiagnosticReportResultHistoryDAO(
    _HistoryPage, DAO[DiagnosticReportResultHistory, BaseModel, BaseModel]
):
    pass


class ReportAttachmentDAO(_Scoped, DAO[ReportAttachment, BaseModel, BaseModel]):
    async def valid_snapshot(self, db, account_id):
        rows = await db.scalars(
            select(self.model).where(
                self.model.account_id == account_id, self.model.record_status == "valid"
            )
        )

        return list(rows)

    async def page_for_patient(self, db, account_id, patient_id, offset, shows):
        statement = select(self.model).where(
            self.model.account_id == account_id, self.model.patient_id == patient_id
        )
        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.uploaded_at, self.model.id)
            .offset(offset)
            .limit(shows)
        )

        return list(rows), total


class ReportAttachmentHistoryDAO(
    _HistoryPage, DAO[ReportAttachmentHistory, BaseModel, BaseModel]
):
    pass


dao_reports = DiagnosticReportDAO(DiagnosticReport)
dao_report_histories = DiagnosticReportHistoryDAO(DiagnosticReportHistory)
dao_report_results = DiagnosticReportResultDAO(DiagnosticReportResult)
dao_report_result_histories = DiagnosticReportResultHistoryDAO(
    DiagnosticReportResultHistory
)
dao_report_attachments = ReportAttachmentDAO(ReportAttachment)
dao_report_attachment_histories = ReportAttachmentHistoryDAO(ReportAttachmentHistory)
