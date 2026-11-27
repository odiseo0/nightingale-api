import unittest
from decimal import Decimal
from uuid import uuid7

from pydantic import ValidationError

from src.api.accounts.domain.accounts import BillingPermissions
from src.api.billing.domain.charges import CreatePatientChargePayload

# The offline policy of D28: only charge drafts are prepared offline as typed
# operations; API revalidates price, object, permission and version at
# acceptance. These tests pin the payload/permission side; the probe exercises
# the batch path end to end (tests use the shared billing fixtures).


class OfflineIntentTests(unittest.TestCase):
    def test_offline_draft_payload_carries_no_price_nor_state(self):
        # An offline draft never fixes the price: without an explicit manual
        # amount the server resolves the CURRENT price at acceptance (D25/D28).
        payload = CreatePatientChargePayload.model_validate({
            "patientId": str(uuid7()), "serviceId": str(uuid7()),
        })
        self.assertIsNone(payload.amount)
        self.assertIsNone(payload.currency)
        with self.assertRaises(ValidationError):
            # A stale local clock or client state cannot ride along.
            CreatePatientChargePayload.model_validate({
                "patientId": str(uuid7()), "serviceId": str(uuid7()),
                "issuedAt": "2026-11-27T00:00:00Z",
            })

    def test_local_cache_grants_nothing(self):
        # A local copy of permissions never authorizes: the context grant is
        # evaluated at acceptance time, and the default is denied (D27).
        self.assertFalse(BillingPermissions().granted("billing_charges"))
        self.assertTrue(
            BillingPermissions(billing_charges="granted").granted("billing_charges")
        )


if __name__ == "__main__":
    unittest.main()
