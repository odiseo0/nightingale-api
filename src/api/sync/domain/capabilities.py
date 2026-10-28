from typing import Literal

from src.core.schema import BaseModel


class DefaultAppointmentWindow(BaseModel):
    days_before: Literal[30] = 30
    days_after: Literal[180] = 180
    max_days: Literal[366] = 366


class CapabilitiesResponse(BaseModel):
    contract_version: Literal[1] = 1
    model_revision: Literal["api-v1.1"] = "api-v1.1"
    operation_catalog: list[str]
    online_only_actions: list[str]
    max_batch_operations: Literal[100] = 100
    max_body_bytes: Literal[1048576] = 1048576
    max_operation_bytes: Literal[65536] = 65536
    max_page_size: Literal[500] = 500
    sync_retention_days: Literal[90] = 90
    snapshot_ttl_seconds: Literal[900] = 900
    recovery_required_codes: list[Literal["CURSOR_EXPIRED", "SNAPSHOT_EXPIRED", "SNAPSHOT_SCOPE_CHANGED", "RESULT_EXPIRED"]]
    default_appointment_window: DefaultAppointmentWindow = DefaultAppointmentWindow()
