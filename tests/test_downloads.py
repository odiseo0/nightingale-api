import unittest
from datetime import UTC, datetime, timedelta
from typing import get_args, get_type_hints
from uuid import uuid7

from pydantic import ValidationError

from src.api.accounts.domain.accounts import AccountChange
from src.api.sync.application.download_cases import CLINICAL_AUDIENCES, clinical_change_allowed
from src.api.sync.domain.downloads import ChangeGroup, ChangeQuery, SnapshotRequest, SnapshotResponse, SyncChange, SyncPosition, SyncWindow
from src.api.sync.domain.events import Heartbeat
from src.core.services.sync_signatures import sign_position, verify_position


class DownloadSchemaTests(unittest.TestCase):
    def test_projection_catalog_covers_entities_and_filters_roles_and_sections(self):
        from src.api.accounts.domain.policies import projection_allowed, projection_audiences
        from src.api.sync.domain.downloads import PROJECTION_SCHEMAS

        self.assertEqual(set(projection_audiences()), set(PROJECTION_SCHEMAS))
        for entity in ("account_device", "membership", "invitation", "service"):
            self.assertFalse(projection_allowed(entity, None, False, []))
            self.assertTrue(projection_allowed(entity, None, True, []))
        for entity, section in (
            ("patient_clinical_profile", "profile"), ("patient_condition", "conditions"),
            ("patient_allergy_intolerance", "allergies"), ("clinical_encounter", "encounters"),
            ("patient_note", "notes"), ("patient_measurement", "measurements"),
            ("patient_immunization", "immunizations"), ("patient_antecedent", "antecedents"),
            ("declared_medication", "declared_medications"),
            ("care_plan", "care_plans"), ("care_plan_goal", "care_plans"),
            ("care_plan_action", "care_plans"), ("care_plan_review", "care_plans"),
            ("diagnostic_report", "diagnostic_reports"),
            ("diagnostic_report_result", "diagnostic_reports"),
            ("report_attachment", "diagnostic_reports"),
            ("specialty_template", "specialty_templates"),
            ("specialty_record", "specialty_templates"),
            ("dental_finding", "specialty_templates"),
            ("dental_treatment", "specialty_templates"),
        ):
            for level in ("none", "read", "read_write"):
                sections = [] if level == "none" else [section]
                self.assertEqual(projection_allowed(entity, None, False, sections), level != "none")
                self.assertEqual(projection_allowed(entity, "clinical_" + section, False, sections), level != "none")
        for section in ("conditions", "allergies"):
            self.assertTrue(projection_allowed("patient_clinical_section_review", None, False, [section], section))
        self.assertFalse(projection_allowed("patient_clinical_section_review", None, True, ["conditions"]))
        self.assertFalse(projection_allowed("patient_note", "clinical_conditions", True, ["conditions"]))
        self.assertFalse(projection_allowed("unknown", "members", True, []))
        self.assertFalse(clinical_change_allowed("unknown", []))

    def test_public_instants_use_utc_z_with_an_offset_input(self):
        instant = "2026-11-01T03:00:00-04:00"
        expected = "2026-11-01T07:00:00Z"
        group = ChangeGroup(group_id=uuid7(), operation_id=uuid7(), changes=[], accepted_at=instant)
        self.assertEqual(group.model_dump(mode="json", by_alias=True)["acceptedAt"], expected)
        capture = SnapshotResponse(snapshot_id=uuid7(), account_id=uuid7(), model_revision="api-v1.1", base_cursor="fixture",
                                   window=SyncWindow(appointments_from="2026-11-01", appointments_until="2026-11-02", time_zone="America/Caracas",
                                                     starts_at="2026-11-01T04:00:00Z", ends_at="2026-11-02T04:00:00Z"), expires_at=instant, item_count=0)
        self.assertEqual(capture.model_dump(mode="json", by_alias=True)["expiresAt"], expected)
        self.assertEqual(Heartbeat(server_time=instant).model_dump(mode="json", by_alias=True)["serverTime"], expected)

    def test_snapshot_dates_are_explicit_bounded_and_separate_from_page_parameters(self):
        self.assertIsNone(SnapshotRequest().appointments_from)
        self.assertEqual(SnapshotRequest(appointmentsFrom="2026-11-01").appointments_from.isoformat(), "2026-11-01")
        for data in ({"appointmentsFrom": None}, {"appointmentsFrom": "20261101"}, {"page": 1},
                     {"appointmentsFrom": "2026-11-01", "appointmentsUntil": "2026-11-01"},
                     {"appointmentsFrom": "2026-01-01", "appointmentsUntil": "2028-01-01"}):
            with self.assertRaises(ValidationError):
                SnapshotRequest.model_validate(data)

    def test_mac_rejects_altered_body_signature_wrong_key_and_noncanonical_encoding(self):
        key = b"fictional-signing-key-for-tests-only"
        body = b'{"sequence":12}'
        signed = sign_position(body, key)
        self.assertEqual(verify_position(signed, key), body)
        for value in (signed + "=", "x" + signed, signed[:-1], ".", "é", signed.replace(".", "..")):
            self.assertIsNone(verify_position(value, key))
        self.assertIsNone(verify_position(signed, b"other-key"))

    def test_change_query_requires_only_incremental_cursor(self):
        for value in ({}, {"cursor": "a", "page": 2}, {"cursor": "a", "shows": 1}, {"cursor": "x" * 8193}):
            with self.assertRaises(ValidationError):
                ChangeQuery.model_validate(value)

    def test_cursor_carries_scope_and_fixed_window_and_rejects_unbounded_lifetime(self):
        now = datetime.now(UTC)
        data = dict(account_id=uuid7(), user_id=uuid7(), device_id=uuid7(), audience="members",
                    permission_epoch=1, sequence=0, issued_at=now, expires_at=now + timedelta(days=90),
                    window=SyncWindow(appointments_from="2026-11-01", appointments_until="2026-11-03",
                                      time_zone="America/Caracas", starts_at="2026-11-01T04:00:00Z", ends_at="2026-11-03T04:00:00Z"))
        parsed = SyncPosition.model_validate_json(SyncPosition(**data).model_dump_json(by_alias=True))
        self.assertEqual(parsed.window.time_zone, "America/Caracas")
        for patch in ({"expires_at": now}, {"sequence": -1}, {"permission_epoch": 0}, {"expires_at": now + timedelta(days=91)}):
            with self.assertRaises(ValidationError):
                SyncPosition(**{**data, **patch})

    def test_remove_has_no_state_and_unknown_entity_cannot_leak_a_projection(self):
        data = dict(entity_type="appointment", entity_key=uuid7(), entity_version=2, change_kind="remove", state=None)
        self.assertIsNone(SyncChange(**data).state)
        for patch in ({"change_kind": "upsert"}, {"entity_type": "unknown"}, {"state": {"private": "fixture"}}):
            with self.assertRaises(ValidationError):
                SyncChange(**{**data, **patch})

    def test_every_journal_audience_has_exactly_one_section_rule(self):
        audience_type = get_type_hints(AccountChange)["audience"]
        audiences = set(get_args(audience_type))
        administrative = {"members", "owner"}
        # The closed financial audience of D27/D28 is never derived from clinical
        # sections; its read filtering is wired by the billing sync task (T24).
        financial = {"billing"}
        self.assertEqual(audiences, administrative | financial | set(CLINICAL_AUDIENCES))
        self.assertFalse(administrative & set(CLINICAL_AUDIENCES))
        self.assertEqual(set(CLINICAL_AUDIENCES.values()), set(get_args(get_type_hints(AccountChange)["audience"])[2:-1]) and {
            "profile", "conditions", "allergies", "encounters", "notes",
            "measurements", "immunizations", "antecedents", "declared_medications", "care_plans", "diagnostic_reports", "specialty_templates",
        })
        for audience in administrative:
            for sections in ([], ["conditions"]):
                self.assertTrue(clinical_change_allowed(audience, sections))
        for sections in ([], ["conditions"], ["notes"]):
            self.assertFalse(clinical_change_allowed("billing", sections))
        for audience, section in CLINICAL_AUDIENCES.items():
            self.assertTrue(clinical_change_allowed(audience, [section]))
            self.assertFalse(clinical_change_allowed(audience, [s for s in CLINICAL_AUDIENCES.values() if s != section]))
