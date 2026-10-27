import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.appointments.domain.appointments import AppointmentInterval, AppointmentReasonPayload, CreateAppointmentPayload, AppointmentQuery, EmptyAppointmentPayload


class AppointmentSchemaTests(unittest.TestCase):
    def test_terminal_action_reason_is_optional_administrative_text(self):
        self.assertIsNone(AppointmentReasonPayload().change_reason)
        self.assertEqual(AppointmentReasonPayload(changeReason=" Fixture reason ").change_reason,"Fixture reason")
        for value in ({"changeReason":" "},{"status":"cancelled"},{"actorUserId":str(uuid7())}):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                AppointmentReasonPayload.model_validate(value)

    def test_reschedule_does_not_accept_reference_or_snapshot_changes(self):
        base = {"startsAt":"2026-11-02T12:00:00Z","endsAt":"2026-11-02T12:45:00Z"}
        self.assertEqual(AppointmentInterval.model_validate(base).starts_at.minute,0)
        for patch in ({"patientId":str(uuid7())},{"serviceNameSnapshot":"Changed"},{"confirmedAt":None},{"endsAt":"2026-11-02T12:45:01Z"}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                AppointmentInterval.model_validate({**base,**patch})

    def test_confirmation_accepts_only_an_empty_object(self):
        self.assertEqual(EmptyAppointmentPayload().model_dump(),{})
        for value in ({"actorUserId":str(uuid7())},{"confirmedAt":"2026-10-27T00:00:00Z"},None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                EmptyAppointmentPayload.model_validate(value)

    def test_creation_uses_explicit_offsets_whole_minutes_and_no_client_state(self):
        base = {
            "patientId":str(uuid7()),"professionalId":str(uuid7()),"serviceId":str(uuid7()),
            "startsAt":"2026-10-27T09:00:00-04:00","endsAt":"2026-10-27T09:45:00-04:00",
        }
        self.assertIsNone(CreateAppointmentPayload.model_validate(base).responsible_contact_id)
        self.assertEqual(CreateAppointmentPayload.model_validate(base).model_dump(mode="json",by_alias=True)["startsAt"],"2026-10-27T13:00:00Z")
        for patch in (
            {"startsAt":"2026-10-27T09:00:01-04:00"}, {"endsAt":"2026-10-27T09:00:00-04:00"},
            {"endsAt":"2026-10-28T09:01:00-04:00"}, {"startsAt":0},
            {"startsAt":"2026-10-27T09:00:00"}, {"status":"confirmed"},
            {"actorUserId":str(uuid7())}, {"serviceNameSnapshot":"Client name"},
        ):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                CreateAppointmentPayload.model_validate({**base,**patch})

    def test_list_requires_a_bounded_range_and_public_filter_names(self):
        base = {"from":"2026-10-27T00:00:00Z","until":"2026-10-28T00:00:00Z","status":"scheduled"}
        self.assertEqual(AppointmentQuery.model_validate(base).status,"scheduled")
        for patch in ({"until":"2026-10-27T00:00:00Z"},{"until":"2028-01-01T00:00:00Z"},{"status":"active"},{"shows":501}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                AppointmentQuery.model_validate({**base,**patch})
