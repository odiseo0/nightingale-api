from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import timedelta
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid7

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import (
    account_context,
    register_own_device,
)
from src.api.accounts.application.invitations_cases import (
    apply_invitation_operation,
    invitation_context,
    invitation_target,
)
from src.api.accounts.application.management_cases import (
    apply_management_operation,
    lock_professional,
)
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    InvitationAcceptanceResult,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
    DeviceAlreadyRegistered,
    DeviceVersionConflict,
)
from src.api.appointments.application.appointments_cases import (
    apply_appointment_operation,
)
from src.api.appointments.application.schedule_changes import apply_schedule_change
from src.api.audit.application.audit_cases import record_operation
from src.api.audit.domain.audit import OperationAudit
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.patients.application.contacts_cases import (
    apply_contact_operation,
)
from src.api.patients.application.patients_cases import (
    apply_patient_operation,
)
from src.api.schedule.application.blocks_cases import (
    block_permission,
    block_projection_accounts,
)
from src.api.services.application.offers_cases import (
    apply_offer_operation,
)
from src.api.services.application.services_cases import (
    apply_service_operation,
    service_permission,
    service_projection_accounts,
)
from src.api.services.domain.offers import ServiceOfferResponse
from src.api.sync.domain.errors import OperationNotFound, ResultExpired
from src.api.sync.domain.operations import (
    APPOINTMENT_SCHEMAS,
    BLOCK_SCHEMAS,
    CONTACT_SCHEMAS,
    EXCEPTION_SCHEMAS,
    OFFER_SCHEMAS,
    RULE_SCHEMAS,
    SERVICE_SCHEMAS,
    OperationBatch,
    OperationBatchResult,
    OperationEnvelope,
    OperationRecord,
    OperationResult,
    OperationState,
)
from src.api.sync.repository.dao import dao_changes, dao_heads, dao_receipts
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.schema import ApiError
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.sync.repository.models import AccountSyncHead


def operation_result(
    operation_id: UUID,
    correlation_id: UUID,
    status: Literal["accepted", "conflict", "rejected", "retryable_failure"],
    code: str | None = None,
    version: int | None = None,
    state: OperationState | Mapping[str, object] | None = None,
) -> OperationResult:
    try:
        return OperationResult(
            operation_id=operation_id,
            status=status,
            entity_version=version,
            state=state,
            error=None
            if code is None
            else ApiError(
                code=code,
                message="No se puede completar la operación",
                correlation_id=correlation_id,
                details=[],
            ),
        )
    except ValidationError as error:
        raise DAOError("El resultado no cumple su esquema") from error


async def authorized_context(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID | None,
    registration: bool = False,
    invitation_id: UUID | None = None,
    allow_inactive: bool = False,
    related_device_id: UUID | None = None,
    professional: bool = False,
    catalog: bool = False,
    entity_key=None,
    own_service: bool = False,
    blocks: bool = False,
) -> Result[
    tuple[AccountContext, AccountSyncHead],
    InvalidCredential | AccountNotFound | AccountObjectNotFound | AccessDenied,
]:
    identity = await authenticate(db, credential, related_device_id=related_device_id)

    match identity:
        case Ok(actor):
            pass
        case Err(error):
            return Err(error)

    if invitation_id is not None:
        target = await invitation_target(db, actor, invitation_id)

        if isinstance(target, Err):
            return target

        account_id = target.value

    # Identity first, then account control, business rows and receipt. Refresh
    # after waiting: another writer may have changed this account's access.
    # https://www.postgresql.org/docs/18/explicit-locking.html#LOCKING-ROWS
    if professional or catalog or blocks:
        await lock_professional(db, account_id)

    if catalog:
        targets = await service_projection_accounts(db, actor, account_id, entity_key)

        for target in targets:
            await dao_heads.lock_account(db, target)

    if blocks:
        for target in await block_projection_accounts(db, actor, account_id):
            await dao_heads.lock_account(db, target)

    head = await dao_heads.lock_account(db, account_id)

    if head is Empty:
        return Err(AccountNotFound(account_id))

    permission = (
        await invitation_context(db, actor, account_id, invitation_id)
        if invitation_id is not None
        else await account_context(
            db, actor, account_id, require_device=not registration
        )
    )

    match permission:
        case Ok(context):
            pass
        case Err(error):
            return Err(error)

    if (
        context.account.status != "active" and not (allow_inactive and context.owner)
    ) or context.device_status == "revoked":
        return Err(AccessDenied())

    if own_service:
        permission = await service_permission(db, context)

        if isinstance(permission, Err):
            return permission

    return Ok((context, head))


