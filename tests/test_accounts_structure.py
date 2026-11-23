import test_authorization_structure as structure


class AccountsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/accounts"
    dao_names = {
        "AccountDAO", "AccountMembershipDAO", "ProfessionalDAO",
        "AccountProfessionalDAO", "AccountDeviceAccessDAO", "AccountInvitationDAO",
    }


class SyncStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/sync"
    dao_names = {"AccountSyncHeadDAO", "OperationReceiptDAO", "ChangeLogDAO", "SyncSnapshotDAO", "SyncSnapshotItemDAO", "SyncStreamLeaseDAO"}


class AuditStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/audit"
    dao_names = {"AuditEventDAO"}


class UsersStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/users"
    dao_names = {"UserDAO"}


class ClinicalRecordsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/clinical_records"
    dao_names = {
        "PatientConditionDAO", "PatientAllergyIntoleranceDAO",
        "ClinicalEntryDAO", "PatientClinicalTimelineDAO",
        "PatientNoteDAO", "PatientMeasurementDAO",
        "PatientImmunizationDAO", "PatientAntecedentDAO",
    }


class EncountersStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/encounters"
    dao_names = {"ClinicalEncounterDAO"}


class PatientsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/patients"
    dao_names = {"PatientDAO", "AccountPatientDAO", "PatientIdentifierDAO", "ContactPersonDAO", "PatientContactRelationshipDAO"}


class ServicesStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/services"
    dao_names = {"ServiceDAO", "ProfessionalServiceDAO"}


class ScheduleStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/schedule"
    dao_names = {"ScheduleRuleDAO", "ScheduleExceptionDAO", "ScheduleBlockDAO"}


class AppointmentsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/appointments"
    dao_names = {"AppointmentDAO", "AppointmentHistoryDAO"}


class VademecumStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/vademecum"
    dao_names = {"VademecumDAO"}
