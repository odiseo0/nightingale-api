from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OperationNotFound:
    pass


@dataclass(frozen=True, slots=True)
class ResultExpired:
    pass
