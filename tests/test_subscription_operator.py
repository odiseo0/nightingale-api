import unittest
from uuid import uuid4

from pydantic import ValidationError

from src.api.subscriptions.domain.operators import (
    PlatformOperator,
    OperatorAccessDeniedError,
    ensure_operator_action,
    revoke_operator,
)
from src.core.services.device_tokens import issue_token, parse_token


def operator(**overrides) -> PlatformOperator:
    values = {
        "operator_id": uuid4(),
        "display_name": "Operador ficticio",
        "actions": frozenset({"review"}),
    }
    values.update(overrides)
    return PlatformOperator(**values)


class OperatorAccessTests(unittest.TestCase):
    def test_active_operator_uses_only_granted_actions(self):
        reviewer = operator()
        ensure_operator_action(reviewer, credential_revoked=False, action="review")
        for denied in ("catalog", "rates", "operators"):
            with self.assertRaises(OperatorAccessDeniedError, msg=denied):
                ensure_operator_action(reviewer, credential_revoked=False, action=denied)

    def test_revoked_operator_loses_access_even_with_a_valid_credential(self):
        revoked = revoke_operator(operator())
        self.assertEqual(revoked.status, "revoked")
        self.assertEqual(revoked.version, 2)
        with self.assertRaises(OperatorAccessDeniedError):
            ensure_operator_action(revoked, credential_revoked=False, action="review")
        with self.assertRaises(OperatorAccessDeniedError):
            revoke_operator(revoked)

    def test_revoked_credential_denies_an_active_operator(self):
        with self.assertRaises(OperatorAccessDeniedError):
            ensure_operator_action(operator(), credential_revoked=True, action="review")

    def test_operator_has_no_account_membership_or_clinical_shape(self):
        # D23: the platform actor cannot become owner/assistant nor reach clinical data;
        # its model simply has no account, role or section fields to authorize with.
        self.assertEqual(
            set(PlatformOperator.model_fields),
            {"operator_id", "display_name", "actions", "status", "version"},
        )
        with self.assertRaises(ValidationError):
            operator(actions=frozenset())
        with self.assertRaises(ValidationError):
            operator(actions=frozenset({"admin"}))

    def test_all_actions_can_be_granted_together(self):
        full = operator(actions=frozenset({"review", "catalog", "rates", "operators"}))
        for action in ("review", "catalog", "rates", "operators"):
            ensure_operator_action(full, credential_revoked=False, action=action)


class OperatorCredentialTests(unittest.TestCase):
    def test_operator_credentials_reuse_the_opaque_revocable_pattern(self):
        # D23 reuses the device-token pattern: 256-bit secret, only the hash persists.
        token_id, secret, digest = issue_token()
        self.assertTrue(secret.startswith(f"ngt_{token_id}."))

        parsed = parse_token(secret)
        self.assertIsNotNone(parsed)
        parsed_id, parsed_digest = parsed
        self.assertEqual(parsed_id, token_id)
        self.assertEqual(parsed_digest, digest)

    def test_malformed_credentials_do_not_parse(self):
        for invalid in ("", "ngt_", "ngt_not-a-uuid.x", "bearer abc", "ngt_" + "0" * 36 + ".short"):
            self.assertIsNone(parse_token(invalid), invalid)


if __name__ == "__main__":
    unittest.main()
