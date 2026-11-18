import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid7

from src.api.analytics.domain.dependencies import DerivedInputs
from src.api.analytics.domain.series import (
    SeriesEntry,
    SeriesSelection,
    age_on,
    select_valid_series,
)


def entry(value: str, measured: date, version: int = 1, status: str = "valid", kind: str = "weight"):
    return SeriesEntry(
        measurement_id=str(uuid7()),
        source_version=version,
        kind=kind,
        measured_at=measured,
        value=Decimal(value),
        unit="kg",
        record_status=status,
    )


class ClinicalSeriesTests(unittest.TestCase):
    def test_series_uses_only_valid_and_orders_by_fact_date(self):
        late_loaded = entry("69", date(2020, 1, 10))
        recent = entry("70", date(2026, 11, 1))
        historical = entry("65", date(2021, 3, 1))
        invalid = entry("700", date(2026, 11, 2), status="entered-in-error")

        selection = select_valid_series(
            [recent, invalid, late_loaded, historical], "weight"
        )

        self.assertEqual(
            [point.measured_at for point in selection.points],
            [date(2020, 1, 10), date(2021, 3, 1), date(2026, 11, 1)],
        )

    def test_correction_replaces_point_without_duplicate(self):
        measurement_id = str(uuid7())
        corrected = SeriesEntry(
            measurement_id=measurement_id, source_version=2, kind="weight",
            measured_at=date(2026, 11, 1), value=Decimal("70"), unit="kg",
            record_status="valid",
        )
        old = SeriesEntry(
            measurement_id=measurement_id, source_version=1, kind="weight",
            measured_at=date(2026, 11, 1), value=Decimal("700"), unit="kg",
            record_status="entered-in-error",
        )

        selection = select_valid_series([corrected, old], "weight")

        self.assertEqual(len(selection.points), 1)
        self.assertEqual(selection.points[0].source_version, 2)
        self.assertEqual(selection.points[0].value, Decimal("70"))

    def test_age_on_measurement_and_future_date_rejected(self):
        birth = date(2020, 2, 29)
        age = age_on(birth, date(2026, 11, 18))
        assert age is not None
        self.assertEqual(age.age_years, 6)
        self.assertGreaterEqual(age.age_months, 80)
        self.assertIsNone(age_on(birth, date(2019, 1, 1)))

    def test_birth_change_or_correction_invalidates_derivatives(self):
        clean = DerivedInputs(selections=[SeriesSelection(points=[])])
        self.assertFalse(clean.invalidated)

        changed = DerivedInputs(
            selections=[SeriesSelection(points=[])], birth_date_changed=True
        )
        self.assertTrue(changed.invalidated)


if __name__ == "__main__":
    unittest.main()
