import test_authorization_structure as structure


class AccountsStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/accounts"
    dao_names = {
        "AccountDAO", "AccountMembershipDAO", "ProfessionalDAO",
        "AccountProfessionalDAO", "AccountDeviceAccessDAO",
    }


class SyncStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/sync"
    dao_names = {"AccountSyncHeadDAO"}


class UsersStructureTests(structure.AuthorizationStructureTests):
    component = structure.ROOT / "src/api/users"
    dao_names = {"UserDAO"}
