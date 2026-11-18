import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid7
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from src.api.accounts.domain.accounts import ClinicalPermissions, ClinicalPermissionsPayload
from src.api.accounts.application.accounts_cases import readable_clinical_sections
from src.api.clinical_records.application.access_cases import (
    clinical_result_allowed,
    clinical_result_section,
    clinical_read_scope,
)
from src.api.clinical_records.domain.conditions import SetPatientClinicalSectionReviewPayload
from src.api.sync.application.capabilities_cases import get_capabilities
from src.api.sync.application.download_cases import clinical_change_allowed, position_for_scope
from src.api.sync.domain.downloads import SnapshotRequest, SyncPosition, SyncWindow
from src.core import Err, Ok
from src.core.services.sync_signatures import sign_position


class ClinicalPermissionTests(unittest.TestCase):
    def test_levels_are_independent_and_default_to_read_write(self):
        permissions = ClinicalPermissions(clinical_profile="none", conditions="read")
        self.assertEqual(permissions.level("profile"), "none")
        self.assertEqual(permissions.level("conditions"), "read")
        self.assertEqual(permissions.level("allergies"), "read_write")
        self.assertEqual(ClinicalPermissions().level("profile"), "read_write")

    def test_permission_payload_and_online_catalog(self):
        payload = ClinicalPermissionsPayload.model_validate({
            "clinicalPermissions": {
                "clinicalProfile": "none",
                "conditions": "read",
                "allergies": "read_write",
            }
        })
        self.assertEqual(payload.clinical_permissions.conditions, "read")
        self.assertEqual(payload.clinical_permissions.encounters, "read_write")
        self.assertEqual(payload.clinical_permissions.notes, "read_write")
        self.assertEqual(payload.clinical_permissions.measurements, "read_write")
        self.assertEqual(payload.clinical_permissions.immunizations, "read_write")
        self.assertEqual(payload.clinical_permissions.antecedents, "read_write")
        capabilities = get_capabilities().value
        self.assertIn("SetMemberClinicalPermissions", capabilities.operation_catalog)
        self.assertIn("SetMemberClinicalPermissions", capabilities.online_only_actions)
        with self.assertRaises(ValidationError):
            ClinicalPermissionsPayload.model_validate({"clinicalPermissions": {}, "ownerUserId": str(uuid7())})

    def test_result_scope_covers_every_clinical_action_and_fails_closed(self):
        expected = {
            "SetPatientSexAtBirth": "profile",
            "CreatePatientCondition": "conditions",
            "UpdatePatientCondition": "conditions",
            "InvalidatePatientCondition": "conditions",
            "CreatePatientAllergyIntolerance": "allergies",
            "UpdatePatientAllergyIntolerance": "allergies",
            "InvalidatePatientAllergyIntolerance": "allergies",
            "CreatePatientEncounter": "encounters",
            "UpdatePatientEncounter": "encounters",
            "InvalidatePatientEncounter": "encounters",
            "CreatePatientNote": "notes",
            "UpdatePatientNote": "notes",
            "InvalidatePatientNote": "notes",
            "RecordPatientMeasurement": "measurements",
            "CorrectPatientMeasurement": "measurements",
            "InvalidatePatientMeasurement": "measurements",
            "RecordPatientImmunization": "immunizations",
            "UpdatePatientImmunization": "immunizations",
            "InvalidatePatientImmunization": "immunizations",
            "CreatePatientAntecedent": "antecedents",
            "UpdatePatientAntecedent": "antecedents",
            "InvalidatePatientAntecedent": "antecedents",
        }
        for action, section in expected.items():
            with self.subTest(action=action):
                self.assertEqual(clinical_result_section(action, None), section)
                for level in ("none", "read", "read_write"):
                    context = SimpleNamespace(
                        owner=False,
                        clinical_permissions=ClinicalPermissions.model_validate({
                            section if section != "profile" else "clinicalProfile": level,
                        }),
                    )
                    self.assertEqual(clinical_result_allowed(context, section), level == "read_write")
                    self.assertEqual(section in readable_clinical_sections(context), level != "none")
                    self.assertEqual(
                        clinical_change_allowed("clinical_" + section, readable_clinical_sections(context)),
                        level != "none",
                    )
        for section in ("conditions", "allergies"):
            payload = SetPatientClinicalSectionReviewPayload(
                section=section, information_status="unknown"
            )
            self.assertEqual(
                clinical_result_section("SetPatientClinicalSectionReview", payload),
                section,
            )
        self.assertIsNone(
            clinical_result_section("SetPatientClinicalSectionReview", None)
        )
        self.assertIsNone(clinical_result_section("CreateAppointment", None))

    def test_result_policy_requires_current_section_write_access(self):
        for section in (
            "profile",
            "conditions",
            "allergies",
            "encounters",
            "notes",
            "measurements",
            "immunizations",
            "antecedents",
        ):
            for level in ("none", "read", "read_write"):
                context = SimpleNamespace(
                    owner=False,
                    clinical_permissions=ClinicalPermissions.model_validate({
                        section if section != "profile" else "clinicalProfile": level
                    }),
                )
                with self.subTest(section=section, level=level):
                    self.assertEqual(
                        clinical_result_allowed(context, section),
                        level == "read_write",
                    )
        owner = SimpleNamespace(owner=True, clinical_permissions=ClinicalPermissions())
        self.assertTrue(clinical_result_allowed(owner, "conditions"))
        self.assertFalse(clinical_result_allowed(owner, None))

    def test_clinical_audiences_require_their_explicit_section(self):
        self.assertTrue(clinical_change_allowed("members", []))
        self.assertTrue(clinical_change_allowed("owner", []))
        self.assertFalse(clinical_change_allowed("clinical_profile", []))
        self.assertFalse(clinical_change_allowed("clinical_conditions", ["profile"]))
        self.assertTrue(clinical_change_allowed("clinical_allergies", ["allergies"]))

    def test_stage2_sections_share_scope_without_duplicates(self):
        permissions = ClinicalPermissions(
            encounters="none",
            notes="read",
            measurements="read_write",
            immunizations="none",
            antecedents="read",
        )
        self.assertEqual(permissions.level("encounters"), "none")
        self.assertEqual(permissions.level("notes"), "read")
        self.assertEqual(permissions.level("measurements"), "read_write")
        self.assertEqual(permissions.level("immunizations"), "none")
        self.assertEqual(permissions.level("antecedents"), "read")
        self.assertTrue(clinical_change_allowed("clinical_notes", ["notes"]))
        self.assertFalse(clinical_change_allowed("clinical_notes", ["conditions"]))
        with self.assertRaises(ValidationError):
            SyncPosition(
                account_id=uuid7(),
                user_id=uuid7(),
                device_id=uuid7(),
                audience="members",
                clinical_sections=["notes", "notes"],
                permission_epoch=1,
                sequence=0,
                window=SyncWindow(
                    appointments_from="2026-11-01",
                    appointments_until="2026-11-03",
                    time_zone="America/Caracas",
                    starts_at="2026-11-01T04:00:00Z",
                    ends_at="2026-11-03T04:00:00Z",
                ),
                issued_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )

    def test_snapshot_opt_in_is_strict_and_off_by_default(self):
        self.assertFalse(SnapshotRequest().include_clinical)
        self.assertTrue(SnapshotRequest.model_validate({"includeClinical": True}).include_clinical)
        for value in ("true", 1, None):
            with self.assertRaises(ValidationError):
                SnapshotRequest.model_validate({"includeClinical": value})

    def test_cursor_scope_rejects_sections_outside_current_access(self):
        now = datetime.now(UTC)
        user_id = uuid7()
        device_id = uuid7()
        account_id = uuid7()
        context = SimpleNamespace(
            account=SimpleNamespace(id=account_id),
            actor=SimpleNamespace(user_id=user_id, device_id=device_id),
            owner=False,
            clinical_permissions=ClinicalPermissions(clinical_profile="none", conditions="read", allergies="none"),
        )
        head = SimpleNamespace(permission_epoch=4, retained_from_sequence=1, last_sequence=10)
        position = SyncPosition(
            account_id=account_id,
            user_id=user_id,
            device_id=device_id,
            audience="members",
            clinical_sections=["conditions"],
            permission_epoch=4,
            sequence=0,
            window=SyncWindow(
                appointments_from="2026-11-01",
                appointments_until="2026-11-03",
                time_zone="America/Caracas",
                starts_at="2026-11-01T04:00:00Z",
                ends_at="2026-11-03T04:00:00Z",
            ),
            issued_at=now,
            expires_at=now + timedelta(days=90),
        )
        key = b"fixture-only-clinical-signing-key"
        cursor = sign_position(position.model_dump_json(by_alias=True).encode(), key)
        self.assertIsInstance(position_for_scope(context, head, cursor, key, now), Ok)
        denied = position.model_copy(update={"clinical_sections": ["profile"]})
        cursor = sign_position(denied.model_dump_json(by_alias=True).encode(), key)
        self.assertIsInstance(position_for_scope(context, head, cursor, key, now), Err)
        with self.assertRaises(ValidationError):
            SyncPosition.model_validate({**position.model_dump(), "clinical_sections": ["conditions", "conditions"]})


class ClinicalReadPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_section_reauthorizes_read_levels_and_requires_a_device(self):
        for section in ("profile", "conditions", "allergies", "encounters", "notes", "measurements", "immunizations", "antecedents"):
            for level in ("none", "read", "read_write"):
                field = "clinical_profile" if section == "profile" else section
                context = SimpleNamespace(owner=False, account=SimpleNamespace(status="active"),
                                          clinical_permissions=ClinicalPermissions(**{field: level}))
                with self.subTest(section=section, level=level), \
                    patch("src.api.clinical_records.application.access_cases.authenticate", new=AsyncMock(return_value=Ok(SimpleNamespace()))) as identity, \
                    patch("src.api.clinical_records.application.access_cases.account_context", new=AsyncMock(return_value=Ok(context))) as scope:
                    result = await clinical_read_scope(None, None, uuid7(), section)
                    self.assertEqual(isinstance(result, Ok), level != "none")
                    identity.assert_awaited_once()
                    arguments = scope.await_args
                    assert arguments is not None
                    self.assertTrue(arguments.kwargs["require_device"])


if __name__ == "__main__":
    unittest.main()
