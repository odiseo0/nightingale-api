from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from src.core.schema import BaseModel

# Closed platform actions (api-v1.md §14.1); separate from account RBAC (D23).
OperatorAction = Literal["review", "catalog", "rates", "operators"]

OperatorStatus = Literal["active", "revoked"]


class OperatorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlatformOperator(OperatorModel):
    """Platform actor for subscription review; never a member of any account."""

    operator_id: UUID
    display_name: Annotated[str, Field(min_length=1)]
    actions: Annotated[frozenset[OperatorAction], Field(min_length=1)]
    status: OperatorStatus = "active"
    version: Annotated[int, Field(ge=1)] = 1


class OperatorAccessDeniedError(PermissionError):
    pass


def ensure_operator_action(
    operator: PlatformOperator, credential_revoked: bool, action: OperatorAction
) -> None:
    """Every operator request re-checks identity, credential and action (D23)."""
    if operator.status != "active" or credential_revoked:
        raise OperatorAccessDeniedError("operator credential is not valid")

    if action not in operator.actions:
        raise OperatorAccessDeniedError(f"operator lacks the {action} action")


def revoke_operator(operator: PlatformOperator) -> PlatformOperator:
    if operator.status == "revoked":
        raise OperatorAccessDeniedError("operator is already revoked")

    return operator.model_copy(update={"status": "revoked", "version": operator.version + 1})
