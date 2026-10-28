import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.sse import ServerSentEvent
from starlette.requests import ClientDisconnect
from anyio import create_task_group, sleep

from src.core.services.pg_notifications import NotificationListener
from src.core.services.sse import BoundedEventSourceResponse


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_stream_finishes_cleanup_in_the_cancel_scope(self):
        cleaned = asyncio.Event()
        async def events():
            await asyncio.Event().wait()
            yield ServerSentEvent(event="heartbeat")

        async def cleanup():
            await sleep(.01)
            cleaned.set()

        response = BoundedEventSourceResponse(events(), cleanup)
        async with create_task_group() as tasks:
            tasks.start_soon(response, {"type": "http", "asgi": {"spec_version": "2.4"}}, AsyncMock(), AsyncMock())
            await sleep(.01)
            tasks.cancel_scope.cancel()
        self.assertTrue(cleaned.is_set())

    async def test_pending_hint_is_bounded_and_overflow_marks_the_consumer(self):
        listener = NotificationListener()
        slot = listener.subscribe("fixture-account")
        listener.wake("other-account")
        self.assertTrue(slot.pending.empty())
        listener.wake("fixture-account")
        self.assertEqual(slot.pending.qsize(), 1)
        listener.wake("fixture-account")
        self.assertTrue(slot.overloaded)
        self.assertEqual(slot.pending.qsize(), 1)
        listener.unsubscribe("fixture-account", slot)
        self.assertEqual(listener.slots, {})

    async def test_listen_is_confirmed_before_ready_and_recovery_wakes_subscribers(self):
        listener = NotificationListener()
        slot = listener.subscribe("fixture-account")
        connection = MagicMock()
        connection.close = AsyncMock()
        connection.is_closed.return_value = False
        confirmed = asyncio.Event()

        async def listen(channel, callback):
            self.assertFalse(listener.ready)
            await confirmed.wait()

        connection.add_listener = AsyncMock(side_effect=listen)
        with patch("src.core.services.pg_notifications.asyncpg.connect", AsyncMock(return_value=connection)):
            await listener.start("postgresql+asyncpg://fixture:fictional@127.0.0.1/fixture")
            await asyncio.sleep(0)
            self.assertFalse(listener.ready)
            confirmed.set()
            for _ in range(30):
                if listener.ready:
                    break
                await asyncio.sleep(0)
            self.assertTrue(listener.ready)
            self.assertEqual(listener.generation, 1)
            self.assertEqual(slot.pending.qsize(), 1)
            connection.add_termination_listener.call_args.args[0](connection)
            self.assertFalse(listener.ready)
            await listener.stop()
        connection.close.assert_awaited_once()
        self.assertFalse(listener.ready)

    async def test_slow_network_send_times_out_and_releases_resources(self):
        async def events():
            yield ServerSentEvent(event="heartbeat", raw_data='{"serverTime":"fixture"}', retry=3000)

        async def send(message):
            if message["type"] == "http.response.body":
                await asyncio.Event().wait()

        cleanup = AsyncMock()
        response = BoundedEventSourceResponse(events(), cleanup)
        with self.assertRaises(ClientDisconnect):
            await response({"type": "http", "asgi": {"spec_version": "2.4"}}, AsyncMock(), send)
        cleanup.assert_awaited_once()

    async def test_native_sse_encoding_preserves_event_id_retry_and_json(self):
        async def events():
            yield ServerSentEvent(event="changes_available", id="12", retry=3000, raw_data='{"cursor":"fixture"}')

        response = BoundedEventSourceResponse(events(), AsyncMock())
        frame = await anext(response.frames)
        self.assertIn(b"event: changes_available\n", frame)
        self.assertIn(b"id: 12\n", frame)
        self.assertIn(b"retry: 3000\n", frame)
        self.assertIn(b'data: {"cursor":"fixture"}\n', frame)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        await response.frames.aclose()
        await response.events.aclose()


if __name__ == "__main__":
    unittest.main()
