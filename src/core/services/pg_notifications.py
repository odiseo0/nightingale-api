"""One reconnecting PostgreSQL listener per process; no client owns its connection."""

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field

import asyncpg
from sqlalchemy.engine import make_url


@dataclass(eq=False, slots=True)
class NotificationSlot:
    pending: asyncio.Queue[None] = field(default_factory=lambda: asyncio.Queue(maxsize=1))
    overloaded: bool = False


@dataclass(slots=True)
class NotificationListener:
    ready: bool = False
    generation: int = 0
    slots: dict[str, set[NotificationSlot]] = field(default_factory=dict)
    task: asyncio.Task[None] | None = None

    def subscribe(self, topic: str) -> NotificationSlot:
        slot = NotificationSlot()
        self.slots.setdefault(topic, set()).add(slot)

        return slot

    def unsubscribe(self, topic: str, slot: NotificationSlot) -> None:
        subscribers = self.slots.get(topic)
        if subscribers is not None:
            subscribers.discard(slot)
            if not subscribers:
                del self.slots[topic]

    def wake(self, topic: str) -> None:
        for slot in self.slots.get(topic, ()):
            if slot.pending.full():
                slot.overloaded = True
            else:
                slot.pending.put_nowait(None)

    async def start(self, uri: str) -> None:
        if self.task is not None:
            raise RuntimeError("El listener ya tiene un proceso activo")
        self.task = asyncio.create_task(self.run(uri), name="postgres-notifications")

    async def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        self.ready = False

    async def run(self, uri: str) -> None:
        dsn = make_url(uri).set(drivername="postgresql").render_as_string(hide_password=False)
        while True:
            connection: asyncpg.Connection | None = None
            lost = asyncio.Event()

            def terminated(connection: asyncpg.Connection) -> None:
                self.ready = False
                lost.set()

            def received(connection: asyncpg.Connection, pid: int, channel: str, payload: str) -> None:
                topic, separator, position = payload.partition(":")
                if separator and len(payload) < 128 and position.isascii() and position.isdecimal():
                    self.wake(topic)

            try:
                connection = await asyncpg.connect(dsn, timeout=3, command_timeout=3,
                                                  server_settings={"application_name": "nightingale-sync-listener"})
                if connection is None:
                    raise OSError("El proveedor no abrió la conexión de escucha")
                connection.add_termination_listener(terminated)
                # add_listener awaits LISTEN outside a transaction. Only then may
                # callers inspect persistent state or resume after a lost listener.
                # https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.add_listener
                # https://www.postgresql.org/docs/18/sql-listen.html
                await connection.add_listener("nightingale_sync", received)
                if connection.is_closed():
                    continue
                self.generation += 1
                self.ready = True
                for topic in tuple(self.slots):
                    self.wake(topic)

                while not lost.is_set():
                    try:
                        await asyncio.wait_for(lost.wait(), timeout=15)
                    except TimeoutError:
                        await connection.execute("SELECT 1")
            except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
                # Details can contain a connection string. Readiness conveys the
                # failure without logging credentials or stopping ordinary reads.
                pass
            finally:
                self.ready = False
                if connection is not None:
                    with suppress(asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
                        await connection.close(timeout=3)
            await asyncio.sleep(1)


notifications = NotificationListener()
