from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class VademecumDataset(Base):
    __tablename__: str = "vademecum_datasets"
    __table_args__ = (
        CheckConstraint(
            "substring(id::text from 15 for 1)='7' AND "
            "substring(id::text from 20 for 1) IN ('8','9','a','b')",
            name="uuidv7",
        ),
        CheckConstraint("source_sha256 ~ '^[0-9a-f]{64}$'", name="source_sha256"),
        CheckConstraint("schema_version='1.0.0'", name="schema_version"),
        CheckConstraint("isfinite(registry_cutoff_date)", name="cutoff_finite"),
        CheckConstraint("btrim(medical_notice)<>''", name="medical_notice"),
        CheckConstraint("isfinite(imported_at)", name="imported_at_finite"),
        Index(
            "uq_vademecum_datasets_active",
            "active",
            unique=True,
            postgresql_where=text("active"),
        ),
        {"schema": "nightingale"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_sha256: Mapped[str] = mapped_column(Text, unique=True)
    schema_version: Mapped[str] = mapped_column(Text)
    registry_cutoff_date: Mapped[date] = mapped_column(Date)
    medical_notice: Mapped[str] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default="false")


class VademecumProduct(Base):
    __tablename__: str = "vademecum_products"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dataset_id"], ["nightingale.vademecum_datasets.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("btrim(registration_number)<>''", name="registration_number"),
        CheckConstraint("btrim(name)<>''", name="name"),
        CheckConstraint("isfinite(approved_at)", name="approved_at_finite"),
        CheckConstraint("isfinite(valid_until)", name="valid_until_finite"),
        CheckConstraint("btrim(representative)<>''", name="representative"),
        CheckConstraint(
            "manufacturer IS NULL OR btrim(manufacturer)<>''", name="manufacturer"
        ),
        CheckConstraint(
            "ingredient_link_status IN ('complete','unlinked','missing_ingredient',"
            "'historical_complete','product_reference','inferred_complete',"
            "'combination_only','historical_partial','inferred_partial','partial')",
            name="ingredient_link_status",
        ),
        CheckConstraint(
            "ingredient_resolution IN ('source_text','historical_product_match',"
            "'unresolved','product_name_inference','product_reference')",
            name="ingredient_resolution",
        ),
        CheckConstraint(
            "product_reference IS NULL OR jsonb_typeof(product_reference)='object'",
            name="product_reference_object",
        ),
        Index(
            "ix_vademecum_products_order",
            "dataset_id",
            "name",
            "registration_number",
        ),
        {"schema": "nightingale"},
    )

    dataset_id: Mapped[UUID] = mapped_column(primary_key=True)
    registration_number: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    active_ingredient_text: Mapped[str] = mapped_column(Text)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    representative: Mapped[str] = mapped_column(Text)
    manufacturer: Mapped[str | None] = mapped_column(Text)
    ingredient_link_status: Mapped[str] = mapped_column(Text)
    ingredient_resolution: Mapped[str] = mapped_column(Text)
    product_reference: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    search_text: Mapped[str] = mapped_column(Text)


class VademecumProductIngredient(Base):
    __tablename__: str = "vademecum_product_ingredients"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dataset_id", "registration_number"],
            [
                "nightingale.vademecum_products.dataset_id",
                "nightingale.vademecum_products.registration_number",
            ],
            ondelete="RESTRICT",
        ),
        CheckConstraint("btrim(ingredient_id)<>''", name="ingredient_id"),
        Index(
            "ix_vademecum_product_ingredients_inverse",
            "dataset_id",
            "ingredient_id",
            "registration_number",
        ),
        {"schema": "nightingale"},
    )

    dataset_id: Mapped[UUID] = mapped_column(primary_key=True)
    registration_number: Mapped[str] = mapped_column(Text, primary_key=True)
    ingredient_id: Mapped[str] = mapped_column(Text, primary_key=True)


class VademecumMonograph(Base):
    __tablename__: str = "vademecum_monographs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dataset_id"], ["nightingale.vademecum_datasets.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="monograph_id"),
        CheckConstraint("btrim(name)<>''", name="name"),
        CheckConstraint("jsonb_typeof(document)='object'", name="document_object"),
        Index("ix_vademecum_monographs_order", "dataset_id", "name", "id"),
        {"schema": "nightingale"},
    )

    dataset_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    atc_code: Mapped[str] = mapped_column(Text)
    document: Mapped[dict[str, object]] = mapped_column(JSONB)
    search_text: Mapped[str] = mapped_column(Text)


class VademecumProductMonograph(Base):
    __tablename__: str = "vademecum_product_monographs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dataset_id", "registration_number"],
            [
                "nightingale.vademecum_products.dataset_id",
                "nightingale.vademecum_products.registration_number",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["dataset_id", "monograph_id"],
            [
                "nightingale.vademecum_monographs.dataset_id",
                "nightingale.vademecum_monographs.id",
            ],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_vademecum_product_monographs_inverse",
            "dataset_id",
            "monograph_id",
            "registration_number",
        ),
        {"schema": "nightingale"},
    )

    dataset_id: Mapped[UUID] = mapped_column(primary_key=True)
    registration_number: Mapped[str] = mapped_column(Text, primary_key=True)
    monograph_id: Mapped[str] = mapped_column(Text, primary_key=True)
    combination: Mapped[bool] = mapped_column(Boolean)
