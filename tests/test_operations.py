import unittest
from uuid import uuid7

from pydantic import ValidationError

from src.api.sync.domain.operations import OperationBatch, OperationEnvelope


class OperationSchemaTests(unittest.TestCase):
    def operation(self, **changes):
        return {
            "operationId": str(uuid7()), "contractVersion": 1,
            "action": "RegisterAccountDevice", "entityKey": str(uuid7()),
            "expectedVersion": 0, "payload": {}, **changes,
        }

    def test_envelope_preserves_payload_and_normalizes_optional_fields(self):
        operation = OperationEnvelope.model_validate(self.operation(payload={"name": " Fixture "}))
        self.assertEqual(operation.payload, {"name": " Fixture "})
        self.assertEqual(operation.depends_on, [])
        self.assertIsNone(operation.occurred_at_local)
        self.assertEqual(operation.model_dump(mode="json", by_alias=True)["dependsOn"], [])
        self.assertEqual(OperationEnvelope.model_validate(self.operation(action=" FutureOperation ")).action, " FutureOperation ")

    def test_batch_rejects_duplicate_and_forward_dependencies_before_effects(self):
        first, second = self.operation(), self.operation()
        for operations in (
            [first, first], [dict(first, dependsOn=[first["operationId"]])],
            [dict(first, dependsOn=[second["operationId"]]), second],
            [dict(first, dependsOn=[second["operationId"]] * 2)],
        ):
            with self.subTest(operations=operations), self.assertRaises(ValidationError):
                OperationBatch.model_validate({"operations": operations})
        self.assertEqual(len(OperationBatch.model_validate({
            "operations": [first, dict(second, dependsOn=[first["operationId"]])],
        }).operations), 2)

    def test_structural_limits_and_unsafe_values_are_rejected(self):
        for change in (
            {"expectedVersion": True}, {"contractVersion": True}, {"expectedVersion": -1}, {"action": " "},
            {"contractVersion": 2}, {"actorUserId": str(uuid7())},
            {"entityKey": {"arbitrary": str(uuid7())}}, {"occurredAtLocal": "2026-10-26T12:00:00"},
            {"dependsOn": [str(uuid7()) for _ in range(9)]}, {"payload": {"value": float("nan")}},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                OperationEnvelope.model_validate(self.operation(**change))
        for items in ([], [self.operation() for _ in range(101)]):
            with self.assertRaises(ValidationError):
                OperationBatch.model_validate({"operations": items})
