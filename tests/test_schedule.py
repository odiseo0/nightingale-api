import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.schedule.domain.schedule import CreateScheduleRulePayload, ScheduleRulePatch, ScheduleRuleQuery


class ScheduleSchemaTests(unittest.TestCase):
    def rule(self, **values):
        return {"professionalId": str(uuid7()), "isoWeekday": 1, "localStartMinute": 0,
                "localEndMinute": 1440, "validFrom": "2026-10-26", **values}

    def test_iso_minutes_dates_and_midnight_end(self):
        self.assertEqual(CreateScheduleRulePayload.model_validate(self.rule()).local_end_minute, 1440)
        for values in (
            {"isoWeekday": 0}, {"isoWeekday": 8}, {"isoWeekday": True},
            {"localStartMinute": -1}, {"localStartMinute": 1440},
            {"localEndMinute": 0}, {"localEndMinute": 1441},
            {"localStartMinute": 60, "localEndMinute": 60},
            {"localStartMinute": 1.5}, {"localEndMinute": True},
            {"validFrom": 0}, {"validFrom": "2026-10-26T00:00:00Z"},
            {"validUntil": "2026-10-25"}, {"validUntil": "infinity"},
            {"status": "active"}, {"accountId": str(uuid7())},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                CreateScheduleRulePayload.model_validate(self.rule(**values))

    def test_patch_keeps_absence_and_explicit_open_end(self):
        self.assertEqual(ScheduleRulePatch(validUntil=None).model_dump(exclude_unset=True), {"valid_until": None})
        for values in ({}, {"isoWeekday": None}, {"localStartMinute": None}, {"validFrom": None}, {"professionalId": str(uuid7())}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                ScheduleRulePatch.model_validate(values)

    def test_query_validates_range_and_public_filter_names(self):
        query = ScheduleRuleQuery(fromDate="2026-10-26", untilDate="2026-10-26", isoWeekday=1)
        self.assertEqual(query.model_dump(mode="json", by_alias=True)["fromDate"], "2026-10-26")
        for values in ({"fromDate": "2026-10-27", "untilDate": "2026-10-26"}, {"isoWeekday": 8}, {"page": 0}, {"shows": 501}, {"other": 1}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                ScheduleRuleQuery.model_validate(values)
