from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base

_UUIDV7 = (
    "substring(id::text from 15 for 1)='7' AND "
    "substring(id::text from 20 for 1) IN ('8','9','a','b')"
)


class PatientCharge(Base):
    __tablename__: str = "patient_charges"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "patient_id"],
            [
                "nightingale.account_patients.account_id",
                "nightingale.account_patients.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "appointment_id", "patient_id"],
            [
                "nightingale.appointments.account_id",
                "nightingale.appointments.id",
                "nightingale.appointments.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "encounter_id", "patient_id"],
            [
                "nightingale.clinical_encounters.account_id",
                "nightingale.clinical_encounters.id",
                "nightingale.clinical_encounters.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["created_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("btrim(description)<>''", name="description"),
        CheckConstraint("amount >= 0", name="amount"),
        CheckConstraint("currency IN ('USD','VES')", name="currency"),
        CheckConstraint(
            "price_source IN ('offer','base','manual')", name="price_source"
        ),
        CheckConstraint("status IN ('draft','issued','cancelled')", name="status"),
        CheckConstraint(
            "issued_at IS NULL OR isfinite(issued_at)", name="issued_at_finite"
        ),
        CheckConstraint(
            "cancelled_at IS NULL OR isfinite(cancelled_at)", name="cancelled_at_finite"
        ),
        CheckConstraint(
            "cancellation_reason IS NULL OR btrim(cancellation_reason)<>''",
            name="cancellation_reason",
        ),
        CheckConstraint(
            "(status='draft' AND issued_at IS NULL AND cancelled_at IS NULL) OR "
            "(status='issued' AND issued_at IS NOT NULL AND cancelled_at IS NULL) OR "
            "(status='cancelled' AND issued_at IS NOT NULL AND cancelled_at IS NOT NULL "
            "AND cancellation_reason IS NOT NULL)",
            name="status_coherence",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint(
            "isfinite(updated_at) AND updated_at >= created_at",
            name="updated_at_finite",
        ),
        CheckConstraint("version > 0", name="version"),
        Index("uq_patient_charges_id_account", "id", "account_id", unique=True),
        Index("ix_patient_charges_patient", "account_id", "patient_id", "created_at"),
        Index("ix_patient_charges_status", "account_id", "status", "created_at"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    patient_id: Mapped[UUID] = mapped_column()
    appointment_id: Mapped[UUID | None] = mapped_column()
    encounter_id: Mapped[UUID | None] = mapped_column()
    service_id: Mapped[UUID | None] = mapped_column()
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(Text)
    price_source: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="draft")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class ChargeHistory(Base):
    __tablename__: str = "charge_histories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["charge_id", "account_id"],
            [
                "nightingale.patient_charges.id",
                "nightingale.patient_charges.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["actor_id"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint(
            "action IN ('created','draft_updated','amount_adjusted','issued',"
            "'cancelled','corrected')",
            name="action",
        ),
        CheckConstraint("charge_version > 0", name="charge_version"),
        CheckConstraint("reason IS NULL OR btrim(reason)<>''", name="reason"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        Index("ix_charge_histories_charge", "charge_id", "created_at"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    charge_id: Mapped[UUID] = mapped_column()
    account_id: Mapped[UUID] = mapped_column()
    action: Mapped[str] = mapped_column(Text)
    charge_version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[UUID] = mapped_column()
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class BillingExchangeRate(Base):
    __tablename__: str = "billing_exchange_rates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"], ["nightingale.accounts.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["registered_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("isfinite(rate_date)", name="rate_date_finite"),
        CheckConstraint("rate_ves_per_usd > 0", name="rate"),
        CheckConstraint("btrim(source)<>''", name="source"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        Index("uq_billing_exchange_rates", "account_id", "rate_date", unique=True),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    rate_date: Mapped[date] = mapped_column(Date)
    rate_ves_per_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    source: Mapped[str] = mapped_column(Text)
    registered_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class PatientBillingGrant(Base):
    __tablename__: str = "patient_billing_grants"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "patient_id"],
            [
                "nightingale.account_patients.account_id",
                "nightingale.account_patients.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "appointment_id", "patient_id"],
            [
                "nightingale.appointments.account_id",
                "nightingale.appointments.id",
                "nightingale.appointments.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["charge_id", "account_id"],
            [
                "nightingale.patient_charges.id",
                "nightingale.patient_charges.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["created_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="token_hash"),
        CheckConstraint(
            "cardinality(actions) > 0 AND actions <@ "
            "ARRAY['read_charge','submit_report','read_result','read_receipt']::text[]",
            name="actions",
        ),
        CheckConstraint(
            "appointment_id IS NOT NULL OR charge_id IS NOT NULL", name="object"
        ),
        CheckConstraint("isfinite(expires_at)", name="expires_at_finite"),
        CheckConstraint(
            "revoked_at IS NULL OR isfinite(revoked_at)", name="revoked_at_finite"
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        Index("ix_patient_billing_grants_patient", "account_id", "patient_id"),
        Index("ix_patient_billing_grants_appointment", "appointment_id"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    patient_id: Mapped[UUID] = mapped_column()
    appointment_id: Mapped[UUID | None] = mapped_column()
    charge_id: Mapped[UUID | None] = mapped_column()
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    actions: Mapped[list[str]] = mapped_column(ARRAY(Text))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class PatientPaymentReport(Base):
    __tablename__: str = "patient_payment_reports"
    __table_args__ = (
        ForeignKeyConstraint(
            ["charge_id", "account_id"],
            [
                "nightingale.patient_charges.id",
                "nightingale.patient_charges.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "patient_id"],
            [
                "nightingale.account_patients.account_id",
                "nightingale.account_patients.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["grant_id"], ["nightingale.patient_billing_grants.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["previous_report_id"],
            ["nightingale.patient_payment_reports.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="status"),
        CheckConstraint("isfinite(declared_paid_on)", name="paid_on_finite"),
        CheckConstraint("declared_amount > 0", name="amount"),
        CheckConstraint("declared_currency IN ('USD','VES')", name="currency"),
        CheckConstraint("btrim(declared_method)<>''", name="method"),
        CheckConstraint(
            "declared_reference_last4 IS NULL OR declared_reference_last4 ~ '^[0-9]{4}$'",
            name="reference_last4",
        ),
        CheckConstraint(
            "declared_note IS NULL OR btrim(declared_note)<>''", name="note"
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint(
            "isfinite(updated_at) AND updated_at >= created_at",
            name="updated_at_finite",
        ),
        CheckConstraint("version > 0", name="version"),
        Index("uq_patient_payment_reports_id_account", "id", "account_id", unique=True),
        Index("ix_patient_payment_reports_inbox", "account_id", "status", "created_at"),
        Index("ix_patient_payment_reports_charge", "charge_id", "created_at"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    charge_id: Mapped[UUID] = mapped_column()
    patient_id: Mapped[UUID] = mapped_column()
    grant_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(Text, server_default="pending")
    declared_paid_on: Mapped[date] = mapped_column(Date)
    declared_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    declared_currency: Mapped[str] = mapped_column(Text)
    declared_method: Mapped[str] = mapped_column(Text)
    declared_reference_last4: Mapped[str | None] = mapped_column(Text)
    declared_note: Mapped[str | None] = mapped_column(Text)
    previous_report_id: Mapped[UUID | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class PatientPaymentEvidence(Base):
    __tablename__: str = "patient_payment_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["report_id"],
            ["nightingale.patient_payment_reports.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("btrim(storage_key)<>''", name="storage_key"),
        CheckConstraint(
            "content_type IN ('image/jpeg','image/png','application/pdf')",
            name="content_type",
        ),
        CheckConstraint("size_bytes > 0 AND size_bytes <= 5242880", name="size"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="sha256"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    report_id: Mapped[UUID] = mapped_column(unique=True)
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    content_type: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class BillingReview(Base):
    __tablename__: str = "billing_reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["report_id", "account_id"],
            [
                "nightingale.patient_payment_reports.id",
                "nightingale.patient_payment_reports.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reviewer_id"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["billing_exchange_rate_id"],
            ["nightingale.billing_exchange_rates.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("decision IN ('approved','rejected')", name="decision"),
        CheckConstraint(
            "verified_paid_on IS NULL OR isfinite(verified_paid_on)",
            name="paid_on_finite",
        ),
        CheckConstraint(
            "verified_amount IS NULL OR verified_amount > 0", name="amount"
        ),
        CheckConstraint(
            "verified_currency IS NULL OR verified_currency IN ('USD','VES')",
            name="currency",
        ),
        CheckConstraint(
            "internal_note IS NULL OR btrim(internal_note)<>''", name="internal_note"
        ),
        CheckConstraint("reason IS NULL OR btrim(reason)<>''", name="reason"),
        CheckConstraint(
            "(decision='approved' AND verified_paid_on IS NOT NULL "
            "AND verified_amount IS NOT NULL AND verified_currency IS NOT NULL) OR "
            "(decision='rejected' AND reason IS NOT NULL)",
            name="coherence",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    report_id: Mapped[UUID] = mapped_column(unique=True)
    account_id: Mapped[UUID] = mapped_column()
    reviewer_id: Mapped[UUID] = mapped_column()
    decision: Mapped[str] = mapped_column(Text)
    verified_paid_on: Mapped[date | None] = mapped_column(Date)
    verified_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    verified_currency: Mapped[str | None] = mapped_column(Text)
    billing_exchange_rate_id: Mapped[UUID | None] = mapped_column()
    internal_note: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class PatientPayment(Base):
    __tablename__: str = "patient_payments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["charge_id", "account_id"],
            [
                "nightingale.patient_charges.id",
                "nightingale.patient_charges.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "patient_id"],
            [
                "nightingale.account_patients.account_id",
                "nightingale.account_patients.patient_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["origin_report_id", "account_id"],
            [
                "nightingale.patient_payment_reports.id",
                "nightingale.patient_payment_reports.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["annulled_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["registered_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("origin IN ('patient_report','staff_entry')", name="origin"),
        CheckConstraint(
            "(origin='patient_report' AND origin_report_id IS NOT NULL) OR "
            "(origin='staff_entry' AND origin_report_id IS NULL)",
            name="origin_coherence",
        ),
        CheckConstraint("amount > 0", name="amount"),
        CheckConstraint("currency IN ('USD','VES')", name="currency"),
        CheckConstraint(
            "(amount_usd IS NULL AND exchange_rate IS NULL AND exchange_rate_date IS NULL "
            "AND exchange_rate_source IS NULL) OR "
            "(amount_usd IS NOT NULL AND amount_usd > 0 AND exchange_rate IS NOT NULL "
            "AND exchange_rate > 0 AND exchange_rate_date IS NOT NULL "
            "AND isfinite(exchange_rate_date) AND exchange_rate_source IS NOT NULL "
            "AND btrim(exchange_rate_source)<>'' AND currency='USD')",
            name="conversion_coherence",
        ),
        CheckConstraint("isfinite(paid_on)", name="paid_on_finite"),
        CheckConstraint("btrim(method)<>''", name="method"),
        CheckConstraint(
            "reference_last4 IS NULL OR reference_last4 ~ '^[0-9]{4}$'",
            name="reference_last4",
        ),
        CheckConstraint("status IN ('active','annulled')", name="status"),
        CheckConstraint(
            "(status='active' AND annulled_at IS NULL AND annulled_by IS NULL "
            "AND annulment_reason IS NULL) OR "
            "(status='annulled' AND annulled_at IS NOT NULL AND isfinite(annulled_at) "
            "AND annulled_by IS NOT NULL AND annulment_reason IS NOT NULL "
            "AND btrim(annulment_reason)<>'')",
            name="annulment_coherence",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint(
            "isfinite(updated_at) AND updated_at >= created_at",
            name="updated_at_finite",
        ),
        CheckConstraint("version > 0", name="version"),
        Index("uq_patient_payments_origin_report", "origin_report_id", unique=True),
        Index("ix_patient_payments_charge", "account_id", "charge_id", "status"),
        Index("ix_patient_payments_account", "account_id", "created_at"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    charge_id: Mapped[UUID] = mapped_column()
    patient_id: Mapped[UUID] = mapped_column()
    origin: Mapped[str] = mapped_column(Text)
    origin_report_id: Mapped[UUID | None] = mapped_column()
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(Text)
    amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    exchange_rate_date: Mapped[date | None] = mapped_column(Date)
    exchange_rate_source: Mapped[str | None] = mapped_column(Text)
    paid_on: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(Text)
    reference_last4: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    annulled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    annulled_by: Mapped[UUID | None] = mapped_column()
    annulment_reason: Mapped[str | None] = mapped_column(Text)
    registered_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class PaymentReceipt(Base):
    __tablename__: str = "payment_receipts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["payment_id"], ["nightingale.patient_payments.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(_UUIDV7, name="uuidv7"),
        CheckConstraint("btrim(storage_key)<>''", name="storage_key"),
        CheckConstraint("content_type='application/pdf'", name="content_type"),
        CheckConstraint("size_bytes > 0", name="size"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="sha256"),
        CheckConstraint("isfinite(issued_at)", name="issued_at_finite"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    payment_id: Mapped[UUID] = mapped_column(unique=True)
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    content_type: Mapped[str] = mapped_column(Text, server_default="application/pdf")
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(Text)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