async def accept_operation(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID | None,
    operation: OperationEnvelope,
    correlation_id: UUID,
    *,
    internal_invitation: bool = False,
) -> Result[
    OperationResult,
    InvalidCredential
    | AccountNotFound
    | AccountObjectNotFound
    | AccountRuleError
    | AccessDenied
    | ResultExpired,
]:
    canonical = operation.model_dump(mode="json", by_alias=True)
    payload = operation.validated_payload()

    if payload is not None:
        canonical["payload"] = payload.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=operation.action.startswith("Update"),
        )

    fingerprint = hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).digest()

    async with transaction(db):
        scope = await authorized_context(
            db,
            credential,
            account_id,
            registration=operation.action == "RegisterAccountDevice",
            invitation_id=operation.entity_key if internal_invitation else None,
            allow_inactive=operation.action == "SetAccountStatus",
            related_device_id=operation.entity_key
            if isinstance(operation.entity_key, UUID)
            and operation.action in ("RevokeAccountDevice", "RestoreAccountDevice")
            else None,
            professional=operation.action in RULE_SCHEMAS
            or operation.action in APPOINTMENT_SCHEMAS
            or operation.action in EXCEPTION_SCHEMAS
            or operation.action in OFFER_SCHEMAS
            or operation.action
            in ("UpdateAccountDetails", "UpdateProfessionalProfile"),
            catalog=operation.action in SERVICE_SCHEMAS,
            entity_key=operation.entity_key,
            own_service=operation.action in SERVICE_SCHEMAS
            or operation.action in OFFER_SCHEMAS,
            blocks=operation.action in BLOCK_SCHEMAS,
        )

        match scope:
            case Ok((context, head)):
                pass
            case Err(error):
                return Err(error)

        actor = context.actor
        account_id = context.account.id

        if operation.action in BLOCK_SCHEMAS and isinstance(operation.entity_key, UUID):
            permission = await block_permission(db, context, operation.entity_key)

            if isinstance(permission, Err):
                return permission

        if (
            operation.action in SERVICE_SCHEMAS
            or operation.action in OFFER_SCHEMAS
            or operation.action
            in (
                "CreateInvitation",
                "RevokeInvitation",
                "SetMembershipStatus",
                "UpdateAccountDetails",
                "UpdateAccountPolicy",
                "SetAccountStatus",
                "RevokeAccountDevice",
                "RestoreAccountDevice",
                "UpdateProfessionalProfile",
            )
        ) and not context.owner:
            return Err(AccessDenied())

        if (
            operation.action == "RegisterAccountDevice"
            and context.device_status is None
            and operation.entity_key != actor.device_id
        ):
            return Err(AccessDenied())

        now = await dao_heads.get_server_time(db)
        receipt = await dao_receipts.get_scoped(
            db, account_id, actor.user_id, operation.operation_id
        )

        if receipt is not Empty:
            if receipt.request_hash != fingerprint:
                return Ok(
                    operation_result(
                        operation.operation_id,
                        correlation_id,
                        "conflict",
                        "IDEMPOTENCY_CONFLICT",
                    )
                )

            if receipt.result_json is None or now >= receipt.result_expires_at:
                return Err(ResultExpired())

            original = OperationRecord.model_validate(receipt.result_json)

            return Ok(
                OperationResult(
                    operation_id=operation.operation_id,
                    status="duplicate",
                    entity_version=original.entity_version,
                    state=original.state,
                    error=original.error,
                    original_result=original,
                )
            )

        # A new installation can read its own past receipt only when already
        # authorized; it cannot use registration to inspect another device.
        if (
            operation.action == "RegisterAccountDevice"
            and operation.entity_key != actor.device_id
        ):
            return Err(AccessDenied())

        result = None

        for dependency in operation.depends_on:
            previous = await dao_receipts.get_scoped(
                db, account_id, actor.user_id, dependency
            )

            if previous is Empty or previous.status != "accepted":
                result = operation_result(
                    operation.operation_id,
                    correlation_id,
                    "rejected",
                    "DEPENDENCY_FAILED",
                )
                break

        entity_type = {
            "RegisterAccountDevice": "account_device",
            "CreateInvitation": "invitation",
            "RevokeInvitation": "invitation",
            "SetMembershipStatus": "membership",
            "UpdateAccountDetails": "account",
            "UpdateAccountPolicy": "account",
            "SetAccountStatus": "account",
            "UpdateProfessionalProfile": "professional",
            "RevokeAccountDevice": "account_device",
            "RestoreAccountDevice": "account_device",
            "RegisterPatient": "patient_profile",
            "UpdatePatientProfile": "patient_profile",
            "SetPatientProfileStatus": "patient_profile",
            "SetPatientCompletion": "patient_profile",
            "AddPatientIdentifier": "patient_identifier",
        }.get(operation.action, "invitation" if internal_invitation else "unknown")
        changes = []
        permission_changed = True

        if operation.action in CONTACT_SCHEMAS:
            entity_type = (
                "patient_contact"
                if "Relationship" in operation.action
                else "contact_person"
            )

        if operation.action in SERVICE_SCHEMAS:
            entity_type = "service"

        if operation.action in OFFER_SCHEMAS:
            entity_type = "service_offer"

        if operation.action in RULE_SCHEMAS:
            entity_type = "schedule_rule"

        if operation.action in EXCEPTION_SCHEMAS:
            entity_type = "schedule_exception"

        if operation.action in BLOCK_SCHEMAS:
            entity_type = "schedule_block"

        if operation.action in APPOINTMENT_SCHEMAS:
            entity_type = "appointment"

        if result is None:
            if (
                operation.action in RULE_SCHEMAS
                or operation.action in EXCEPTION_SCHEMAS
                or operation.action in BLOCK_SCHEMAS
                or operation.action in APPOINTMENT_SCHEMAS
                or operation.action in OFFER_SCHEMAS
                or operation.action in SERVICE_SCHEMAS
                or operation.action in CONTACT_SCHEMAS
                or operation.action
                in (
                    "CreateInvitation",
                    "RevokeInvitation",
                    "SetMembershipStatus",
                    "UpdateAccountDetails",
                    "UpdateAccountPolicy",
                    "SetAccountStatus",
                    "RevokeAccountDevice",
                    "RestoreAccountDevice",
                    "UpdateProfessionalProfile",
                    "RegisterPatient",
                    "UpdatePatientProfile",
                    "SetPatientProfileStatus",
                    "SetPatientCompletion",
                    "AddPatientIdentifier",
                )
                or internal_invitation
            ):
                if operation.action in APPOINTMENT_SCHEMAS:
                    effect = await apply_appointment_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif (
                    operation.action in BLOCK_SCHEMAS
                    or operation.action in EXCEPTION_SCHEMAS
                    or operation.action in RULE_SCHEMAS
                    or operation.action == "UpdateAccountDetails"
                ):
                    effect = await apply_schedule_change(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif operation.action in OFFER_SCHEMAS:
                    effect = await apply_offer_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif operation.action in SERVICE_SCHEMAS:
                    effect = await apply_service_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif operation.action in CONTACT_SCHEMAS:
                    effect = await apply_contact_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif operation.action in (
                    "RegisterPatient",
                    "UpdatePatientProfile",
                    "SetPatientProfileStatus",
                    "SetPatientCompletion",
                    "AddPatientIdentifier",
                ):
                    effect = await apply_patient_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )
                elif (
                    operation.action
                    in ("CreateInvitation", "RevokeInvitation", "SetMembershipStatus")
                    or internal_invitation
                ):
                    effect = await apply_invitation_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                        operation.operation_id,
                    )
                else:
                    effect = await apply_management_operation(
                        db,
                        context,
                        operation.action,
                        operation.entity_key,
                        operation.expected_version,
                        payload,
                    )

                match effect:
                    case Ok(value):
                        result = operation_result(
                            operation.operation_id,
                            correlation_id,
                            "accepted",
                            version=value.version,
                            state=value.state,
                        )
                        changes = value.changes
                        permission_changed = value.permission_changed
                    case Err(AccountRuleError(code, version)):
                        if internal_invitation:
                            # F41 needs membership. A rejected initial acceptance
                            # must not create membership only to store a receipt.
                            return effect

                        result = operation_result(
                            operation.operation_id,
                            correlation_id,
                            "conflict"
                            if code in ("VERSION_CONFLICT", "SLOT_UNAVAILABLE")
                            else "rejected",
                            code,
                            version=version,
                        )
                    case Err(error):
                        return Err(error)
            elif operation.action != "RegisterAccountDevice":
                result = operation_result(
                    operation.operation_id,
                    correlation_id,
                    "rejected",
                    "UNSUPPORTED_OPERATION",
                )
            elif payload is None:
                result = operation_result(
                    operation.operation_id,
                    correlation_id,
                    "rejected",
                    "VALIDATION_ERROR",
                )
            else:
                effect = await register_own_device(
                    db, context, operation.entity_key, operation.expected_version
                )

                match effect:
                    case Ok(state):
                        result = operation_result(
                            operation.operation_id,
                            correlation_id,
                            "accepted",
                            version=state.version,
                            state=state,
                        )
                        changes = [
                            AccountChange(
                                entity_type,
                                canonical["entityKey"],
                                state,
                                state.version,
                            )
                        ]
                    case Err(DeviceVersionConflict(version)):
                        result = operation_result(
                            operation.operation_id,
                            correlation_id,
                            "conflict",
                            "VERSION_CONFLICT",
                            version=version,
                        )
                    case Err(DeviceAlreadyRegistered(version)):
                        result = operation_result(
                            operation.operation_id,
                            correlation_id,
                            "rejected",
                            "NO_CHANGES",
                            version=version,
                        )
                    case Err(error):
                        return Err(error)

        await dao_receipts.record(
            db,
            {
                "account_id": account_id,
                "actor_user_id": actor.user_id,
                "operation_id": operation.operation_id,
                "source_device_id": actor.device_id,
                "contract_version": operation.contract_version,
                "action": operation.action,
                "entity_type": entity_type,
                "entity_key": canonical["entityKey"],
                "request_hash": fingerprint,
                "status": result.status,
                "entity_version": result.entity_version,
                "result_json": result.model_dump(
                    mode="json", by_alias=True, exclude_unset=True
                ),
                "completed_at": now,
                "result_expires_at": now + timedelta(days=90),
                "purged_at": None,
            },
            commit=False,
        )
        await record_operation(
            db,
            OperationAudit(
                account_id=account_id,
                actor_user_id=actor.user_id,
                actor_device_id=actor.device_id,
                action=operation.action,
                object_type=entity_type,
                object_key=canonical["entityKey"],
                outcome=result.status,
                operation_id=operation.operation_id,
                correlation_id=correlation_id,
                occurred_at=now,
            ),
        )

        if result.status == "accepted":
            targets = sorted({change.account_id or account_id for change in changes})
            group_id = uuid7()

            for target in targets:
                target_head = (
                    head
                    if target == account_id
                    else await dao_heads.lock_account(db, target)
                )
                sequence = await dao_heads.advance(
                    db,
                    target_head,
                    now,
                    permission_changed=permission_changed,
                    commit=False,
                )
                group = [
                    change
                    for change in changes
                    if (change.account_id or account_id) == target
                ]

                for ordinal, change in enumerate(group, 1):
                    try:
                        projection = (
                            ServiceOfferResponse.model_validate(change.state)
                            if isinstance(change.state, Mapping)
                            else change.state
                        ).model_dump(mode="json", by_alias=True)
                    except ValidationError as error:
                        raise DAOError("La proyección no cumple su esquema") from error

                    await dao_changes.append(
                        db,
                        {
                            "account_id": target,
                            "sequence": sequence,
                            "ordinal": ordinal,
                            "group_id": group_id,
                            "group_size": len(group),
                            "source_account_id": account_id,
                            "actor_user_id": actor.user_id,
                            "operation_id": operation.operation_id,
                            "entity_type": change.entity_type,
                            "entity_key": change.entity_key,
                            "entity_version": change.version,
                            "change_kind": "upsert",
                            "audience": change.audience,
                            "projection_json": projection,
                            "previous_starts_at": change.previous_starts_at,
                            "previous_ends_at": change.previous_ends_at,
                            "accepted_at": now,
                        },
                        commit=False,
                    )

    return Ok(result)


