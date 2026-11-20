from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, Numeric, Text, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from src.core.db.model import Base, Date


class DiagnosticReport(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    source_name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, server_default="unknown")
    sample_date: Mapped[str | None] = mapped_column(Text)
    issued_date: Mapped[str | None] = mapped_column(Text)
    report_kind: Mapped[str] = mapped_column(Text)
    report_status: Mapped[str] = mapped_column(Text)
    attachment_id: Mapped[UUID | None]
    clinical_summary: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")
    attachment: Mapped[ReportAttachment | None] = relationship(
        primaryjoin=lambda: and_(
            foreign(DiagnosticReport.account_id) == ReportAttachment.account_id,
            foreign(DiagnosticReport.attachment_id) == ReportAttachment.id,
            foreign(DiagnosticReport.patient_id) == ReportAttachment.patient_id,
        ),
        viewonly=True,
    )


class DiagnosticReportHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    encounter_id: Mapped[UUID | None]
    source_name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    sample_date: Mapped[str | None] = mapped_column(Text)
    issued_date: Mapped[str | None] = mapped_column(Text)
    report_kind: Mapped[str] = mapped_column(Text)
    report_status: Mapped[str] = mapped_column(Text)
    attachment_id: Mapped[UUID | None]
    clinical_summary: Mapped[str | None] = mapped_column(Text)
    captured_at_local: Mapped[datetime | None]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class DiagnosticReportResult(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    report_id: Mapped[UUID]
    analyte_name: Mapped[str] = mapped_column(Text)
    result_kind: Mapped[str] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    text_value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(Text)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric)
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric)
    reference_text: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class DiagnosticReportResultHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    report_id: Mapped[UUID]
    analyte_name: Mapped[str] = mapped_column(Text)
    result_kind: Mapped[str] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    text_value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(Text)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric)
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric)
    reference_text: Mapped[str | None] = mapped_column(Text)
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]


class ReportAttachment(Date, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID]
    patient_id: Mapped[UUID]
    file_name: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    byte_size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime]
    record_status: Mapped[str] = mapped_column(Text, server_default="valid")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(server_default="1")


class ReportAttachmentHistory(Date, Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID]
    file_name: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    byte_size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime]
    record_status: Mapped[str] = mapped_column(Text)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[UUID]
    updated_by_user_id: Mapped[UUID]
    action: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID]
    operation_id: Mapped[UUID]
    changed_at: Mapped[datetime]
