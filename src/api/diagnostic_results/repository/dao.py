from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import DAO
from src.core.schema import BaseModel

from .models import (
    DiagnosticReport,
    DiagnosticReportHistory,
    DiagnosticReportResult,
    DiagnosticReportResultHistory,
    ReportAttachment,
    ReportAttachmentHistory,
)


class DiagnosticReportDAO(DAO[DiagnosticReport, BaseModel, BaseModel]):
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

    async def for_attachment(
        self, db: AsyncSession, account_id: UUID, attachment_id: UUID
    ) -> UUID | None:
        return await db.scalar(
            select(self.model.id)
            .join(self.model.attachment)
            .where(
                self.model.account_id == account_id,
                ReportAttachment.id == attachment_id,
            )
        )


class DiagnosticReportResultDAO(DAO[DiagnosticReportResult, BaseModel, BaseModel]):
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

    async def page_for_report(
        self, db: AsyncSession, account_id: UUID, report_id: UUID, query
    ) -> tuple[list[DiagnosticReportResult], int]:
        statement = select(self.model).where(
            self.model.account_id == account_id,
            self.model.report_id == report_id,
        )
        if query.record_status is not None:
            statement = statement.where(self.model.record_status == query.record_status)
        else:
            statement = statement.where(self.model.record_status == "valid")

        total = await self.count(db, statement)
        rows = await db.scalars(
            statement.order_by(self.model.id)
            .offset((query.page - 1) * query.shows)
            .limit(query.shows)
        )

        return list(rows), total


class ReportAttachmentDAO(DAO[ReportAttachment, BaseModel, BaseModel]):
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


dao_reports = DiagnosticReportDAO(DiagnosticReport)
dao_report_histories = DAO(DiagnosticReportHistory)
dao_report_results = DiagnosticReportResultDAO(DiagnosticReportResult)
dao_report_result_histories = DAO(DiagnosticReportResultHistory)
dao_report_attachments = ReportAttachmentDAO(ReportAttachment)
dao_report_attachment_histories = DAO(ReportAttachmentHistory)
