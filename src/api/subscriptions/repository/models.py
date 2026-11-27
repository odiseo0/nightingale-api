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


class SubscriptionPlan(Base):
    __tablename__: str = "subscription_plans"
    __table_args__ = (
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint(
            "code IN ('independent','small_practice','medical_center')", name="code"
        ),
        CheckConstraint("btrim(name)<>''", name="name"),
        CheckConstraint("btrim(description)<>''", name="description"),
        CheckConstraint("status IN ('available','retired')", name="status"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint("isfinite(updated_at) AND updated_at >= created_at", name="updated_at_finite"),
        CheckConstraint("version > 0", name="version"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="available")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class SubscriptionPlanVersion(Base):
    __tablename__: str = "subscription_plan_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["plan_id"], ["nightingale.subscription_plans.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("seat_limit > 0", name="seat_limit"),
        CheckConstraint("price_30d_usd > 0", name="price_30d"),
        CheckConstraint("price_year_usd > 0", name="price_year"),
        CheckConstraint("currency='USD'", name="currency"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        Index("uq_subscription_plan_versions", "plan_id", "version", unique=True),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    plan_id: Mapped[UUID] = mapped_column()
    version: Mapped[int] = mapped_column(Integer)
    seat_limit: Mapped[int] = mapped_column(Integer)
    price_30d_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_year_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(Text, server_default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class AccountSubscription(Base):
    __tablename__: str = "account_subscriptions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"], ["nightingale.accounts.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["plan_version_id"],
            ["nightingale.subscription_plan_versions.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint(
            "status IN ('pending_activation','active','grace','suspended','cancelled')",
            name="status",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint("isfinite(updated_at) AND updated_at >= created_at", name="updated_at_finite"),
        CheckConstraint("version > 0", name="version"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column(unique=True)
    plan_version_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(Text, server_default="pending_activation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class SubscriptionPeriod(Base):
    __tablename__: str = "subscription_periods"
    __table_args__ = (
        ForeignKeyConstraint(
            ["subscription_id"],
            ["nightingale.account_subscriptions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["plan_version_id"],
            ["nightingale.subscription_plan_versions.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("periodicity IN ('days_30','year_1')", name="periodicity"),
        CheckConstraint("isfinite(starts_at)", name="starts_at_finite"),
        CheckConstraint("isfinite(ends_at) AND ends_at > starts_at", name="ends_at_finite"),
        CheckConstraint("sequence > 0", name="sequence"),
        ForeignKeyConstraint(
            ["origin_review_id"],
            ["nightingale.subscription_reviews.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "uq_subscription_periods_origin_review",
            "origin_review_id",
            unique=True,
        ),
        Index(
            "uq_subscription_periods_sequence",
            "subscription_id",
            "sequence",
            unique=True,
        ),
        # Overlap exclusion lives only in the migration (EXCLUDE USING gist);
        # SQLAlchemy has no portable construct for it.
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    subscription_id: Mapped[UUID] = mapped_column()
    plan_version_id: Mapped[UUID] = mapped_column()
    periodicity: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sequence: Mapped[int] = mapped_column(Integer)
    origin_review_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class PlatformOperator(Base):
    __tablename__: str = "platform_operators"
    __table_args__ = (
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("btrim(display_name)<>''", name="display_name"),
        CheckConstraint(
            "cardinality(actions) > 0 AND "
            "actions <@ ARRAY['review','catalog','rates','operators']::text[]",
            name="actions",
        ),
        CheckConstraint("status IN ('active','revoked')", name="status"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint("isfinite(updated_at) AND updated_at >= created_at", name="updated_at_finite"),
        CheckConstraint("version > 0", name="version"),
        Index("uq_platform_operators_oidc", "oidc_issuer", "oidc_subject", unique=True),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    oidc_issuer: Mapped[str] = mapped_column(Text)
    oidc_subject: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    actions: Mapped[list[str]] = mapped_column(ARRAY(Text))
    status: Mapped[str] = mapped_column(Text, server_default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class PlatformOperatorCredential(Base):
    __tablename__: str = "platform_operator_credentials"
    __table_args__ = (
        ForeignKeyConstraint(
            ["operator_id"], ["nightingale.platform_operators.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="token_hash"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint("revoked_at IS NULL OR isfinite(revoked_at)", name="revoked_at_finite"),
        Index("ix_platform_operator_credentials_operator", "operator_id"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    operator_id: Mapped[UUID] = mapped_column()
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BcvExchangeRate(Base):
    __tablename__: str = "bcv_exchange_rates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["registered_by"], ["nightingale.platform_operators.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("isfinite(rate_date)", name="rate_date_finite"),
        CheckConstraint("rate_ves_per_usd > 0", name="rate"),
        CheckConstraint("btrim(source)<>''", name="source"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    rate_date: Mapped[date] = mapped_column(Date, unique=True)
    rate_ves_per_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    source: Mapped[str] = mapped_column(Text)
    registered_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class PaymentReport(Base):
    __tablename__: str = "payment_reports"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"], ["nightingale.accounts.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["subscription_id", "account_id"],
            [
                "nightingale.account_subscriptions.id",
                "nightingale.account_subscriptions.account_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["plan_version_id"],
            ["nightingale.subscription_plan_versions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["previous_report_id"], ["nightingale.payment_reports.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["submitted_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("periodicity IN ('days_30','year_1')", name="periodicity"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="status"),
        CheckConstraint("isfinite(declared_paid_on)", name="paid_on_finite"),
        CheckConstraint("declared_amount > 0", name="amount"),
        CheckConstraint("declared_currency IN ('VES','USD')", name="currency"),
        CheckConstraint("btrim(declared_method)<>''", name="method"),
        CheckConstraint(
            "declared_reference_last4 IS NULL OR declared_reference_last4 ~ '^[0-9]{4}$'",
            name="reference_last4",
        ),
        CheckConstraint("declared_note IS NULL OR btrim(declared_note)<>''", name="note"),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        CheckConstraint("isfinite(updated_at) AND updated_at >= created_at", name="updated_at_finite"),
        CheckConstraint("version > 0", name="version"),
        Index("ix_payment_reports_account", "account_id", "created_at"),
        Index("ix_payment_reports_status", "status", "created_at"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column()
    subscription_id: Mapped[UUID] = mapped_column()
    plan_version_id: Mapped[UUID] = mapped_column()
    periodicity: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="pending")
    declared_paid_on: Mapped[date] = mapped_column(Date)
    declared_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    declared_currency: Mapped[str] = mapped_column(Text)
    declared_method: Mapped[str] = mapped_column(Text)
    declared_reference_last4: Mapped[str | None] = mapped_column(Text)
    declared_note: Mapped[str | None] = mapped_column(Text)
    previous_report_id: Mapped[UUID | None] = mapped_column()
    submitted_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class PaymentReportEvidence(Base):
    __tablename__: str = "payment_report_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["report_id"], ["nightingale.payment_reports.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["uploaded_by"], ["nightingale.app_users.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
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
    uploaded_by: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


class SubscriptionReview(Base):
    __tablename__: str = "subscription_reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["report_id"], ["nightingale.payment_reports.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["operator_id"], ["nightingale.platform_operators.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["bcv_rate_id"], ["nightingale.bcv_exchange_rates.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("decision IN ('approved','rejected')", name="decision"),
        CheckConstraint(
            "verified_paid_on IS NULL OR isfinite(verified_paid_on)", name="paid_on_finite"
        ),
        CheckConstraint("verified_amount IS NULL OR verified_amount > 0", name="amount"),
        CheckConstraint(
            "verified_currency IS NULL OR verified_currency IN ('VES','USD')",
            name="currency",
        ),
        CheckConstraint("reason IS NULL OR btrim(reason)<>''", name="reason"),
        CheckConstraint(
            "(decision='approved' AND verified_paid_on IS NOT NULL "
            "AND verified_amount IS NOT NULL AND verified_currency IS NOT NULL) "
            "OR (decision='rejected' AND reason IS NOT NULL)",
            name="coherence",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    report_id: Mapped[UUID] = mapped_column(unique=True)
    operator_id: Mapped[UUID] = mapped_column()
    decision: Mapped[str] = mapped_column(Text)
    verified_paid_on: Mapped[date | None] = mapped_column(Date)
    verified_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    verified_currency: Mapped[str | None] = mapped_column(Text)
    bcv_rate_id: Mapped[UUID | None] = mapped_column()
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
