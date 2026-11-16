import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid7

from pydantic import ValidationError

from src.api.accounts.domain.accounts import ClinicalPermissions, ClinicalPermissionsPayload
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
        capabilities = get_capabilities().value
        self.assertIn("SetMemberClinicalPermissions", capabilities.operation_catalog)
        self.assertIn("SetMemberClinicalPermissions", capabilities.online_only_actions)
        with self.assertRaises(ValidationError):
            ClinicalPermissionsPayload.model_validate({"clinicalPermissions": {}, "ownerUserId": str(uuid7())})

    def test_clinical_audiences_require_their_explicit_section(self):
        self.assertTrue(clinical_change_allowed("members", []))
        self.assertTrue(clinical_change_allowed("owner", []))
        self.assertFalse(clinical_change_allowed("clinical_profile", []))
        self.assertFalse(clinical_change_allowed("clinical_conditions", ["profile"]))
        self.assertTrue(clinical_change_allowed("clinical_allergies", ["allergies"]))

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


if __name__ == "__main__":
    unittest.main()