async def accept_invitation(
    db: AsyncSession,
    credential: str | None,
    invitation_id: UUID,
    operation_id: UUID,
    correlation_id: UUID,
) -> Result[
    InvitationAcceptanceResult,
    InvalidCredential
    | AccountNotFound
    | AccountObjectNotFound
    | AccountRuleError
    | AccessDenied
    | ResultExpired,
]:
    envelope = OperationEnvelope(
        operation_id=operation_id,
        contract_version=1,
        action="AcceptInvitation",
        entity_key=invitation_id,
        expected_version=0,
        payload={},
    )

    result = await accept_operation(
        db, credential, None, envelope, correlation_id, internal_invitation=True
    )

    if isinstance(result, Err):
        return result

    response = result.value
    original = response.original_result if response.status == "duplicate" else response

    if original is None:
        raise DAOError("El resultado duplicado no conserva su resultado original")

    if original.status != "accepted":
        if original.error is None:
            raise DAOError("El resultado fallido no conserva su error")

        return Err(AccountRuleError(original.error.code, original.entity_version))

    if original.error is not None or not isinstance(
        original.state, InvitationAcceptanceResult
    ):
        raise DAOError("El resultado no conserva la aceptación de invitación")

    return Ok(original.state.model_copy(update={"status": response.status}))


