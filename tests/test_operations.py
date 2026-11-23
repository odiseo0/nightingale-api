import json
import unittest
from pathlib import Path
from uuid import uuid7

import test_foundation as foundation
from pydantic import ValidationError

from src.core.constants import MAX_BATCH_OPERATIONS
from src.api.sync.domain.operations import OperationBatch, OperationEnvelope
from src.api.sync.repository.models import ChangeLog


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
        for size in (MAX_BATCH_OPERATIONS - 1, MAX_BATCH_OPERATIONS):
            batch = OperationBatch.model_validate(
                {"operations": [self.operation() for _ in range(size)]}
            )
            self.assertEqual(len(batch.operations), size)
        for items in (
            [],
            [self.operation() for _ in range(MAX_BATCH_OPERATIONS + 1)],
        ):
            with self.assertRaises(ValidationError):
                OperationBatch.model_validate({"operations": items})


class SyncModelTests(unittest.TestCase):
    def test_change_log_model_matches_physical_schema(self):
        self.assertEqual(ChangeLog.__tablename__, "change_log")
        self.assertEqual(ChangeLog.__table__.name, "change_log")
        self.assertNotIn("change_logs", ChangeLog.metadata.tables)


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


class ClinicalResultTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_duplicate_and_get_enforce_shared_scope_and_audit(self):
        result = self.run_python("""
            import asyncio
            import hashlib
            import json
            from datetime import UTC, datetime, timedelta
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7

            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.accounts.domain.accounts import ClinicalPermissions
            from src.api.authorization.domain.errors import AccessDenied
            from src.api.clinical_records.domain.conditions import ClinicalSectionReviewResponse
            from src.api.sync.application.operations_cases import accept_operation, get_operation
            from src.api.sync.domain.operations import OperationEnvelope, OperationResult
            from src.core import Err, Ok

            async def check():
                account_id, user_id, device_id, patient_id, operation_id = [uuid7() for _ in range(5)]
                operation = OperationEnvelope.model_validate({
                    'operationId': str(operation_id), 'contractVersion': 1,
                    'action': 'SetPatientClinicalSectionReview', 'entityKey': str(patient_id),
                    'expectedVersion': 0,
                    'payload': {'section': 'allergies', 'informationStatus': 'unknown'},
                })
                state = ClinicalSectionReviewResponse(
                    patient_id=patient_id, section='allergies', information_status='unknown',
                    source_type='unknown', reviewed_by_user_id=user_id,
                    reviewed_at=datetime.now(UTC), active_count=0, version=1,
                )
                accepted = OperationResult(
                    operation_id=operation_id, status='accepted', entity_version=1,
                    state=state, error=None,
                )
                canonical = operation.model_dump(mode='json', by_alias=True)
                canonical['payload'] = operation.validated_payload().model_dump(mode='json', by_alias=True)
                fingerprint = hashlib.sha256(json.dumps(
                    canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False,
                ).encode()).digest()
                now = datetime.now(UTC)
                receipt = SimpleNamespace(
                    request_hash=fingerprint, result_json=accepted.model_dump(mode='json', by_alias=True),
                    result_expires_at=now + timedelta(days=90), clinical_section='allergies',
                    action='SetPatientClinicalSectionReview', entity_key=str(patient_id),
                )

                def context(level):
                    return SimpleNamespace(
                        owner=False, account=SimpleNamespace(id=account_id, status='active'),
                        actor=SimpleNamespace(user_id=user_id, device_id=device_id),
                        clinical_permissions=ClinicalPermissions(conditions='read_write', allergies=level),
                    )

                async def duplicate(level, audit_failure=False):
                    audit = AsyncMock(side_effect=RuntimeError('fixture') if audit_failure else None)
                    with patch('src.api.sync.application.operations_cases.authorized_context', new=AsyncMock(return_value=Ok((context(level), SimpleNamespace())))), \
                        patch('src.api.sync.application.operations_cases.dao_heads.get_server_time', new=AsyncMock(return_value=now)), \
                        patch('src.api.sync.application.operations_cases.dao_receipts.get_by', new=AsyncMock(return_value=receipt)) as read, \
                        patch('src.api.sync.application.operations_cases.record_control', new=audit):
                        async with AsyncSession() as db:
                            try:
                                outcome = await accept_operation(db, None, account_id, operation, operation_id)
                            except RuntimeError:
                                outcome = 'audit_failure'
                    return outcome, read.await_count, audit.await_count

                allowed, read_count, audit_count = await duplicate('read_write')
                assert isinstance(allowed, Ok) and allowed.value.status == 'duplicate'
                assert read_count == audit_count == 1
                denied, read_count, audit_count = await duplicate('none')
                assert isinstance(denied, Err) and isinstance(denied.error, AccessDenied)
                assert read_count == audit_count == 0
                failed, _, _ = await duplicate('read_write', True)
                assert failed == 'audit_failure'

                async def get(level):
                    with patch('src.api.sync.application.operations_cases.authorized_context', new=AsyncMock(return_value=Ok((context(level), SimpleNamespace())))), \
                        patch('src.api.sync.application.operations_cases.dao_heads.get_server_time', new=AsyncMock(return_value=now)), \
                        patch('src.api.sync.application.operations_cases.dao_receipts.get_scope', new=AsyncMock(return_value=(receipt.action, receipt.clinical_section))), \
                        patch('src.api.sync.application.operations_cases.dao_receipts.get_by', new=AsyncMock(return_value=receipt)) as read, \
                        patch('src.api.sync.application.operations_cases.record_control', new=AsyncMock()) as audit:
                        async with AsyncSession() as db:
                            outcome = await get_operation(db, None, account_id, operation_id)
                    return outcome, read.await_count, audit.await_count

                allowed, read_count, audit_count = await get('read_write')
                assert isinstance(allowed, Ok) and read_count == audit_count == 1
                denied, read_count, audit_count = await get('read')
                assert isinstance(denied, Err) and isinstance(denied.error, AccessDenied)
                assert read_count == audit_count == 0
                receipt.clinical_section = None
                for action in ('SetPatientClinicalSectionReview', 'SetPatientSexAtBirth', 'CreatePatientNote'):
                    receipt.action = action
                    for level in ('none', 'read', 'read_write'):
                        denied, read_count, audit_count = await get(level)
                        assert isinstance(denied, Err) and isinstance(denied.error, AccessDenied)
                        assert read_count == audit_count == 0, (action, level)
                # Administrative receipts need no clinical section.
                receipt.action = 'RegisterPatient'
                allowed, read_count, audit_count = await get('none')
                assert isinstance(allowed, Ok) and read_count == 1 and audit_count == 0
                return {'checks': 15}

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())
        self.assertEqual(result, {"checks": 15})


class PayloadReuseTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_legacy_permission_receipt_survives_the_new_default_section(self):
        result = self.run_python("""
            import asyncio, hashlib
            from datetime import UTC, datetime, timedelta
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.accounts.domain.accounts import ClinicalPermissions, ClinicalPermissionsPayload
            from src.api.sync.application import operations_cases as cases
            from src.api.sync.domain.operations import OperationEnvelope, OperationResult
            from src.core import Ok
            from src.core.schema import ApiError

            async def check():
                account, user, device, target, identifier = [uuid7() for _ in range(5)]
                permissions = {name: 'read_write' for name in ('clinicalProfile','conditions','allergies','encounters','notes','measurements','immunizations','antecedents')}
                envelope = dict(operationId=str(identifier), contractVersion=1, action='SetMemberClinicalPermissions', entityKey=str(target), expectedVersion=1, payload={'clinicalPermissions': permissions})
                original = OperationEnvelope.model_validate(envelope)
                legacy = original.model_dump(mode='json', by_alias=True)
                fingerprint = hashlib.sha256(json.dumps(legacy, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).digest()
                now = datetime.now(UTC)
                previous = OperationResult(operation_id=identifier, status='rejected', entity_version=2, state=None, error=ApiError(code='NO_CHANGES', message='Fixture', correlation_id=uuid7()))
                receipt = SimpleNamespace(request_hash=fingerprint, clinical_section=None, action='SetMemberClinicalPermissions', entity_key=str(target), result_json=previous.model_dump(mode='json', by_alias=True), result_expires_at=now+timedelta(days=90))
                context = SimpleNamespace(owner=True, account=SimpleNamespace(id=account, status='active'), actor=SimpleNamespace(user_id=user, device_id=device), device_status='active', clinical_permissions=ClinicalPermissions())
                statuses = []
                for level in (None, 'read_write', 'read', 'none'):
                    fields = dict(permissions)
                    if level is not None: fields['declaredMedications'] = level
                    operation = OperationEnvelope.model_validate({**envelope, 'payload': {'clinicalPermissions': fields}})
                    with patch.object(cases, 'authorized_context', new=AsyncMock(return_value=Ok((context, SimpleNamespace())))), patch.object(cases.dao_heads, 'get_server_time', new=AsyncMock(return_value=now)), patch.object(cases.dao_receipts, 'get_by', new=AsyncMock(return_value=receipt)):
                        async with AsyncSession() as db:
                            outcome = await cases.accept_operation(db, None, account, operation, uuid7())
                    assert isinstance(outcome, Ok)
                    statuses.append(outcome.value.status)
                    if level in (None, 'read_write'):
                        prior = outcome.value.original_result
                        assert prior is not None and prior.error is not None
                        assert prior.error.code == 'NO_CHANGES'
                    else:
                        error = outcome.value.error
                        assert error is not None and error.code == 'IDEMPOTENCY_CONFLICT'
                    validated = operation.validated_payload()
                    assert isinstance(validated, ClinicalPermissionsPayload)
                    assert validated.clinical_permissions.declared_medications == (level or 'read_write')
                return {'statuses': statuses}
            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())
        self.assertEqual(result['statuses'], ['duplicate', 'duplicate', 'conflict', 'conflict'])

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

    def test_correction_fingerprint_preserves_present_absent_and_null(self):
        result = self.run_python("""
            import json
            from src.api.sync.application.operations_cases import _operation_fingerprint
            from src.api.sync.domain.operations import OperationEnvelope

            base = dict(
                operationId='019a0000-0000-7000-8000-000000000001', contractVersion=1,
                action='CorrectPatientMeasurement',
                entityKey='019a0000-0000-7000-8000-000000000002', expectedVersion=1,
            )
            operations = [OperationEnvelope.model_validate({**base, 'payload': payload}) for payload in (
                {'correctionReason': 'Fixture', 'method': 'manual'},
                {'correctionReason': 'Fixture'},
                {'correctionReason': 'Fixture', 'method': None},
            )]
            current = [_operation_fingerprint(item, item.validated_payload()) for item in operations]
            legacy = [_operation_fingerprint(
                item, item.validated_payload(), legacy_correction=True
            ) for item in operations]
            assert len(set(current)) == 3
            assert len(set(legacy)) == 2
            assert legacy[1] == legacy[2]
            print(json.dumps({'current': len(set(current)), 'legacy': len(set(legacy))}))
        """, self.database_settings())
        self.assertEqual(result, {'current': 3, 'legacy': 2})

    def test_correction_receipts_keep_legacy_compatibility(self):
        result = self.run_python("""
            import asyncio
            from datetime import UTC, datetime, timedelta
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.accounts.domain.accounts import ClinicalPermissions
            from src.api.sync.application import operations_cases as cases
            from src.api.sync.domain.operations import OperationEnvelope, OperationResult
            from src.core import Ok

            async def check():
                account, user, device, measurement = [uuid7() for _ in range(4)]
                base = dict(contractVersion=1, action='CorrectPatientMeasurement',
                    entityKey=str(measurement), expectedVersion=1)
                omitted = OperationEnvelope.model_validate({**base, 'operationId': str(uuid7()),
                    'payload': {'correctionReason': 'Fixture'}})
                null = OperationEnvelope.model_validate({**base, 'operationId': str(omitted.operation_id),
                    'payload': {'correctionReason': 'Fixture', 'method': None}})
                original = OperationResult(operation_id=omitted.operation_id,
                    status='accepted', entity_version=2, state=None, error=None)
                now = datetime.now(UTC)
                receipt = SimpleNamespace(request_hash=b'', clinical_section='measurements',
                    action=omitted.action, entity_key=str(measurement),
                    result_json=original.model_dump(mode='json', by_alias=True),
                    result_expires_at=now + timedelta(days=90))
                context = SimpleNamespace(owner=True, account=SimpleNamespace(id=account, status='active'),
                    actor=SimpleNamespace(user_id=user, device_id=device),
                    clinical_permissions=ClinicalPermissions())
                outcomes = {}
                with (patch.object(cases, 'authorized_context', new=AsyncMock(return_value=Ok((context, SimpleNamespace())))),
                      patch.object(cases, 'record_control', new=AsyncMock()),
                      patch.object(cases, 'apply_measurement_operation', new=AsyncMock()) as effect,
                      patch.object(cases.dao_heads, 'get_server_time', new=AsyncMock(return_value=now)),
                      patch.object(cases.dao_receipts, 'get_by', new=AsyncMock(return_value=receipt))):
                    for label, fingerprint in (
                        ('legacy', cases._operation_fingerprint(omitted, omitted.validated_payload(), legacy_correction=True)),
                        ('current', cases._operation_fingerprint(omitted, omitted.validated_payload())),
                    ):
                        receipt.request_hash = fingerprint
                        statuses = []
                        for operation in (omitted, null):
                            async with AsyncSession() as db:
                                result = await cases.accept_operation(db, None, account, operation, uuid7())
                            assert isinstance(result, Ok)
                            statuses.append(result.value.status)
                        outcomes[label] = statuses
                    effect.assert_not_awaited()
                return outcomes

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())
        self.assertEqual(result, {'legacy': ['duplicate', 'duplicate'],
                                  'current': ['duplicate', 'conflict']})

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
                    with patch.object(schema, 'model_validate', wraps=schema.model_validate) as validate, patch('src.api.accounts.application.management_cases.dao_accounts.get_server_time', new=AsyncMock(return_value=datetime.now(UTC))), patch('src.api.accounts.application.invitations_cases.dao_memberships.get_by', new=AsyncMock(return_value=Empty)):
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


class AdministrativePolicyTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_all_owner_actions_deny_assistants_before_receipt_lookup(self):
        result = self.run_python("""
            import asyncio
            from datetime import UTC, datetime
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.accounts.domain.accounts import ClinicalPermissions
            from src.api.authorization.domain.errors import AccessDenied
            from src.api.sync.application import operations_cases as cases
            from src.api.sync.domain.operations import OperationEnvelope
            from src.core import Err, Ok

            class ReachedReceipt(Exception):
                pass

            async def check():
                actions = 'CreateInvitation RevokeInvitation SetMembershipStatus SetMemberClinicalPermissions UpdateAccountDetails UpdateAccountPolicy SetAccountStatus RevokeAccountDevice RestoreAccountDevice UpdateProfessionalProfile CreateService UpdateService SetServiceStatus OfferService UpdateServiceOffer SetServiceOfferStatus'.split()
                account_id, user_id, device_id = [uuid7() for _ in range(3)]
                for owner in (False, True):
                    context = SimpleNamespace(owner=owner,
                        actor=SimpleNamespace(user_id=user_id, device_id=device_id),
                        account=SimpleNamespace(id=account_id, status='active'),
                        device_status='active', clinical_permissions=ClinicalPermissions())
                    for action in actions:
                        operation = OperationEnvelope(operation_id=uuid7(), contract_version=1,
                            action=action, entity_key=uuid7(), expected_version=0, payload={})
                        with patch.object(cases, 'authorized_context', new=AsyncMock(return_value=Ok((context, SimpleNamespace())))), \
                            patch.object(cases.dao_heads, 'get_server_time', new=AsyncMock(return_value=datetime.now(UTC))), \
                            patch.object(cases.dao_receipts, 'get_by', new=AsyncMock(side_effect=ReachedReceipt)) as read:
                            async with AsyncSession() as db:
                                try:
                                    outcome = await cases.accept_operation(db, None, account_id, operation, uuid7())
                                except ReachedReceipt:
                                    assert owner and read.await_count == 1, action
                                else:
                                    assert not owner and isinstance(outcome, Err)
                                    assert isinstance(outcome.error, AccessDenied) and read.await_count == 0, action
                return {'role_checks': len(actions) * 2}
            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())
        self.assertEqual(result, {'role_checks': 32})
