from typing import Literal

from src.api.accounts.domain.accounts import (
    AccountContext,
    ClinicalLevel,
    ClinicalPermissions,
    ClinicalSection,
)
from src.core.schema import BaseModel

type ObjectRule = Literal[
    "account",
    "own_device",
    "account_device",
    "patient",
    "contact",
    "schedule",
    "block",
    "appointment",
    "clinical_record",
    "membership",
    "invitation",
    "own_professional",
    "own_catalog",
    "own_offer",
]


class OperationPolicy(BaseModel):
    name: str
    owner_only: bool
    object_rule: ObjectRule
    sections: tuple[ClinicalSection, ...] = ()
    required_level: Literal["read_write"] | None = None
    changes_scope: bool = False
    # A shared review has two public positions, but only one descriptor.
    publication: tuple[tuple[int, ClinicalSection | None], ...] = ()


def operation_policies() -> dict[str, OperationPolicy]:
    groups: tuple[tuple[str, bool, ClinicalSection | None, ObjectRule], ...] = (
        ("RegisterAccountDevice", False, None, "own_device"),
        (
            "RegisterPatient UpdatePatientProfile SetPatientProfileStatus SetPatientCompletion AddPatientIdentifier",
            False,
            None,
            "patient",
        ),
        (
            "CreateContactPerson UpdateContactPerson SetContactPersonStatus CreatePatientContactRelationship UpdatePatientContactRelationship SetPatientContactRelationshipStatus",
            False,
            None,
            "contact",
        ),
        (
            "CreateScheduleRule UpdateScheduleRule SetScheduleRuleStatus CreateScheduleException UpdateScheduleException SetScheduleExceptionStatus",
            False,
            None,
            "schedule",
        ),
        (
            "CreateScheduleBlock UpdateScheduleBlock SetScheduleBlockStatus",
            False,
            None,
            "block",
        ),
        (
            "CreateAppointment ConfirmAppointment RescheduleAppointment CancelAppointment CompleteAppointment MarkAppointmentNoShow",
            False,
            None,
            "appointment",
        ),
        ("SetPatientSexAtBirth", False, "profile", "clinical_record"),
        (
            "CreatePatientCondition UpdatePatientCondition InvalidatePatientCondition SetPatientClinicalSectionReview",
            False,
            "conditions",
            "clinical_record",
        ),
        (
            "CreatePatientAllergyIntolerance UpdatePatientAllergyIntolerance InvalidatePatientAllergyIntolerance SetPatientClinicalSectionReview",
            False,
            "allergies",
            "clinical_record",
        ),
        (
            "CreatePatientEncounter UpdatePatientEncounter InvalidatePatientEncounter",
            False,
            "encounters",
            "clinical_record",
        ),
        (
            "CreatePatientNote UpdatePatientNote InvalidatePatientNote",
            False,
            "notes",
            "clinical_record",
        ),
        (
            "RecordPatientMeasurement CorrectPatientMeasurement InvalidatePatientMeasurement",
            False,
            "measurements",
            "clinical_record",
        ),
        (
            "RecordPatientImmunization UpdatePatientImmunization InvalidatePatientImmunization",
            False,
            "immunizations",
            "clinical_record",
        ),
        (
            "CreatePatientAntecedent UpdatePatientAntecedent InvalidatePatientAntecedent",
            False,
            "antecedents",
            "clinical_record",
        ),
        (
            "DeclarePatientMedication UpdatePatientDeclaredMedication ReviewPatientDeclaredMedication InvalidatePatientDeclaredMedication",
            False,
            "declared_medications",
            "clinical_record",
        ),
        (
            "CreatePatientCarePlan UpdatePatientCarePlan InvalidatePatientCarePlan AddCarePlanGoal UpdateCarePlanGoal EvaluateCarePlanGoal InvalidateCarePlanGoal AddCarePlanAction UpdateCarePlanAction CompleteCarePlanAction InvalidateCarePlanAction AddCarePlanReview InvalidateCarePlanReview",
            False,
            "care_plans",
            "clinical_record",
        ),
        (
            "CreateDiagnosticReport UpdateDiagnosticReport CorrectDiagnosticReport AddDiagnosticReportResult UpdateDiagnosticReportResult InvalidateDiagnosticReportResult UploadReportAttachment InvalidateReportAttachment",
            False,
            "diagnostic_reports",
            "clinical_record",
        ),
        (
            "CreateSpecialtyTemplate UpdateSpecialtyTemplate RetireSpecialtyTemplate CaptureSpecialtyRecord UpdateSpecialtyRecord InvalidateSpecialtyRecord",
            False,
            "specialty_templates",
            "clinical_record",
        ),
        (
            "RecordDentalFinding UpdateDentalFinding ResolveDentalFinding InvalidateDentalFinding AddDentalTreatment UpdateDentalTreatment InvalidateDentalTreatment",
            False,
            "specialty_templates",
            "clinical_record",
        ),
        ("CreateInvitation RevokeInvitation", True, None, "invitation"),
        ("SetMembershipStatus SetMemberClinicalPermissions", True, None, "membership"),
        (
            "UpdateAccountDetails UpdateAccountPolicy SetAccountStatus",
            True,
            None,
            "account",
        ),
        ("RevokeAccountDevice RestoreAccountDevice", True, None, "account_device"),
        ("UpdateProfessionalProfile", True, None, "own_professional"),
        ("CreateService UpdateService SetServiceStatus", True, None, "own_catalog"),
        (
            "OfferService UpdateServiceOffer SetServiceOfferStatus",
            True,
            None,
            "own_offer",
        ),
    )
    policies: dict[str, OperationPolicy] = {}
    position = 0

    for actions, owner_only, section, object_rule in groups:
        for action in actions.split():
            policy = policies.get(action)

            if policy is None:
                policy = OperationPolicy(
                    name=action,
                    owner_only=owner_only,
                    object_rule=object_rule,
                    changes_scope=action
                    in (
                        "RegisterAccountDevice",
                        "SetAccountStatus",
                        "SetMembershipStatus",
                        "SetMemberClinicalPermissions",
                        "RevokeAccountDevice",
                        "RestoreAccountDevice",
                    ),
                )
                policies[action] = policy

            if section is not None:
                policy.sections += (section,)
                policy.required_level = "read_write"

            publication_entry: tuple[int, ClinicalSection | None] = (position, section)
            policy.publication += (publication_entry,)
            position += 1

    policies["AcceptInvitation"] = OperationPolicy(
        name="AcceptInvitation",
        owner_only=False,
        object_rule="invitation",
        changes_scope=True,
    )

    return policies


