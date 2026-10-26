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
