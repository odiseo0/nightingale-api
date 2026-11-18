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
    ClinicalPermissionsPayload,
    InvitationAcceptanceResult,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
    DeviceAlreadyRegistered,
    DeviceVersionConflict,
)
from src.api.accounts.domain.policies import operation_policies
from src.api.appointments.application.appointments_cases import (
    apply_appointment_operation,
)
from src.api.appointments.application.schedule_changes import apply_schedule_change
from src.api.audit.application.audit_cases import record_control, record_operation
from src.api.audit.domain.audit import ControlAudit, OperationAudit
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.access_cases import (
    clinical_result_allowed,
    clinical_result_section,
)
from src.api.clinical_records.application.allergies_cases import apply_allergy_operation
from src.api.clinical_records.application.antecedents_cases import (
    apply_antecedent_operation,
)
from src.api.clinical_records.application.clinical_cases import apply_clinical_operation
from src.api.clinical_records.application.conditions_cases import (
    apply_condition_operation,
)
from src.api.clinical_records.application.immunizations_cases import (
    apply_immunization_operation,
)
from src.api.care_plans.application.plan_cases import apply_care_plan_operation
from src.api.diagnostic_results.application.report_cases import apply_diagnostic_operation
from src.api.specialties.application.odontogram_cases import apply_dental_operation
from src.api.specialties.application.template_cases import apply_specialty_operation
from src.api.medications.application.medication_cases import (
    apply_declared_medication_operation,
)
from src.api.clinical_records.application.measurements_cases import (
    apply_measurement_operation,
)
from src.api.clinical_records.application.notes_cases import apply_note_operation
from src.api.clinical_records.domain.conditions import (
    SetPatientClinicalSectionReviewPayload,
)
from src.api.encounters.application.encounters_cases import apply_encounter_operation
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
    ALLERGY_SCHEMAS,
    ANTECEDENT_SCHEMAS,
    APPOINTMENT_SCHEMAS,
    BLOCK_SCHEMAS,
    CONDITION_SCHEMAS,
    CONTACT_SCHEMAS,
    ENCOUNTER_SCHEMAS,
    EXCEPTION_SCHEMAS,
    IMMUNIZATION_SCHEMAS,
    MEDICATION_SCHEMAS,
    CARE_PLAN_SCHEMAS,
    DIAGNOSTIC_SCHEMAS,
    SPECIALTY_SCHEMAS,
    DENTAL_SCHEMAS,
    MEASUREMENT_SCHEMAS,
    NOTE_SCHEMAS,
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
        # Keep pre-medication/pre-care-plan receipts and explicit/default read_write equivalent.
        legacy_permissions = (
            isinstance(payload, ClinicalPermissionsPayload)
            and payload.clinical_permissions.declared_medications == "read_write"
            and payload.clinical_permissions.care_plans == "read_write"
            and payload.clinical_permissions.diagnostic_reports == "read_write"
            and payload.clinical_permissions.specialty_templates == "read_write"
            and payload.clinical_permissions.specialty_templates == "read_write"
        )
        canonical["payload"] = payload.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=operation.action.startswith("Update"),
            exclude={"clinical_permissions": {"declared_medications", "care_plans", "diagnostic_reports", "specialty_templates"}}
            if legacy_permissions else None,
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
        policy = operation_policies().get(operation.action)
        object_rule = None if policy is None else policy.object_rule
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
            or object_rule == "own_offer"
            or operation.action == "UpdateAccountDetails"
            or object_rule == "own_professional",
            catalog=object_rule == "own_catalog",
            entity_key=operation.entity_key,
            own_service=object_rule in ("own_catalog", "own_offer"),
            blocks=object_rule == "block",
        )

        match scope:
            case Ok((context, head)):
                pass
            case Err(error):
                return Err(error)

        actor = context.actor
        account_id = context.account.id
        clinical_section = clinical_result_section(operation.action, payload)

        if clinical_section is not None and not clinical_result_allowed(
            context, clinical_section
        ):
            return Err(AccessDenied())

        if object_rule == "block" and isinstance(operation.entity_key, UUID):
            permission = await block_permission(db, context, operation.entity_key)

            if isinstance(permission, Err):
                return permission

        if policy is not None and policy.owner_only and not context.owner:
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
            if (
                clinical_section is not None
                and receipt.clinical_section != clinical_section
            ):
                return Err(AccessDenied())

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

            if clinical_section is not None:
                await record_control(
                    db,
                    ControlAudit(
                        account_id=account_id,
                        actor_user_id=actor.user_id,
                        actor_device_id=actor.device_id,
                        action="ReadOperationResult",
                        object_type="operation_result",
                        object_key=str(operation.operation_id),
                        outcome="accepted",
                        correlation_id=correlation_id,
                        occurred_at=now,
                    ),
                )

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
            "SetMemberClinicalPermissions": "membership",
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
            "SetPatientSexAtBirth": "patient_clinical_profile",
            "CreatePatientCondition": "patient_condition",
            "UpdatePatientCondition": "patient_condition",
            "InvalidatePatientCondition": "patient_condition",
            "SetPatientClinicalSectionReview": "patient_clinical_section_review",
            "CreatePatientAllergyIntolerance": "patient_allergy_intolerance",
            "UpdatePatientAllergyIntolerance": "patient_allergy_intolerance",
            "InvalidatePatientAllergyIntolerance": "patient_allergy_intolerance",
            "CreatePatientEncounter": "clinical_encounter",
            "UpdatePatientEncounter": "clinical_encounter",
            "InvalidatePatientEncounter": "clinical_encounter",
            "CreatePatientNote": "patient_note",
            "UpdatePatientNote": "patient_note",
            "InvalidatePatientNote": "patient_note",
            "RecordPatientMeasurement": "patient_measurement",
            "CorrectPatientMeasurement": "patient_measurement",
            "InvalidatePatientMeasurement": "patient_measurement",
            "RecordPatientImmunization": "patient_immunization",
            "UpdatePatientImmunization": "patient_immunization",
            "InvalidatePatientImmunization": "patient_immunization",
            "CreatePatientAntecedent": "patient_antecedent",
            "UpdatePatientAntecedent": "patient_antecedent",
            "InvalidatePatientAntecedent": "patient_antecedent",
            "DeclarePatientMedication": "declared_medication",
            "CreatePatientCarePlan": "care_plan",
            "UpdatePatientCarePlan": "care_plan",
            "InvalidatePatientCarePlan": "care_plan",
            "AddCarePlanGoal": "care_plan_goal",
            "UpdateCarePlanGoal": "care_plan_goal",
            "EvaluateCarePlanGoal": "care_plan_goal",
            "InvalidateCarePlanGoal": "care_plan_goal",
            "AddCarePlanAction": "care_plan_action",
            "UpdateCarePlanAction": "care_plan_action",
            "CompleteCarePlanAction": "care_plan_action",
            "InvalidateCarePlanAction": "care_plan_action",
            "AddCarePlanReview": "care_plan_review",
            "InvalidateCarePlanReview": "care_plan_review",
            "CreateDiagnosticReport": "diagnostic_report",
            "UpdateDiagnosticReport": "diagnostic_report",
            "CorrectDiagnosticReport": "diagnostic_report",
            "AddDiagnosticReportResult": "diagnostic_report_result",
            "UpdateDiagnosticReportResult": "diagnostic_report_result",
            "InvalidateDiagnosticReportResult": "diagnostic_report_result",
            "UploadReportAttachment": "report_attachment",
            "InvalidateReportAttachment": "report_attachment",
            "CreateSpecialtyTemplate": "specialty_template",
            "UpdateSpecialtyTemplate": "specialty_template",
            "RetireSpecialtyTemplate": "specialty_template",
            "CaptureSpecialtyRecord": "specialty_record",
            "UpdateSpecialtyRecord": "specialty_record",
            "InvalidateSpecialtyRecord": "specialty_record",
            "RecordDentalFinding": "dental_finding",
            "UpdateDentalFinding": "dental_finding",
            "ResolveDentalFinding": "dental_finding",
            "InvalidateDentalFinding": "dental_finding",
            "AddDentalTreatment": "dental_treatment",
            "UpdateDentalTreatment": "dental_treatment",
            "InvalidateDentalTreatment": "dental_treatment",
            "UpdatePatientDeclaredMedication": "declared_medication",
            "ReviewPatientDeclaredMedication": "declared_medication",
            "InvalidatePatientDeclaredMedication": "declared_medication",
        }.get(operation.action, "invitation" if internal_invitation else "unknown")
        changes = []
        permission_changed = policy is not None and policy.changes_scope

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
                or operation.action in CONDITION_SCHEMAS
                or operation.action in ALLERGY_SCHEMAS
                or operation.action in ENCOUNTER_SCHEMAS
                or operation.action in NOTE_SCHEMAS
                or operation.action in MEASUREMENT_SCHEMAS
                or operation.action in IMMUNIZATION_SCHEMAS
                or operation.action in ANTECEDENT_SCHEMAS
                or operation.action in MEDICATION_SCHEMAS
                or operation.action in CARE_PLAN_SCHEMAS
                or operation.action in DIAGNOSTIC_SCHEMAS
                or operation.action in SPECIALTY_SCHEMAS
                or operation.action in DENTAL_SCHEMAS
                or operation.action in OFFER_SCHEMAS
                or operation.action in SERVICE_SCHEMAS
                or operation.action in CONTACT_SCHEMAS
                or operation.action
                in (
                    "CreateInvitation",
                    "RevokeInvitation",
                    "SetMembershipStatus",
                    "SetMemberClinicalPermissions",
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
                    "SetPatientSexAtBirth",
                )
                or internal_invitation
            ):
                if (
                    operation.action in CONDITION_SCHEMAS
                    or operation.action in ALLERGY_SCHEMAS
                    or operation.action in ENCOUNTER_SCHEMAS
                    or operation.action in NOTE_SCHEMAS
                    or operation.action in MEASUREMENT_SCHEMAS
                    or operation.action in IMMUNIZATION_SCHEMAS
                    or operation.action in ANTECEDENT_SCHEMAS
                    or operation.action == "SetPatientSexAtBirth"
                ) and not isinstance(operation.entity_key, UUID):
                    return Err(AccountRuleError("VALIDATION_ERROR"))

                apply_condition = (
                    apply_allergy_operation
                    if operation.action == "SetPatientClinicalSectionReview"
                    and isinstance(payload, SetPatientClinicalSectionReviewPayload)
                    and payload.section == "allergies"
                    else apply_condition_operation
                )
                handlers = (
                    (
                        APPOINTMENT_SCHEMAS,
                        lambda: apply_appointment_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        ),
                    ),
                    (
                        set(BLOCK_SCHEMAS)
                        | set(EXCEPTION_SCHEMAS)
                        | set(RULE_SCHEMAS)
                        | {"UpdateAccountDetails"},
                        lambda: apply_schedule_change(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        ),
                    ),
                    (
                        OFFER_SCHEMAS,
                        lambda: apply_offer_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        ),
                    ),
                    (
                        SERVICE_SCHEMAS,
                        lambda: apply_service_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        ),
                    ),
                    (
                        CONTACT_SCHEMAS,
                        lambda: apply_contact_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        ),
                    ),
                    (
                        ANTECEDENT_SCHEMAS,
                        lambda: apply_antecedent_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        IMMUNIZATION_SCHEMAS,
                        lambda: apply_immunization_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        DENTAL_SCHEMAS,
                        lambda: apply_dental_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        SPECIALTY_SCHEMAS,
                        lambda: apply_specialty_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        DIAGNOSTIC_SCHEMAS,
                        lambda: apply_diagnostic_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        CARE_PLAN_SCHEMAS,
                        lambda: apply_care_plan_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        MEDICATION_SCHEMAS,
                        lambda: apply_declared_medication_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        MEASUREMENT_SCHEMAS,
                        lambda: apply_measurement_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                            operation.occurred_at_local,
                        ),
                    ),
                    (
                        NOTE_SCHEMAS,
                        lambda: apply_note_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        ENCOUNTER_SCHEMAS,
                        lambda: apply_encounter_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                            operation.occurred_at_local,
                        ),
                    ),
                    (
                        ALLERGY_SCHEMAS,
                        lambda: apply_allergy_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        CONDITION_SCHEMAS,
                        lambda: apply_condition(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        {"SetPatientSexAtBirth"},
                        lambda: apply_clinical_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                    (
                        {
                            "RegisterPatient",
                            "UpdatePatientProfile",
                            "SetPatientProfileStatus",
                            "SetPatientCompletion",
                            "AddPatientIdentifier",
                        },
                        lambda: apply_patient_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        ),
                    ),
                )

                for catalog, handle in handlers:
                    if operation.action in catalog:
                        effect = await handle()
                        break
                else:
                    effect = await (
                        apply_invitation_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                            operation.operation_id,
                        )
                        if operation.action
                        in (
                            "CreateInvitation",
                            "RevokeInvitation",
                            "SetMembershipStatus",
                            "SetMemberClinicalPermissions",
                        )
                        or internal_invitation
                        else apply_management_operation(
                            db,
                            context,
                            operation.action,
                            operation.entity_key,
                            operation.expected_version,
                            payload,
                        )
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
                "clinical_section": clinical_result_section(operation.action, payload),
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
        result_scope = await dao_receipts.get_scope(
            db, account_id, context.actor.user_id, operation_id
        )

        if result_scope is Empty:
            return Err(OperationNotFound())

        action, clinical_section = result_scope

        if action == "SetMemberClinicalPermissions" and not context.owner:
            return Err(AccessDenied())

        if context.account.status != "active" and action != "SetAccountStatus":
            return Err(AccessDenied())

        # Old clinical receipts need explicit scope before result lookup.
        policy = operation_policies().get(action)
        if policy is not None and policy.sections and clinical_section is None:
            return Err(AccessDenied())

        if clinical_section is not None and not clinical_result_allowed(
            context, clinical_section
        ):
            return Err(AccessDenied())

        receipt = await dao_receipts.get_scoped(
            db, account_id, context.actor.user_id, operation_id
        )

        if receipt is Empty:
            return Err(OperationNotFound())

        object_rule = None if policy is None else policy.object_rule
        if object_rule in ("own_catalog", "own_offer"):
            permission = await service_permission(db, context)

            if isinstance(permission, Err):
                return permission

        if object_rule == "block" and isinstance(receipt.entity_key, str):
            permission = await block_permission(db, context, UUID(receipt.entity_key))

            if isinstance(permission, Err):
                return Err(AccessDenied())

        now = await dao_heads.get_server_time(db)

        if receipt.result_json is None or now >= receipt.result_expires_at:
            return Err(ResultExpired())

        response = OperationResult.model_validate(receipt.result_json)

        if clinical_section is not None:
            await record_control(
                db,
                ControlAudit(
                    account_id=account_id,
                    actor_user_id=context.actor.user_id,
                    actor_device_id=context.actor.device_id,
                    action="ReadOperationResult",
                    object_type="operation_result",
                    object_key=str(operation_id),
                    outcome="accepted",
                    correlation_id=uuid7(),
                    occurred_at=now,
                ),
            )

    return Ok(response)