async def submit_batch(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    batch: OperationBatch,
    correlation_id: UUID,
) -> Result[
    OperationBatchResult,
    InvalidCredential | AccountNotFound | AccessDenied | ResultExpired,
]:
    results = []
    temporary = set()

    for operation in batch.operations:
        try:
            if temporary.intersection(operation.depends_on):
                # Still authenticate this request; a prior temporal failure does
                # not turn into a permanent dependency rejection.
                async with transaction(db):
                    scope = await authorized_context(
                        db,
                        credential,
                        account_id,
                        operation.action == "RegisterAccountDevice",
                    )

                    if isinstance(scope, Err):
                        return scope

                result = Ok(
                    operation_result(
                        operation.operation_id,
                        correlation_id,
                        "retryable_failure",
                        "TEMPORARY_FAILURE",
                    )
                )
            else:
                result = await accept_operation(
                    db, credential, account_id, operation, correlation_id
                )
        except DAOError, OSError, TimeoutError:
            result = Ok(
                operation_result(
                    operation.operation_id,
                    correlation_id,
                    "retryable_failure",
                    "TEMPORARY_FAILURE",
                )
            )

        match result:
            case Ok(response):
                results.append(response)

                if response.status == "retryable_failure":
                    temporary.add(operation.operation_id)
            case Err(error):
                return Err(error)

    return Ok(OperationBatchResult(results=results, correlation_id=correlation_id))


