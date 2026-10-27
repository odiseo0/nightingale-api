import unittest
import test_foundation as foundation
from uuid import uuid7

from pydantic import ValidationError

from src.api.schedule.domain.schedule import CreateScheduleRulePayload, ScheduleRulePatch, ScheduleRuleQuery
from src.api.schedule.domain.schedule import (
    CreateScheduleExceptionPayload, ScheduleExceptionPatch, ScheduleExceptionQuery,
    CreateScheduleBlockPayload, ScheduleBlockPatch, ScheduleBlockQuery,
    AvailabilityQuery,
)


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


class ExceptionSchemaTests(unittest.TestCase):
    def test_closed_and_replacement_are_distinct_valid_shapes(self):
        base = {"professionalId": str(uuid7()), "localDate": "2026-10-27", "kind": "closed"}
        self.assertIsNone(CreateScheduleExceptionPayload.model_validate(base).local_start_minute)
        self.assertEqual(CreateScheduleExceptionPayload.model_validate({
            **base, "kind": "replacement", "localStartMinute": 0, "localEndMinute": 1440,
        }).local_end_minute, 1440)

        for patch in (
            {"localStartMinute": 1}, {"localDate": "2026-10-27T00:00:00Z"},
            {"localDate": 0}, {"kind": "replacement"},
            {"kind": "replacement", "localStartMinute": 1, "localEndMinute": 1},
            {"kind": "replacement", "localStartMinute": False, "localEndMinute": 60},
            {"kind": "replacement", "localStartMinute": 0, "localEndMinute": 1441},
        ):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                CreateScheduleExceptionPayload.model_validate({**base, **patch})

    def test_patch_preserves_explicit_null_for_combined_validation(self):
        data = ScheduleExceptionPatch(kind="closed", localStartMinute=None, localEndMinute=None)
        self.assertEqual(data.model_dump(exclude_unset=True), {
            "kind": "closed", "local_start_minute": None, "local_end_minute": None,
        })
        for patch in ({}, {"kind": None}, {"localDate": None}, {"professionalId": str(uuid7())}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ScheduleExceptionPatch.model_validate(patch)

    def test_exception_lists_require_a_bounded_local_date_range(self):
        self.assertEqual(ScheduleExceptionQuery(fromDate="2026-01-01", untilDate="2027-01-01").shows, 100)
        for query in (
            {}, {"fromDate": "2026-01-01"},
            {"fromDate": "2026-01-01", "untilDate": "2027-01-02"},
            {"fromDate": "2026-10-28", "untilDate": "2026-10-27"},
        ):
            with self.subTest(query=query), self.assertRaises(ValidationError):
                ScheduleExceptionQuery.model_validate(query)


class BlockSchemaTests(unittest.TestCase):
    def test_absolute_interval_and_explicit_scope(self):
        base = {
            "professionalId": str(uuid7()), "accountId": None, "reasonCode": "vacation",
            "startsAt": "2026-10-27T09:00:00-04:00", "endsAt": "2026-10-27T10:00:00-04:00",
        }
        block = CreateScheduleBlockPayload.model_validate(base)
        self.assertEqual(block.model_dump(mode="json", by_alias=True)["startsAt"], "2026-10-27T13:00:00Z")
        for patch in (
            {"startsAt": "2026-10-27T09:00:00"}, {"startsAt": 0},
            {"endsAt": "2026-10-27T13:00:00Z"}, {"reasonCode": "clinical"},
            {"startsAt": None}, {"startsAt": "infinity"},
            {"startsAt": "0"}, {"startsAt": "20261027T090000Z"},
            {"startsAt": "2026-10-27T09:00:00+0400"},
        ):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                CreateScheduleBlockPayload.model_validate({**base, **patch})
        del base["accountId"]
        with self.assertRaises(ValidationError):
            CreateScheduleBlockPayload.model_validate(base)

    def test_patch_has_no_scope_change_and_rejects_null(self):
        for patch in ({}, {"accountId": None}, {"professionalId": str(uuid7())}, {"startsAt": None}, {"endsAt": None}, {"reasonCode": None}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ScheduleBlockPatch.model_validate(patch)

    def test_utc_query_requires_bounded_interval(self):
        base = {"from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z"}
        self.assertEqual(ScheduleBlockQuery.model_validate(base).shows, 100)
        for patch in ({"until": "2026-01-01T00:00:00Z"}, {"until": "2027-01-03T00:00:00Z"}, {"from": 0}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ScheduleBlockQuery.model_validate({**base, **patch})


class AvailabilityTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_query_requires_duration_and_range_limits(self):
        base = {"professionalId":str(uuid7()),"serviceId":str(uuid7()),"from":"2026-10-01T00:00:00Z","until":"2026-11-01T00:00:00Z"}
        self.assertIsNone(AvailabilityQuery.model_validate(base).duration_minutes)
        for patch in ({"until":"2026-11-01T00:01:00Z"},{"durationMinutes":0},{"durationMinutes":1441},{"durationMinutes":True},{"durationMinutes":1.5},{"from":0},{"shows":10}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                AvailabilityQuery.model_validate({**base,**patch})

    def test_local_gaps_folds_and_variable_length_days(self):
        result = self.run_python("""
            from datetime import date
            from zoneinfo import ZoneInfo
            from src.api.schedule.application.availability_cases import local_instant
            zone = ZoneInfo('America/New_York')
            rejected = 0
            for day, minute in ((date(2026,3,8),150),(date(2026,11,1),90)):
                try:
                    local_instant(day,minute,zone)
                except ValueError:
                    rejected += 1
            durations = []
            for day in (date(2026,3,8),date(2026,11,1)):
                durations.append((local_instant(day,1440,zone)-local_instant(day,0,zone)).total_seconds()/3600)
            print(json.dumps({'rejected':rejected,'hours':durations}))
        """, self.database_settings())
        self.assertEqual(result, {"rejected":2,"hours":[23,25]})

    def test_subtraction_unions_boundaries_duration_and_minute_precision(self):
        result = self.run_python("""
            from datetime import datetime
            from src.api.schedule.application.availability_cases import free_intervals
            from src.api.schedule.domain.schedule import AbsoluteInterval
            def instant(value):
                return datetime.fromisoformat('2026-10-27T'+value+'Z')
            def interval(start,end):
                return AbsoluteInterval(starts_at=instant(start),ends_at=instant(end))
            opened=[interval('08:00','10:00'),interval('09:00','12:00'),interval('12:00','13:00')]
            busy=[interval('07:00','08:00'),interval('09:00','09:30'),interval('09:15','10:00'),interval('11:00','11:00:30')]
            free=free_intervals(opened,busy,instant('08:00'),instant('13:00'),30)
            print(json.dumps({'free':[(i.starts_at.strftime('%H:%M'),i.ends_at.strftime('%H:%M')) for i in free]}))
        """, self.database_settings())
        self.assertEqual(result["free"], [["08:00","09:00"],["10:00","11:00"],["11:01","13:00"]])
