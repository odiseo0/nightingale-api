from contextvars import ContextVar
from datetime import timedelta, timezone
from typing import Literal
from uuid import UUID

REQUEST_TIMEOUT_SECONDS = 15
DELAY_BETWEEN_REQUESTS_SECONDS = 1.5
MAX_BATCH_OPERATIONS: Literal[100] = 100
MAX_BODY_BYTES: Literal[1048576] = 1024 * 1024
MAX_OPERATION_BYTES: Literal[65536] = 64 * 1024
MAX_PAGE_SIZE: Literal[500] = 500
TZ = timezone(timedelta(hours=-4), name="America/Caracas")
CORRELATION_ID: ContextVar[UUID | None] = ContextVar("correlation_id", default=None)
