from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.billing.repository.models import (
    BillingExchangeRate,
    BillingReview,
    ChargeHistory,
    PatientBillingGrant,
    PatientCharge,
    PatientPayment,
    PatientPaymentEvidence,
    PatientPaymentReport,
    PaymentReceipt,
)
from src.core.db import DAO
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, EmptyType, datetime_now


class PatientChargeDAO(DAO[PatientCharge, BaseModel, BaseModel]):
    async def by_id_in_account(
        self, db: AsyncSession, charge_id: UUID, account_id: UUID
    ) -> PatientCharge | EmptyType:
        row = await db.scalar(
            select(PatientCharge).where(
                PatientCharge.id == charge_id,
                PatientCharge.account_id == account_id,
            )
        )

        return Empty if row is None else row

    async def by_id_for_update(
        self, db: AsyncSession, charge_id: UUID, account_id: UUID
    ) -> PatientCharge | EmptyType:
        """Row lock that serializes balance effects on the same charge (§19.6)."""
        row = await db.scalar(
            select(PatientCharge)
            .where(
                PatientCharge.id == charge_id,
                PatientCharge.account_id == account_id,
            )
            .with_for_update()
        )

        return Empty if row is None else row

    async def insert_charge(self, db: AsyncSession, charge: dict) -> None:
        await self.create(db, commit=False, obj_in=charge)

    async def apply_update(
        self,
        db: AsyncSession,
        charge_id: UUID,
        account_id: UUID,
        expected_version: int,
        changes: dict,
    ) -> bool:
        """Optimistic update; False when another writer won the version."""
        result = await db.execute(
            update(PatientCharge)
            .where(
                PatientCharge.id == charge_id,
                PatientCharge.account_id == account_id,
                PatientCharge.version == expected_version,
            )
            .values(**changes, version=expected_version + 1, updated_at=datetime_now())
        )

        return result.rowcount == 1

    async def page_list(
        self,
        db: AsyncSession,
        account_id: UUID,
        page: int,
        shows: int,
        patient_id: UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[PatientCharge], int]:
        filters = [PatientCharge.account_id == account_id]
        if patient_id is not None:
            filters.append(PatientCharge.patient_id == patient_id)
        if status is not None:
            filters.append(PatientCharge.status == status)

        total = await db.scalar(
            select(func.count()).select_from(PatientCharge).where(*filters)
        )
        rows = await db.scalars(
            select(PatientCharge)
            .where(*filters)
            .order_by(PatientCharge.created_at.desc(), PatientCharge.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total or 0

    async def page_by_patient(
        self,
        db: AsyncSession,
        account_id: UUID,
        patient_id: UUID,
        page: int,
        shows: int,
        status: str | None = None,
    ) -> tuple[list[PatientCharge], int]:
        filters = [
            PatientCharge.account_id == account_id,
            PatientCharge.patient_id == patient_id,
        ]
        if status is not None:
            filters.append(PatientCharge.status == status)

        total = await db.scalar(
            select(func.count()).select_from(PatientCharge).where(*filters)
        )
        rows = await db.scalars(
            select(PatientCharge)
            .where(*filters)
            .order_by(PatientCharge.created_at.desc(), PatientCharge.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total or 0


class ChargeHistoryDAO(DAO[ChargeHistory, BaseModel, BaseModel]):
    async def insert_entry(
        self,
        db: AsyncSession,
        entry_id: UUID,
        charge_id: UUID,
        account_id: UUID,
        action: str,
        charge_version: int,
        actor_id: UUID,
        reason: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        obj_in = {
            "id": entry_id,
            "charge_id": charge_id,
            "account_id": account_id,
            "action": action,
            "charge_version": charge_version,
            "actor_id": actor_id,
            "reason": reason,
        }
        if created_at is not None:
            obj_in["created_at"] = created_at

        await self.create(db, commit=False, obj_in=obj_in)

    async def page_account(
        self, db: AsyncSession, account_id: UUID, limit: int = 500
    ) -> list[PatientPayment]:
        rows = await db.scalars(
            select(PatientPayment)
            .where(PatientPayment.account_id == account_id)
            .order_by(PatientPayment.created_at, PatientPayment.id)
            .limit(limit)
        )

        return list(rows)

    async def of_charge(
        self, db: AsyncSession, charge_id: UUID, account_id: UUID
    ) -> list[ChargeHistory]:
        rows = await db.scalars(
            select(ChargeHistory)
            .where(
                ChargeHistory.charge_id == charge_id,
                ChargeHistory.account_id == account_id,
            )
            .order_by(ChargeHistory.created_at, ChargeHistory.id)
        )

        return list(rows)


class BillingExchangeRateDAO(DAO[BillingExchangeRate, BaseModel, BaseModel]):
    async def by_date(
        self, db: AsyncSession, account_id: UUID, rate_date: date
    ) -> BillingExchangeRate | EmptyType:
        row = await db.scalar(
            select(BillingExchangeRate).where(
                BillingExchangeRate.account_id == account_id,
                BillingExchangeRate.rate_date == rate_date,
            )
        )

        return Empty if row is None else row

    async def applicable(
        self, db: AsyncSession, account_id: UUID, paid_on: date
    ) -> BillingExchangeRate | EmptyType:
        """Rate of the verified payment date or the most recent one before it (D22/D25)."""
        row = await db.scalar(
            select(BillingExchangeRate)
            .where(
                BillingExchangeRate.account_id == account_id,
                BillingExchangeRate.rate_date <= paid_on,
            )
            .order_by(BillingExchangeRate.rate_date.desc())
            .limit(1)
        )

        return Empty if row is None else row

    async def insert_rate(
        self,
        db: AsyncSession,
        rate_id: UUID,
        account_id: UUID,
        rate_date: date,
        rate_ves_per_usd: Decimal,
        source: str,
        registered_by: UUID,
    ) -> None:
        await self.create(
            db,
            commit=False,
            obj_in={
                "id": rate_id,
                "account_id": account_id,
                "rate_date": rate_date,
                "rate_ves_per_usd": rate_ves_per_usd,
                "source": source,
                "registered_by": registered_by,
            },
        )

    async def page_rates(
        self, db: AsyncSession, account_id: UUID, page: int, shows: int
    ) -> tuple[list[BillingExchangeRate], int]:
        total = await db.scalar(
            select(func.count())
            .select_from(BillingExchangeRate)
            .where(BillingExchangeRate.account_id == account_id)
        )
        rows = await db.scalars(
            select(BillingExchangeRate)
            .where(BillingExchangeRate.account_id == account_id)
            .order_by(BillingExchangeRate.rate_date.desc())
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total or 0


class PatientBillingGrantDAO(DAO[PatientBillingGrant, BaseModel, BaseModel]):
    async def by_token_hash(
        self, db: AsyncSession, token_hash: str
    ) -> PatientBillingGrant | EmptyType:
        row = await db.scalar(
            select(PatientBillingGrant).where(
                PatientBillingGrant.token_hash == token_hash
            )
        )

        return Empty if row is None else row

    async def insert_grant(self, db: AsyncSession, grant: dict) -> None:
        await self.create(db, commit=False, obj_in=grant)

    async def revoke(
        self, db: AsyncSession, grant_id: UUID, account_id: UUID, revoked_at: datetime
    ) -> bool:
        result = await db.execute(
            update(PatientBillingGrant)
            .where(
                PatientBillingGrant.id == grant_id,
                PatientBillingGrant.account_id == account_id,
                PatientBillingGrant.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

        return result.rowcount == 1

    async def revoke_by_appointment(
        self,
        db: AsyncSession,
        appointment_id: UUID,
        account_id: UUID,
        revoked_at: datetime,
    ) -> int:
        """Cancelling the appointment revokes its anchored grants (D28)."""
        result = await db.execute(
            update(PatientBillingGrant)
            .where(
                PatientBillingGrant.appointment_id == appointment_id,
                PatientBillingGrant.account_id == account_id,
                PatientBillingGrant.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

        return result.rowcount

    async def page_grants(
        self,
        db: AsyncSession,
        account_id: UUID,
        page: int,
        shows: int,
        patient_id: UUID | None = None,
        charge_id: UUID | None = None,
    ) -> tuple[list[PatientBillingGrant], int]:
        filters = [PatientBillingGrant.account_id == account_id]
        if patient_id is not None:
            filters.append(PatientBillingGrant.patient_id == patient_id)
        if charge_id is not None:
            filters.append(PatientBillingGrant.charge_id == charge_id)

        total = await db.scalar(
            select(func.count()).select_from(PatientBillingGrant).where(*filters)
        )
        rows = await db.scalars(
            select(PatientBillingGrant)
            .where(*filters)
            .order_by(PatientBillingGrant.created_at.desc(), PatientBillingGrant.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total or 0


class PatientPaymentReportDAO(DAO[PatientPaymentReport, BaseModel, BaseModel]):
    async def by_id_in_account(
        self, db: AsyncSession, report_id: UUID, account_id: UUID
    ) -> PatientPaymentReport | EmptyType:
        row = await db.scalar(
            select(PatientPaymentReport).where(
                PatientPaymentReport.id == report_id,
                PatientPaymentReport.account_id == account_id,
            )
        )

        return Empty if row is None else row

    async def by_id_for_update(
        self, db: AsyncSession, report_id: UUID, account_id: UUID
    ) -> PatientPaymentReport | EmptyType:
        """Row lock that serializes concurrent reviewers of the same report (§20.7)."""
        row = await db.scalar(
            select(PatientPaymentReport)
            .where(
                PatientPaymentReport.id == report_id,
                PatientPaymentReport.account_id == account_id,
            )
            .with_for_update()
        )

        return Empty if row is None else row

    async def insert_report(self, db: AsyncSession, report: dict) -> None:
        await self.create(db, commit=False, obj_in=report)

    async def apply_status(
        self,
        db: AsyncSession,
        report_id: UUID,
        account_id: UUID,
        expected_version: int,
        status: str,
    ) -> bool:
        result = await db.execute(
            update(PatientPaymentReport)
            .where(
                PatientPaymentReport.id == report_id,
                PatientPaymentReport.account_id == account_id,
                PatientPaymentReport.version == expected_version,
                PatientPaymentReport.status == "pending",
            )
            .values(
                status=status, version=expected_version + 1, updated_at=datetime_now()
            )
        )

        return result.rowcount == 1

    async def page_inbox(
        self,
        db: AsyncSession,
        account_id: UUID,
        page: int,
        shows: int,
        status: str | None = None,
        charge_id: UUID | None = None,
        patient_id: UUID | None = None,
    ) -> tuple[list[PatientPaymentReport], int]:
        filters = [PatientPaymentReport.account_id == account_id]
        if status is not None:
            filters.append(PatientPaymentReport.status == status)
        if charge_id is not None:
            filters.append(PatientPaymentReport.charge_id == charge_id)
        if patient_id is not None:
            filters.append(PatientPaymentReport.patient_id == patient_id)

        total = await db.scalar(
            select(func.count()).select_from(PatientPaymentReport).where(*filters)
        )
        rows = await db.scalars(
            select(PatientPaymentReport)
            .where(*filters)
            .order_by(PatientPaymentReport.created_at, PatientPaymentReport.id)
            .offset((page - 1) * shows)
            .limit(shows)
        )

        return list(rows), total or 0

    async def chain_of(
        self, db: AsyncSession, report_id: UUID, account_id: UUID
    ) -> list[PatientPaymentReport]:
        """Resubmissions linked to a decided report, oldest first (§10.4)."""
        rows = await db.scalars(
            select(PatientPaymentReport)
            .where(
                PatientPaymentReport.previous_report_id == report_id,
                PatientPaymentReport.account_id == account_id,
            )
            .order_by(PatientPaymentReport.created_at, PatientPaymentReport.id)
        )

        return list(rows)


class PatientPaymentEvidenceDAO(DAO[PatientPaymentEvidence, BaseModel, BaseModel]):
    async def by_report(
        self, db: AsyncSession, report_id: UUID
    ) -> PatientPaymentEvidence | EmptyType:
        row = await db.scalar(
            select(PatientPaymentEvidence).where(
                PatientPaymentEvidence.report_id == report_id
            )
        )

        return Empty if row is None else row

    async def insert_evidence(self, db: AsyncSession, evidence: dict) -> None:
        await self.create(db, commit=False, obj_in=evidence)


class BillingReviewDAO(DAO[BillingReview, BaseModel, BaseModel]):
    async def by_report(
        self, db: AsyncSession, report_id: UUID
    ) -> BillingReview | EmptyType:
        row = await db.scalar(
            select(BillingReview).where(BillingReview.report_id == report_id)
        )

        return Empty if row is None else row

    async def insert_review(self, db: AsyncSession, review: dict) -> None:
        await self.create(db, commit=False, obj_in=review)


class PatientPaymentDAO(DAO[PatientPayment, BaseModel, BaseModel]):
    async def by_id_in_account(
        self, db: AsyncSession, payment_id: UUID, account_id: UUID
    ) -> PatientPayment | EmptyType:
        row = await db.scalar(
            select(PatientPayment).where(
                PatientPayment.id == payment_id,
                PatientPayment.account_id == account_id,
            )
        )

        return Empty if row is None else row

    async def insert_payment(self, db: AsyncSession, payment: dict) -> None:
        await self.create(db, commit=False, obj_in=payment)

    async def active_amounts_of(
        self, db: AsyncSession, charge_id: UUID, account_id: UUID
    ) -> list[Decimal]:
        """Active applied amounts; annulled payments stop summing (§13.5)."""
        rows = await db.scalars(
            select(PatientPayment.amount).where(
                PatientPayment.charge_id == charge_id,
                PatientPayment.account_id == account_id,
                PatientPayment.status == "active",
            )
        )

        return list(rows)

    async def annul(
        self,
        db: AsyncSession,
        payment_id: UUID,
        account_id: UUID,
        expected_version: int,
        annulled_at: datetime,
        annulled_by: UUID,
        reason: str,
    ) -> bool:
        result = await db.execute(
            update(PatientPayment)
            .where(
                PatientPayment.id == payment_id,
                PatientPayment.account_id == account_id,
                PatientPayment.version == expected_version,
                PatientPayment.status == "active",
            )
            .values(
                status="annulled",
                annulled_at=annulled_at,
                annulled_by=annulled_by,
                annulment_reason=reason,
                version=expected_version + 1,
                updated_at=datetime_now(),
            )
        )

        return result.rowcount == 1

    async def page_account(
        self, db: AsyncSession, account_id: UUID, limit: int = 500
    ) -> list[PatientPayment]:
        rows = await db.scalars(
            select(PatientPayment)
            .where(PatientPayment.account_id == account_id)
            .order_by(PatientPayment.created_at, PatientPayment.id)
            .limit(limit)
        )

        return list(rows)

    async def of_charge(
        self, db: AsyncSession, charge_id: UUID, account_id: UUID
    ) -> list[PatientPayment]:
        rows = await db.scalars(
            select(PatientPayment)
            .where(
                PatientPayment.charge_id == charge_id,
                PatientPayment.account_id == account_id,
            )
            .order_by(PatientPayment.created_at, PatientPayment.id)
        )

        return list(rows)


class PaymentReceiptDAO(DAO[PaymentReceipt, BaseModel, BaseModel]):
    async def by_payment(
        self, db: AsyncSession, payment_id: UUID
    ) -> PaymentReceipt | EmptyType:
        row = await db.scalar(
            select(PaymentReceipt).where(PaymentReceipt.payment_id == payment_id)
        )

        return Empty if row is None else row

    async def insert_receipt(self, db: AsyncSession, receipt: dict) -> None:
        await self.create(db, commit=False, obj_in=receipt)


dao_charges = PatientChargeDAO(PatientCharge)
dao_charge_histories = ChargeHistoryDAO(ChargeHistory)
dao_exchange_rates = BillingExchangeRateDAO(BillingExchangeRate)
dao_grants = PatientBillingGrantDAO(PatientBillingGrant)
dao_reports = PatientPaymentReportDAO(PatientPaymentReport)
dao_evidence = PatientPaymentEvidenceDAO(PatientPaymentEvidence)
dao_reviews = BillingReviewDAO(BillingReview)
dao_payments = PatientPaymentDAO(PatientPayment)
dao_receipts = PaymentReceiptDAO(PaymentReceipt)


class BillingMetricsDAO(DAO[PatientCharge, BaseModel, BaseModel]):
    async def panel(
        self, db: AsyncSession, account_id: UUID, since: datetime, until: datetime
    ) -> dict:
        """Bounded aggregates of the D28 panel; every total declares its currency
        and never revalues history."""
        charged = await db.execute(
            select(
                PatientCharge.currency, func.coalesce(func.sum(PatientCharge.amount), 0)
            )
            .where(
                PatientCharge.account_id == account_id,
                PatientCharge.status.in_(("issued", "cancelled")),
                PatientCharge.issued_at >= since,
                PatientCharge.issued_at < until,
            )
            .group_by(PatientCharge.currency)
        )
        collected = await db.execute(
            select(
                PatientPayment.currency,
                func.coalesce(func.sum(PatientPayment.amount), 0),
            )
            .where(
                PatientPayment.account_id == account_id,
                PatientPayment.status == "active",
                PatientPayment.created_at >= since,
                PatientPayment.created_at < until,
            )
            .group_by(PatientPayment.currency)
        )
        annulments = await db.execute(
            select(
                PatientPayment.currency,
                func.coalesce(func.sum(PatientPayment.amount), 0),
            )
            .where(
                PatientPayment.account_id == account_id,
                PatientPayment.status == "annulled",
                PatientPayment.annulled_at >= since,
                PatientPayment.annulled_at < until,
            )
            .group_by(PatientPayment.currency)
        )
        charged_rows = charged.all()
        collected_rows = collected.all()
        annulment_rows = annulments.all()
        pending = await db.scalar(
            select(func.count())
            .select_from(PatientPaymentReport)
            .where(
                PatientPaymentReport.account_id == account_id,
                PatientPaymentReport.status == "pending",
            )
        )
        balances = await db.execute(
            select(
                PatientCharge.id,
                PatientCharge.amount,
                func.coalesce(func.sum(PatientPayment.amount), 0),
            )
            .outerjoin(
                PatientPayment,
                (PatientPayment.charge_id == PatientCharge.id)
                & (PatientPayment.status == "active"),
            )
            .where(
                PatientCharge.account_id == account_id,
                PatientCharge.status == "issued",
                PatientCharge.issued_at >= since,
                PatientCharge.issued_at < until,
            )
            .group_by(PatientCharge.id)
        )
        partially_paid = paid_charges = 0
        outstanding: dict[str, Decimal] = {}

        for _, total, paid in balances:
            if paid == 0:
                state = "unpaid"
            elif paid >= total:
                state = "paid"
            else:
                state = "partially_paid"
            if state == "partially_paid":
                partially_paid += 1
            if state == "paid":
                paid_charges += 1

        issued_totals = await db.execute(
            select(
                PatientCharge.currency, func.coalesce(func.sum(PatientCharge.amount), 0)
            )
            .where(
                PatientCharge.account_id == account_id,
                PatientCharge.status == "issued",
                PatientCharge.issued_at >= since,
                PatientCharge.issued_at < until,
            )
            .group_by(PatientCharge.currency)
        )

        for currency, amount in issued_totals.all():
            outstanding[currency] = amount

        for currency, amount in collected_rows:
            outstanding[currency] = outstanding.get(currency, Decimal(0)) - amount

        return {
            "charged": {row[0]: row[1] for row in charged_rows},
            "collected": {row[0]: row[1] for row in collected_rows},
            "annulments": {row[0]: row[1] for row in annulment_rows},
            "pending_review": pending or 0,
            "partially_paid": partially_paid,
            "paid_charges": paid_charges,
            "outstanding": outstanding,
        }


dao_metrics = BillingMetricsDAO(PatientCharge)
