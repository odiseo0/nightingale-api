"""Bound network writes and release stream resources on every exit."""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable

from fastapi.sse import EventSourceResponse, ServerSentEvent, format_sse_event
from anyio import move_on_after
from starlette.types import Message, Receive, Scope, Send


class BoundedEventSourceResponse(EventSourceResponse):
    def __init__(
        self, events: AsyncGenerator[ServerSentEvent, None], cleanup: Callable[[], Awaitable[None]],
    ) -> None:
        self.events = events
        self.cleanup = cleanup
        self.frames = self.encode()
        super().__init__(self.frames, headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    async def encode(self) -> AsyncGenerator[bytes, None]:
        # Direct responses validate access before sending HTTP headers. Reuse the
        # installed FastAPI 0.159.1 SSE formatter and event validation.
        # https://fastapi.tiangolo.com/tutorial/server-sent-events/
        async for event in self.events:
            yield format_sse_event(data_str=event.raw_data, event=event.event, id=event.id,
                                   retry=event.retry, comment=event.comment)

    async def stream_response(self, send: Send) -> None:
        async def bounded_send(message: Message) -> None:
            async with asyncio.timeout(3):
                await send(message)

        await super().stream_response(bounded_send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            # Starlette cancels streams with an AnyIO scope. Let resource cleanup
            # finish inside that cancelled scope, with a bounded grace period.
            # https://anyio.readthedocs.io/en/stable/cancellation.html#shielding
            with move_on_after(3, shield=True):
                await self.frames.aclose()
                await self.events.aclose()
                await self.cleanup()
