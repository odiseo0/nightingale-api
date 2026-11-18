from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class AnalyticMeasurementPoint(Base):
    __tablename__ = "measurement_points"
    __table_args__ = {"schema": "analytics"}

    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    measurement_kind: Mapped[str] = mapped_column(Text, primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(primary_key=True)
    source_measurement_id: Mapped[UUID] = mapped_column(primary_key=True)
    source_version: Mapped[int]
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    systolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    diastolic_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str] = mapped_column(Text)
    change_seq: Mapped[int] = mapped_column(BigInteger)


class AnalyticEtlState(Base):
    __tablename__ = "etl_state"
    __table_args__ = {"schema": "analytics"}

    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    last_change_seq: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime]
