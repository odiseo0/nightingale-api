from pydantic import ConfigDict

from src.api.analytics.domain.series import SeriesSelection
from src.core.schema import BaseModel


class DerivedInputs(BaseModel):
    selections: list[SeriesSelection]
    birth_date_changed: bool = False

    model_config = ConfigDict(extra="forbid")

    @property
    def invalidated(self) -> bool:
        return self.birth_date_changed or any(
            point.source_version > 1
            for selection in self.selections
            for point in selection.points
        )
