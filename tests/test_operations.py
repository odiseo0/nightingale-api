import json
import unittest
from pathlib import Path
from uuid import uuid7

import test_foundation as foundation
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


class InvitationOperationTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_invitation_results_keep_the_original_and_reject_missing_internal_data(self):
        result = self.run_python("""
            import asyncio
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7

            from src.api.accounts.domain.accounts import (
                AccountDeviceResponse, InvitationAcceptanceResult,
            )
            from src.api.accounts.domain.errors import AccountRuleError
            from src.api.sync.application.operations_cases import accept_invitation
            from src.api.sync.domain.operations import OperationRecord, OperationResult
            from src.core import Err, Ok
            from src.core.db import DAOError
            from src.core.schema import ApiError

            operation_id, invitation_id, account_id, correlation_id = [uuid7() for _ in range(4)]
            state = InvitationAcceptanceResult(
                operation_id=operation_id, status="accepted", invitation_id=invitation_id,
                account_id=account_id, membership_version=1,
            )

            def response(status, *, state=None, error=None, original_result=None):
                return OperationResult(
                    operation_id=operation_id, status=status, entity_version=1,
                    state=state, error=error, original_result=original_result,
                )

            async def accept(value):
                with patch(
                    "src.api.sync.application.operations_cases.accept_operation",
                    new=AsyncMock(return_value=Ok(value)),
                ):
                    return await accept_invitation(
                        None, None, invitation_id, operation_id, correlation_id,
                    )

            async def check():
                accepted = response("accepted", state=state)
                original = OperationRecord.model_validate(accepted.model_dump())
                duplicate = response("duplicate", state=state, original_result=original)

                for value in (accepted, duplicate):
                    result = await accept(value)
                    assert isinstance(result, Ok)
                    assert isinstance(result.value, InvitationAcceptanceResult)
                    assert result.value.status == value.status
                    assert result.value.invitation_id == invitation_id
                    assert original.state.status == "accepted"

                error = ApiError(code="NO_CHANGES", message="Fixture", correlation_id=correlation_id)
                for status in ("rejected", "conflict", "retryable_failure"):
                    rejected = response(status, error=error)
                    result = await accept(rejected)
                    assert isinstance(result, Err) and result.error == AccountRuleError("NO_CHANGES", 1)

                    original_rejection = OperationRecord.model_validate(rejected.model_dump())
                    result = await accept(response(
                        "duplicate", original_result=original_rejection,
                    ))
                    assert isinstance(result, Err) and result.error.code == "NO_CHANGES"

                wrong_state = AccountDeviceResponse(
                    device_id=uuid7(), display_name="Fixture", status="active",
                    client_version="1", local_schema_version=1, last_seen_at=None, version=1,
                )
                invalid = [
                    response("accepted"), response("accepted", state=wrong_state),
                    response("accepted", state=state, error=error), response("duplicate"),
                    response("rejected"), response("conflict"), response("retryable_failure"),
                    response("duplicate", original_result=OperationRecord.model_validate(
                        response("rejected").model_dump(),
                    )),
                ]
                for value in invalid:
                    try:
                        await accept(value)
                    except DAOError:
                        pass
                    else:
                        raise AssertionError("Invalid internal result produced a response")

                return {"invalid_results": len(invalid)}

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())

        self.assertEqual(result["invalid_results"], 8)


class PayloadReuseTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_previous_fingerprints_and_single_payload_selection(self):
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/operation_hashes.json").read_text(encoding="utf-8")
        )
        result = self.run_python("""
            import asyncio
            import hashlib
            from contextlib import ExitStack
            from unittest.mock import AsyncMock, patch

            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.authorization.domain.errors import AccessDenied
            from src.api.sync.application.operations_cases import accept_operation
            from src.api.sync.domain.operations import OPERATION_SCHEMAS, OperationEnvelope
            from src.core import Err

            fixture = FIXTURE
            original_sha256 = hashlib.sha256
            hashes = []
            def capture(value):
                digest = original_sha256(value)
                hashes.append(digest.hexdigest())
                return digest

            async def check():
                with patch('src.api.sync.application.operations_cases.authorized_context', new=AsyncMock(return_value=Err(AccessDenied()))), patch('src.api.sync.application.operations_cases.hashlib.sha256', side_effect=capture):
                    for vector in fixture['cases']:
                        operation = OperationEnvelope.model_validate({**fixture['envelope'], **{key: value for key, value in vector.items() if key != 'sha256'}})
                        schema = OPERATION_SCHEMAS.get(operation.action)
                        with ExitStack() as stack:
                            validate = stack.enter_context(patch.object(schema, 'model_validate', wraps=schema.model_validate)) if schema else None
                            async with AsyncSession() as db:
                                await accept_operation(db, None, None, operation, operation.operation_id)
                            if validate is not None:
                                assert validate.call_count == 1, operation.action
                        assert hashes[-1] == vector['sha256'], operation.action
                return {'compared': len(hashes)}

            print(json.dumps(asyncio.run(check())))
        """.replace("FIXTURE", repr(fixture)), self.database_settings())

        self.assertEqual(result["compared"], 48)

    def test_account_cases_reuse_the_validated_instance(self):
        result = self.run_python("""
            import asyncio
            from datetime import UTC, datetime
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7

            from src.api.accounts.application.invitations_cases import apply_invitation_operation
            from src.api.accounts.application.management_cases import apply_management_operation
            from src.api.accounts.domain.accounts import AccountPolicyPayload, MembershipStatusPayload
            from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
            from src.api.sync.domain.operations import OperationEnvelope
            from src.core import Err
            from src.core.utils.utils import Empty

            async def check():
                account_id, user_id, target = [uuid7() for _ in range(3)]
                context = SimpleNamespace(owner=True, account=SimpleNamespace(id=account_id, owner_user_id=user_id, version=1, no_show_grace_minutes=15), actor=SimpleNamespace(user_id=user_id))
                for action, schema, payload in [('UpdateAccountPolicy', AccountPolicyPayload, {'noShowGraceMinutes': 15}), ('SetMembershipStatus', MembershipStatusPayload, {'status': 'active'})]:
                    operation = OperationEnvelope(operation_id=uuid7(), contract_version=1, action=action, entity_key=account_id if action == 'UpdateAccountPolicy' else target, expected_version=1, payload=payload)
                    with patch.object(schema, 'model_validate', wraps=schema.model_validate) as validate, patch('src.api.accounts.application.management_cases.dao_accounts.get_server_time', new=AsyncMock(return_value=datetime.now(UTC))), patch('src.api.accounts.application.invitations_cases.dao_memberships.get_scoped', new=AsyncMock(return_value=Empty)):
                        data = operation.validated_payload()
                        if action == 'UpdateAccountPolicy':
                            outcome = await apply_management_operation(None, context, action, account_id, 1, data)
                            assert isinstance(outcome, Err) and outcome.error == AccountRuleError('NO_CHANGES', 1)
                        else:
                            outcome = await apply_invitation_operation(None, context, action, target, 1, data, operation.operation_id)
                            assert isinstance(outcome, Err) and isinstance(outcome.error, AccountObjectNotFound)
                        assert validate.call_count == 1, action
                return {'cases': 2}

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())

        self.assertEqual(result["cases"], 2)
