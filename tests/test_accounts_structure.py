import test_authorization_structure as structure


class AccountsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/accounts"
    dao_names = {
        "AccountDAO", "AccountMembershipDAO", "ProfessionalDAO",
        "AccountProfessionalDAO", "AccountDeviceAccessDAO", "AccountInvitationDAO",
    }


class SyncStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/sync"
    dao_names = {"AccountSyncHeadDAO", "OperationReceiptDAO", "ChangeLogDAO"}


class AuditStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/audit"
    dao_names = {"AuditEventDAO"}


class UsersStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/users"
    dao_names = {"UserDAO"}


class PatientsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/patients"
    dao_names = {"PatientDAO", "AccountPatientDAO", "PatientIdentifierDAO", "ContactPersonDAO", "PatientContactRelationshipDAO"}
