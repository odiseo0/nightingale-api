from pydantic import ConfigDict

from src.api.analytics.domain.series import SeriesSelection
from src.core.schema import BaseModel


class DerivedInputs(BaseModel):
    """Qué entradas/versiones producen una proyección; invalidar una entrada
    exige recalcular los derivados que la citan."""

    model_config = ConfigDict(extra="forbid")

    selections: list[SeriesSelection]
    birth_date_changed: bool = False

    @property
    def invalidated(self) -> bool:
        return self.birth_date_changed or any(
            point.source_version > 1 for selection in self.selections for point in selection.points
        )


__all__ = ["DerivedInputs"]
