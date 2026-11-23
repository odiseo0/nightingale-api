from typing import Literal

from src.core.constants import (
    MAX_BATCH_OPERATIONS,
    MAX_BODY_BYTES,
    MAX_OPERATION_BYTES,
    MAX_PAGE_SIZE,
)
from src.core.schema import BaseModel


class DefaultAppointmentWindow(BaseModel):
    days_before: Literal[30] = 30
    days_after: Literal[180] = 180
    max_days: Literal[366] = 366


class CapabilitiesResponse(BaseModel):
    contract_version: Literal[1] = 1
    model_revision: Literal["api-v1.3"] = "api-v1.3"
    operation_catalog: list[str]
    online_only_actions: list[str]
    max_batch_operations: Literal[100] = MAX_BATCH_OPERATIONS
    max_body_bytes: Literal[1048576] = MAX_BODY_BYTES
    max_operation_bytes: Literal[65536] = MAX_OPERATION_BYTES
    max_page_size: Literal[500] = MAX_PAGE_SIZE
    sync_retention_days: Literal[90] = 90
    snapshot_ttl_seconds: Literal[900] = 900
    recovery_required_codes: list[Literal["CURSOR_EXPIRED", "SNAPSHOT_EXPIRED", "SNAPSHOT_SCOPE_CHANGED", "RESULT_EXPIRED"]]
    default_appointment_window: DefaultAppointmentWindow = DefaultAppointmentWindow()
