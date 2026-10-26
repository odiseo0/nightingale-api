import unittest

from pydantic import ValidationError

from src.api.accounts.domain.accounts import AccountDetailsPatch, AccountPolicyPayload, InvitationAcceptRequest


class AccountChangeSchemaTests(unittest.TestCase):
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