def policy_allows(
    context: AccountContext,
    action: str,
    section: ClinicalSection | None = None,
    *,
    discovery: bool = False,
) -> bool:
    """Decide base access only; the resource owner still checks object relations."""
    policy = operation_policies().get(action)

    if policy is None or (policy.owner_only and not context.owner):
        return False

    if context.device_status == "revoked":
        return False

    if context.account.status != "active":
        return (
            policy.name == "SetAccountStatus"
            and context.owner
            and context.device_status == "active"
        )

    if (
        policy.name not in ("RegisterAccountDevice", "AcceptInvitation")
        and context.device_status != "active"
    ):
        return False

    if policy.sections:
        if section not in policy.sections:
            return False

        return section is not None and (
            (context.owner and not discovery)
            or context.clinical_permissions.level(section) == policy.required_level
        )

    return section is None


def published_actions(context: AccountContext) -> list[str]:
    policies = operation_policies()
    positions = sorted(
        (position, policy.name, section)
        for policy in policies.values()
        for position, section in policy.publication
    )

    return [
        name
        for _, name, section in positions
        if policy_allows(context, name, section, discovery=True)
    ]


def clinical_section_for_action(
    action: str,
    payload_section: ClinicalSection | None = None,
) -> ClinicalSection | None:
    policy = operation_policies().get(action)

    if policy is None or not policy.sections:
        return None

    if len(policy.sections) == 1:
        return policy.sections[0]

    return payload_section if payload_section in policy.sections else None


