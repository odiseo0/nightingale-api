from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict

from src.api.analytics.domain.series import MeasurementKind, SeriesPoint
from src.core.schema import BaseModel, PageQuery


class SeriesQuery(PageQuery):
    model_config = ConfigDict(extra="forbid")

    kind: MeasurementKind


class SeriesPointResponse(SeriesPoint):
    pass


class SeriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str
    measurement_kind: MeasurementKind
    points: list[SeriesPointResponse]


__all__ = ["SeriesPointResponse", "SeriesQuery", "SeriesResponse"]
