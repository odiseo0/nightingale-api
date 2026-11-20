from contextvars import ContextVar
from datetime import timedelta, timezone
from uuid import UUID

REQUEST_TIMEOUT_SECONDS = 15
DELAY_BETWEEN_REQUESTS_SECONDS = 1.5
TZ = timezone(timedelta(hours=-4), name="America/Caracas")
CORRELATION_ID: ContextVar[UUID | None] = ContextVar("correlation_id", default=None)
