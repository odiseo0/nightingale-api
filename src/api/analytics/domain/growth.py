from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field

from src.api.analytics.domain.references import (
    FIXTURE_LMS_ROWS,
    INDICATOR_RANGES,
    Indicator,
    LmsRow,
    ReferenceCode,
    Sex,
)
from src.core.schema import BaseModel


class GrowthInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_code: ReferenceCode
    indicator: Indicator
    sex: Sex
    age_months: int = Field(ge=0)
    value: Decimal = Field(gt=0)


class GrowthResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_code: ReferenceCode
    indicator: Indicator
    sex: Sex
    age_months: int
    z_score: Decimal
    reference_version: str


class GrowthLimit(BaseModel):
    """La referencia no aplica: se conserva la medición y se explica el límite."""

    model_config = ConfigDict(extra="forbid")

    indicator: Indicator
    age_months: int
    limit_explanation: str


def _nearest_row(input: GrowthInput) -> LmsRow | None:
    rows = [
        row
        for row in FIXTURE_LMS_ROWS
        if row.reference_code == input.reference_code
        and row.indicator == input.indicator
        and row.sex == input.sex
    ]
    for row in rows:
        if row.age_months == input.age_months:
            return row
    return None


def z_score_from_lms(value: Decimal, row: LmsRow) -> Decimal:
    ratio = value / row.mu
    if row.lambda_ == 0:
        return Decimal(str(float(ratio).ln())) / row.sigma
    power = float(ratio) ** float(row.lambda_)
    return Decimal(str((power - 1) / float(row.lambda_))) / row.sigma


def compute_growth(input: GrowthInput) -> GrowthResult | GrowthLimit:
    bounds = INDICATOR_RANGES.get((input.reference_code, input.indicator))
    if bounds is None:
        return GrowthLimit(
            indicator=input.indicator,
            age_months=input.age_months,
            limit_explanation="La referencia no publica este indicador.",
        )

    low, high = bounds
    if not low <= input.age_months <= high:
        return GrowthLimit(
            indicator=input.indicator,
            age_months=input.age_months,
            limit_explanation=(
                f"Edad fuera del rango publicado ({low}–{high} meses) "
                f"para {input.indicator} en {input.reference_code}; no se extrapola."
            ),
        )

    row = _nearest_row(input)
    if row is None:
        return GrowthLimit(
            indicator=input.indicator,
            age_months=input.age_months,
            limit_explanation="Los parámetros LMS verificados no cubren este mes; la tabla completa de la OMS queda pendiente de incorporación.",
        )

    return GrowthResult(
        reference_code=input.reference_code,
        indicator=input.indicator,
        sex=input.sex,
        age_months=input.age_months,
        z_score=z_score_from_lms(input.value, row),
        reference_version="who2006-lms-fixture-20261118",
    )


__all__ = [
    "GrowthInput",
    "GrowthLimit",
    "GrowthResult",
    "compute_growth",
    "z_score_from_lms",
]
