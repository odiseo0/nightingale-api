from typing import Never

from src.api.sync.domain.capabilities import CapabilitiesResponse
from src.api.sync.domain.operations import EMPTY_PAYLOAD_ACTIONS, OPERATION_SCHEMAS
from src.core import Ok, Result


def get_capabilities() -> Result[CapabilitiesResponse, Never]:
    return Ok(
        CapabilitiesResponse(
            operation_catalog=sorted(
                (set(OPERATION_SCHEMAS) | EMPTY_PAYLOAD_ACTIONS) - {"AcceptInvitation"}
            ),
            online_only_actions=[
                "AcceptInvitation",
                "CreateInvitation",
                "RegisterAccountDevice",
                "RestoreAccountDevice",
                "RevokeAccountDevice",
                "RevokeInvitation",
                "SetAccountStatus",
                "SetMembershipStatus",
                "UpdateAccountDetails",
                "UpdateAccountPolicy",
            ],
            recovery_required_codes=[
                "CURSOR_EXPIRED",
                "SNAPSHOT_EXPIRED",
                "SNAPSHOT_SCOPE_CHANGED",
                "RESULT_EXPIRED",
            ],
        )
    )