async def get_operation(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    operation_id: UUID,
) -> Result[
    OperationResult,
    InvalidCredential
    | AccountNotFound
    | AccessDenied
    | OperationNotFound
    | ResultExpired,
]:
    async with transaction(db):
        scope = await authorized_context(
            db, credential, account_id, allow_inactive=True
        )

        match scope:
            case Ok((context, _)):
                pass
            case Err(error):
                return Err(error)
        receipt = await dao_receipts.get_scoped(
            db, account_id, context.actor.user_id, operation_id
        )

        if receipt is Empty:
            return Err(OperationNotFound())

        if context.account.status != "active" and receipt.action != "SetAccountStatus":
            return Err(AccessDenied())

        if receipt.action in SERVICE_SCHEMAS or receipt.action in OFFER_SCHEMAS:
            permission = await service_permission(db, context)

            if isinstance(permission, Err):
                return permission

        if receipt.action in BLOCK_SCHEMAS and isinstance(receipt.entity_key, str):
            permission = await block_permission(db, context, UUID(receipt.entity_key))

            if isinstance(permission, Err):
                return Err(AccessDenied())

        now = await dao_heads.get_server_time(db)

        if receipt.result_json is None or now >= receipt.result_expires_at:
            return Err(ResultExpired())

        response = OperationResult.model_validate(receipt.result_json)

    return Ok(response)