def catalog_clinical_sections() -> list[ClinicalSection]:
    return list(
        dict.fromkeys(
            section
            for policy in operation_policies().values()
            for section in policy.sections
        )
    )


def clinical_level_allows(
    context: AccountContext,
    section: ClinicalSection | None,
    required_level: Literal["read", "read_write"],
) -> bool:
    if section is None or section not in catalog_clinical_sections():
        return False

    level = context.clinical_permissions.level(section)

    if required_level == "read_write":
        return context.owner or level == required_level

    return level != "none"


def clinical_audiences() -> dict[str, ClinicalSection]:
    return {"clinical_" + section: section for section in catalog_clinical_sections()}


def projection_audiences() -> dict[str, tuple[str, ...]]:
    rules: dict[str, tuple[str, ...]] = {
        entity: ("members",)
        for entity in [
            "account",
            "professional",
            "patient_profile",
            "patient_identifier",
            "contact_person",
            "patient_contact",
            "service_offer",
            "schedule_rule",
            "schedule_exception",
            "schedule_block",
            "appointment",
            "appointment_history",
        ]
    }

    rules.update(
        {
            entity: ("owner",)
            for entity in ["account_device", "membership", "invitation", "service"]
        }
    )
    policies = operation_policies()

    for entity, action in (
        ("patient_clinical_profile", "SetPatientSexAtBirth"),
        ("patient_condition", "CreatePatientCondition"),
        ("patient_allergy_intolerance", "CreatePatientAllergyIntolerance"),
        ("patient_clinical_section_review", "SetPatientClinicalSectionReview"),
        ("clinical_encounter", "CreatePatientEncounter"),
        ("patient_note", "CreatePatientNote"),
        ("patient_measurement", "RecordPatientMeasurement"),
        ("patient_immunization", "RecordPatientImmunization"),
        ("patient_antecedent", "CreatePatientAntecedent"),
        ("declared_medication", "DeclarePatientMedication"),
        ("care_plan", "CreatePatientCarePlan"),
        ("care_plan_goal", "AddCarePlanGoal"),
        ("care_plan_action", "AddCarePlanAction"),
        ("care_plan_review", "AddCarePlanReview"),
        ("diagnostic_report", "CreateDiagnosticReport"),
        ("diagnostic_report_result", "AddDiagnosticReportResult"),
        ("report_attachment", "UploadReportAttachment"),
        ("specialty_template", "CreateSpecialtyTemplate"),
        ("specialty_record", "CaptureSpecialtyRecord"),
        ("dental_finding", "RecordDentalFinding"),
        ("dental_treatment", "AddDentalTreatment"),
    ):
        rules[entity] = tuple(
            "clinical_" + section for section in policies[action].sections
        )

    return rules


def projection_allowed(
    entity: str,
    audience: str | None,
    owner: bool,
    sections: list[ClinicalSection],
    section: ClinicalSection | None = None,
) -> bool:
    audiences = projection_audiences().get(entity)

    if audiences is None:
        return False

    if audience is None:
        audience = (
            "clinical_" + section
            if section is not None
            else (audiences[0] if len(audiences) == 1 else None)
        )

    if audience is None or audience not in audiences:
        return False

    if audience == "members":
        return True

    if audience == "owner":
        return owner

    clinical_section = clinical_audiences().get(audience)

    return clinical_section is not None and clinical_section in sections


def sync_scope_matches(
    context: AccountContext,
    audience: str,
    sections: list[ClinicalSection],
    permission_epoch: int,
    current_epoch: int,
) -> bool:
    return (
        audience == ("owner" if context.owner else "members")
        and permission_epoch == current_epoch
        and all(clinical_level_allows(context, section, "read") for section in sections)
    )


def scope_changes(action: str) -> bool:
    policy = operation_policies().get(action)

    return policy is not None and policy.changes_scope


def clinical_permission_values(
    permissions: ClinicalPermissions,
) -> dict[str, ClinicalLevel]:
    return {
        ("clinical_profile" if section == "profile" else section)
        + "_access": permissions.level(section)
        for section in catalog_clinical_sections()
    }
