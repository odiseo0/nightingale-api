import unittest
from types import SimpleNamespace

from src.api.accounts.domain.accounts import BillingPermissions, ClinicalPermissions
from src.api.accounts.domain.policies import operation_policies, policy_allows, published_actions
from src.api.sync.application.capabilities_cases import get_capabilities
from src.api.sync.domain.operations import BLOCK_SCHEMAS, OFFER_SCHEMAS, SERVICE_SCHEMAS


class AuthorizationPolicyTests(unittest.TestCase):
    def test_object_rules_cover_exactly_the_existing_dispatch_groups(self):
        policies = operation_policies()
        for rule, schemas in (("own_catalog", SERVICE_SCHEMAS), ("own_offer", OFFER_SCHEMAS), ("block", BLOCK_SCHEMAS)):
            self.assertEqual({name for name, policy in policies.items() if policy.object_rule == rule}, set(schemas))
        self.assertEqual(policies["UpdateProfessionalProfile"].object_rule, "own_professional")

    def context(self, *, owner=False, account="active", device="active", **permissions):
        billing = permissions.pop("billing_permissions", BillingPermissions())
        return SimpleNamespace(
            owner=owner, account=SimpleNamespace(status=account), device_status=device,
            clinical_permissions=ClinicalPermissions(**permissions),
            billing_permissions=billing,
        )

    def test_catalog_covers_transport_and_keeps_private_invitation_acceptance(self):
        policies = operation_policies()
        self.assertEqual(set(policies), set(get_capabilities().value.operation_catalog) | {"AcceptInvitation"})
        self.assertEqual(policies["AcceptInvitation"].publication, ())
        self.assertFalse(policy_allows(self.context(owner=True), "UnknownAction"))
        self.assertEqual(policies["CreateService"].object_rule, "own_catalog")
        self.assertEqual(policies["CreateScheduleBlock"].object_rule, "block")

    def test_owner_only_rules_match_administrative_matrix(self):
        expected = set("""CreateInvitation RevokeInvitation SetMembershipStatus SetMemberClinicalPermissions
            UpdateAccountDetails UpdateAccountPolicy SetAccountStatus RevokeAccountDevice RestoreAccountDevice
            UpdateProfessionalProfile CreateService UpdateService SetServiceStatus SetServicePrice OfferService
            UpdateServiceOffer SetServiceOfferStatus SetServiceOfferPrice RemoveServiceOfferPrice
            SetMemberBillingPermissions""".split())
        policies = operation_policies()
        self.assertEqual({name for name, rule in policies.items() if rule.owner_only}, expected)
        for action in expected:
            with self.subTest(action=action):
                self.assertFalse(policy_allows(self.context(), action))
                self.assertTrue(policy_allows(self.context(owner=True), action))

    def test_sections_need_the_current_level_and_reviews_need_a_validated_section(self):
        seen = set()
        for action, policy in operation_policies().items():
            for section in policy.sections:
                seen.add(section)
                self.assertEqual(policy.required_level, "read_write")
                for level in ("none", "read", "read_write"):
                    field = "clinical_profile" if section == "profile" else section
                    context = self.context(**{field: level})
                    with self.subTest(action=action, section=section, level=level):
                        self.assertEqual(policy_allows(context, action, section), level == "read_write")
                self.assertFalse(policy_allows(self.context(), action))
        self.assertEqual(seen, {"profile", "conditions", "allergies", "encounters", "notes", "measurements", "immunizations", "antecedents", "declared_medications", "care_plans", "diagnostic_reports", "specialty_templates"})
        self.assertFalse(policy_allows(self.context(owner=True), "SetPatientClinicalSectionReview", "notes"))

    def test_device_and_inactive_account_exceptions_and_shared_review_positions(self):
        for owner in (False, True):
            self.assertEqual(published_actions(self.context(owner=owner, device=None)), ["RegisterAccountDevice"])
            self.assertEqual(published_actions(self.context(owner=owner, device="revoked")), [])
            self.assertEqual(published_actions(self.context(owner=owner, account="inactive")), ["SetAccountStatus"] if owner else [])
            for device in (None, "revoked"):
                self.assertEqual(published_actions(self.context(owner=owner, account="inactive", device=device)), [])
        actions = published_actions(self.context())
        self.assertEqual(actions.count("SetPatientClinicalSectionReview"), 2)
        self.assertEqual(actions[actions.index("InvalidatePatientCondition") + 1], "SetPatientClinicalSectionReview")
        self.assertEqual(actions[actions.index("InvalidatePatientAllergyIntolerance") + 1], "SetPatientClinicalSectionReview")
        self.assertEqual(published_actions(self.context(conditions="none")).count("SetPatientClinicalSectionReview"), 1)
        self.assertEqual(published_actions(self.context(conditions="none", allergies="read")).count("SetPatientClinicalSectionReview"), 0)
