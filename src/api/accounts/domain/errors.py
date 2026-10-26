from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PracticeAlreadyExists:
    owner_user_id: UUID


@dataclass(frozen=True, slots=True)
class AccountNotFound:
    account_id: UUID


@dataclass(frozen=True, slots=True)
class ProfessionalNotFound:
    user_id: UUID


@dataclass(frozen=True, slots=True)
class UnknownTimeZone:
    name: str


@dataclass(frozen=True, slots=True)
class DeviceVersionConflict:
    version: int | None


@dataclass(frozen=True, slots=True)
class DeviceAlreadyRegistered:
    version: int


@dataclass(frozen=True, slots=True)
class AccountObjectNotFound:
    pass


@dataclass(frozen=True, slots=True)
class AccountRuleError:
    code: str
    version: int | None = None
