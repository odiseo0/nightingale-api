"""WHO growth reference fixtures verified against official WHO tables.

Source: WHO Child Growth Standards, weight-for-age boys 0-5 years (z-scores),
https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/wfa-boys-0-5-zscores.pdf
LMS rows: month 0 (0.3487, 3.3464, 0.14602), month 5 (0.1395, 7.5105, 0.11080).
Simplified field table medians: 3.3 kg at month 0, 4.5 kg at month 1
(https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/sft-wfa-boys-z-0-5.pdf).
Full WHO grid import is a recorded limit until the dataset is downloaded and hashed.
"""

from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field

from src.core.schema import BaseModel

ReferenceCode = Literal["who2006", "who2007"]
Sex = Literal["male", "female"]
Indicator = Literal[
    "weight_for_age", "length_height_for_age", "weight_for_length", "bmi_for_age"
]
Metric = Literal["median", "sd", "z_scores", "percentiles"]


class LmsRow(BaseModel):
    reference_code: ReferenceCode
    indicator: Indicator
    sex: Sex
    age_months: int = Field(ge=0)
    lambda_: Decimal
    mu: Decimal
    sigma: Decimal

    model_config = ConfigDict(extra="forbid")


class ReferenceValue(BaseModel):
    reference_code: ReferenceCode
    indicator: Indicator
    sex: Sex
    age_days: int = Field(ge=0)
    metric: Metric
    value: Decimal

    model_config = ConfigDict(extra="forbid")


FIXTURE_LMS_ROWS: list[LmsRow] = [
    LmsRow(
        reference_code="who2006",
        indicator="weight_for_age",
        sex="male",
        age_months=0,
        lambda_=Decimal("0.3487"),
        mu=Decimal("3.3464"),
        sigma=Decimal("0.14602"),
    ),
    LmsRow(
        reference_code="who2006",
        indicator="weight_for_age",
        sex="male",
        age_months=5,
        lambda_=Decimal("0.1395"),
        mu=Decimal("7.5105"),
        sigma=Decimal("0.11080"),
    ),
]

INDICATOR_RANGES: dict[tuple[ReferenceCode, Indicator], tuple[int, int]] = {
    ("who2006", "weight_for_age"): (0, 60),
    ("who2006", "length_height_for_age"): (0, 60),
    ("who2006", "weight_for_length"): (45, 110),
    ("who2006", "bmi_for_age"): (0, 60),
    ("who2007", "length_height_for_age"): (61, 228),
    ("who2007", "bmi_for_age"): (61, 228),
    ("who2007", "weight_for_age"): (61, 120),
}
