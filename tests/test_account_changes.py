import unittest

from pydantic import ValidationError

from src.api.accounts.domain.accounts import AccountDetailsPatch, AccountPolicyPayload, InvitationAcceptRequest


class AccountChangeSchemaTests(unittest.TestCase):
    def test_scope_changes_and_clinical_columns_match_the_existing_contract(self):
        from src.api.accounts.domain.accounts import ClinicalPermissions
        from src.api.accounts.domain.policies import clinical_permission_values, operation_policies, scope_changes

        expected = {"RegisterAccountDevice", "AcceptInvitation", "SetAccountStatus", "SetMembershipStatus",
                    "SetMemberClinicalPermissions", "RevokeAccountDevice", "RestoreAccountDevice"}
        self.assertEqual({name for name in operation_policies() if scope_changes(name)}, expected)
        self.assertFalse(scope_changes("UnknownAction"))
        values = clinical_permission_values(ClinicalPermissions(clinical_profile="none", notes="read"))
        self.assertEqual(set(values), {name + "_access" for name in (
            "clinical_profile", "conditions", "allergies", "encounters", "notes", "measurements", "immunizations", "antecedents", "declared_medications", "care_plans", "diagnostic_reports", "specialty_templates")})
        self.assertEqual(values["clinical_profile_access"], "none")
        self.assertEqual(values["notes_access"], "read")
        self.assertEqual(values["encounters_access"], "read_write")

    def test_patch_distinguishes_absent_and_null_and_rejects_identity_fields(self):
        self.assertEqual(AccountDetailsPatch().model_dump(exclude_unset=True), {})
        for data in ({"displayName": None}, {"timeZone": None}, {"ownerUserId": "fixture"}, {"displayName": " "}, {"locationCountry": "ZZ"}, {"locationCountry": None}):
            with self.assertRaises(ValidationError):
                AccountDetailsPatch.model_validate(data)

    def test_policy_requires_an_integer_in_the_approved_range(self):
        for value in (True, -1, 1441, "15"):
            with self.assertRaises(ValidationError):
                AccountPolicyPayload.model_validate({"noShowGraceMinutes": value})
        self.assertEqual(AccountPolicyPayload(no_show_grace_minutes=0).no_show_grace_minutes, 0)

    def test_invitation_acceptance_does_not_take_claimed_identity(self):
        from uuid import uuid7

        with self.assertRaises(ValidationError):
            InvitationAcceptRequest.model_validate({"operationId": str(uuid7()), "userId": str(uuid7())})
