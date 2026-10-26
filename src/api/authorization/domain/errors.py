from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvalidCredential:
    pass


@dataclass(frozen=True, slots=True)
class AccessDenied:
    pass


@dataclass(frozen=True, slots=True)
class IdentityProviderUnavailable:
    pass


@dataclass(frozen=True, slots=True)
class DeviceNotFound:
    device_id: UUID
