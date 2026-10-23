---
name: fastapi
description: "When planning or "
---

This SKILL is for FastAPI best practices and tips, there's also some guidance related to the project structure which you should follow.


Project Structure:
This is a representation of how the project is structured, it uses a custom implementation inspired from Hexagonal Architecture + Package by Component.
It's flexible, clean and simple

nightingale-api/
├── src/
│   ├── api/
│   │   └── {component}/
│   │       ├── application/     # Use cases
│   │       ├── domain/          # Pydantic Schemas
│   │       ├── infrastructure/  # API Routers
│   │       └── repository/      # SQLAlchemy Models and Data Access Object (DAO)
│   ├── core/
│   │   ├── db/                  # AsyncEngine and Session Factory
│   │   ├── schema/              # Base Pydantic Schemas
│   │   ├── services/            # Services (External like S3, Redis, etc. And Internal like custom services)
│   │   │   └── cache/           
│   │   ├── types/               # Custom Types that the whole application uses
│   │   └── utils/               # Helpers
│   └── settings/                # Settings like DatabaseSettings, StorageSettings, APISettings...
│   └── application.py           # Main file
└── tests/                       # Tests


**Cross-domain imports**: always use the explicit module name. Never `from src.auth import *`.

```python
from src.auth import constants as auth_constants
from src.notifications import service as notification_service
from src.posts.constants import ErrorCode as PostsErrorCode
```

Avoid Circular imports, we can use also use lazy imports (https://realpython.com/python315-lazy-imports/)

## Async Routes

### Decision rule

| Route does this                        | Use         |
|----------------------------------------|-------------|
| `await`-able non-blocking I/O          | `async def` |
| Blocking I/O (no async client exists)  | `def` (sync, runs in threadpool) |
| Mix of both                            | `async def` + `run_in_threadpool` for the blocking part |
| CPU-bound work (>50 ms compute)        | Offload to a worker process (Celery / RQ / Arq) |

### Do / Don't

```python
# DON'T — blocking call inside async route freezes the entire event loop
@router.get("/bad")
async def bad():
    time.sleep(10)            # blocks every request on this worker
    return {"ok": True}

# DO — sync route lets FastAPI run it in a threadpool
@router.get("/sync-ok")
def sync_ok():
    time.sleep(10)            # blocks one threadpool worker, not the loop
    return {"ok": True}

# DO — async route with awaitable sleep
@router.get("/async-ok")
async def async_ok():
    await asyncio.sleep(10)   # yields control, loop keeps serving requests
    return {"ok": True}

# DO — async route that has to call a sync library
from fastapi.concurrency import run_in_threadpool

@router.get("/wrap")
async def wrap():
    result = await run_in_threadpool(legacy_sync_client.fetch, "id")
    return result
```

### Threadpool caveats
- Default Starlette threadpool size is 40. Saturating it slows every sync route.
- Threads cost more than coroutines. Don't use sync routes "just because."

## Pydantic

### Use built-in validators
```python
from enum import StrEnum
from pydantic import AnyUrl, BaseModel, EmailStr, Field


class MusicBand(StrEnum):
    AEROSMITH = "AEROSMITH"
    QUEEN = "QUEEN"
    ACDC = "AC/DC"


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=128)
    username: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    email: EmailStr
    age: int = Field(ge=18)                     # required, must be >= 18
    favorite_band: MusicBand | None = None
    website: AnyUrl | None = None
```

> **Don't** write `Field(ge=18, default=None)`. The constraint and the default contradict
> each other. Decide: required (`Field(ge=18)`) or optional (`int | None = Field(default=None, ge=18)`).

### Custom base model — modern serialization

`json_encoders` is deprecated in Pydantic v2. Use `@field_serializer` for per-field rules,
or annotate a custom type with `PlainSerializer`.

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, field_serializer


class CustomModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_datetimes(self, value):
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo("UTC"))
            return value.strftime("%Y-%m-%dT%H:%M:%S%z")
        return value
```

### Split BaseSettings by domain

`pydantic-settings` is its own package since Pydantic v2.

```python
# src/auth/config.py
from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    JWT_ALG: str
    JWT_SECRET: str
    JWT_EXP_MINUTES: int = 5
    REFRESH_TOKEN_KEY: str
    REFRESH_TOKEN_EXP: timedelta = timedelta(days=30)
    SECURE_COOKIES: bool = True


auth_settings = AuthConfig()
```

## Dependencies

### Use Annotated, not default-arg `Depends(...)`

`Annotated[T, Depends(...)]` is the idiomatic form since FastAPI 0.95 and avoids
gotchas with default values.

```python
# DO — modern Annotated form
from typing import Annotated
from fastapi import Depends

PostDep = Annotated[dict, Depends(valid_post_id)]

@router.get("/posts/{post_id}")
async def get_post(post: PostDep):
    return post

# Avoid — default-argument form (still works, but legacy)
@router.get("/posts/{post_id}")
async def get_post(post: dict = Depends(valid_post_id)):
    return post
```

### Validate inside dependencies (not just inject)
```python
async def valid_post_id(post_id: UUID4) -> dict:
    post = await service.get_by_id(post_id)
    if not post:
        raise PostNotFound()
    return post
```

### Chain dependencies for reuse
```python
async def valid_owned_post(
    post: Annotated[dict, Depends(valid_post_id)],
    token_data: Annotated[dict, Depends(parse_jwt_data)],
) -> dict:
    if post["creator_id"] != token_data["user_id"]:
        raise UserNotOwner()
    return post
```

### Rules
- Dependencies are **cached per request**. Same `Depends(x)` called 5 times in one request → `x` runs once.
- Prefer `async def` dependencies. Sync deps run in the threadpool — wasted overhead for small CPU-only checks.
- Use **the same path-variable name** across endpoints when you want to share a dependency (e.g. `profile_id` in both `/profiles/{profile_id}` and `/creators/{profile_id}`).

## Authentication — JWT

Use **`PyJWT`**, not `python-jose` (unmaintained).

```python
import jwt  # PyJWT
from jwt.exceptions import InvalidTokenError

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except InvalidTokenError as exc:
        raise InvalidCredentials() from exc
```

## Database — SQLAlchemy 2.0 async

Prefer SQLAlchemy 2.0's async API. `encode/databases` is in maintenance mode — don't pick it for new projects.

```python
# src/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionFactory() as session:
        yield session
```

### Naming conventions
- `lower_case_snake`
- Singular tables: `post`, `user`, `post_like`
- Group with prefix: `payment_account`, `payment_bill`
- `_at` suffix for `datetime`, `_date` suffix for `date`
- Use the same FK column name everywhere it appears (`profile_id`, not `user_id` in some tables and `profile_id` in others)

### Index naming convention
```python
from sqlalchemy import MetaData

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)
```

### SQL-first, Pydantic-second
- Do joins, aggregation, and JSON shaping in SQL — Postgres is faster than CPython at this.
- Hydrate the result into Pydantic only for response validation, not for transformation.

## Background work — BackgroundTasks vs Celery

| Use BackgroundTasks when…                | Use Celery / Arq / RQ when…                |
|------------------------------------------|--------------------------------------------|
| Task is < 1 second                       | Task takes seconds to minutes              |
| Failure can be silently dropped          | You need retries, dead-letter, or visibility|
| Task is in-process (send email, log row) | Task is CPU-heavy or needs a separate pool |
| You don't need scheduling                | You need cron, ETA, or rate limiting       |

```python
from fastapi import BackgroundTasks

@router.post("/signup")
async def signup(data: SignupIn, bg: BackgroundTasks):
    user = await service.create_user(data)
    bg.add_task(send_welcome_email, user.email)   # fire-and-forget, in-process
    return user
```

> BackgroundTasks run **after the response is sent, in the same worker process**. If the
> worker dies, the task is lost. There is no retry. Don't use them for anything you'd
> page on.

## Testing

### Async client from day one
```python
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_post(client: AsyncClient):
    resp = await client.post("/posts", json={"title": "hi"})
    assert resp.status_code == 201
```

> **Don't** use `async_asgi_testclient` — it's unmaintained. The example above (httpx +
> `ASGITransport`) is the supported path.

### Override dependencies in tests
Don't monkeypatch internals. Use FastAPI's built-in `dependency_overrides`.

```python
from src.auth.dependencies import parse_jwt_data
from src.main import app


def fake_user():
    return {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[parse_jwt_data] = fake_user
    yield
    app.dependency_overrides.clear()
```

## Migrations (Alembic)

- Migrations must be static and reversible.
- Use the async template: `alembic init -t async migrations`
- Descriptive filenames:
  ```ini
  # alembic.ini
  file_template = %%(year)d-%%(month).2d-%%(day).2d_%%(slug)s
  ```
  → `2026-04-14_add_post_content_idx.py`

## API documentation

### Hide docs outside selected envs
```python
from fastapi import FastAPI
from src.config import settings

SHOW_DOCS_IN = {"local", "staging"}
app_kwargs = {"title": "My API"}
if settings.ENVIRONMENT not in SHOW_DOCS_IN:
    app_kwargs["openapi_url"] = None    # disables /docs and /redoc

app = FastAPI(**app_kwargs)
```

### Document endpoints fully
```python
from fastapi import APIRouter, status

router = APIRouter()


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
    description="Creates an item owned by the authenticated user.",
    tags=["items"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Validation error"},
        status.HTTP_409_CONFLICT:    {"model": ErrorResponse, "description": "Slug already exists"},
    },
)
async def create_item(payload: ItemCreate) -> ItemResponse: ...
```


## 1. Use `async for` instead of `while True` on WebSocket

Most of the examples you will find on the internet use `while True` to read messages from the WebSocket.

I believe the uglier notation is used mainly because the Starlette documentation didn't show the `async for` notation for a long time.

Instead of using the `while True`:

```py
from fastapi import FastAPI
from starlette.websockets import WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
```

You can use the `async for` notation:

```py
from fastapi import FastAPI
from starlette.websockets import WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    async for data in websocket.iter_text():
        await websocket.send_text(f"Message text was: {data}")
```

You can read more about it on the [Starlette documentation][websockets-iter-data].

## 2. Ignore the `WebSocketDisconnect` exception

If you are using the `while True` notation, you will need to catch the `WebSocketDisconnect`.
The `async for` notation will catch it for you.

```py
from fastapi import FastAPI
from starlette.websockets import WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        pass
```

If you need to release resources when the WebSocket is disconnected, you can use that exception to do it.

If you are using an older FastAPI version, only the `receive` methods will raise the `WebSocketDisconnect` exception.
The `send` methods will not raise it. In the latest versions, all methods will raise it.
In that case, you'll need to add the `send` methods inside the `try` block.

## 3. Use HTTPX's `AsyncClient` instead of `TestClient`

Since you are using `async` functions in your application, it will be easier to use HTTPX's `AsyncClient`
instead of Starlette's `TestClient`.

```py
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


# Using TestClient
from starlette.testclient import TestClient

client = TestClient(app)
response = client.get("/")
assert response.status_code == 200
assert response.json() == {"Hello": "World"}

# Using AsyncClient
import anyio
from httpx import AsyncClient, ASGITransport


async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}


anyio.run(main)
```

If you are using lifespan events (`on_startup`, `on_shutdown` or the `lifespan` parameter), you can use the
[`asgi-lifespan`][asgi-lifespan] package to run those events.

```py
from contextlib import asynccontextmanager
from typing import AsyncIterator

import anyio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Starting app")
    yield
    print("Stopping app")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


async def main():
    async with LifespanManager(app) as manager:
        async with AsyncClient(transport=ASGITransport(app=manager.app)) as client:
            response = await client.get("/")
            assert response.status_code == 200
            assert response.json() == {"Hello": "World"}


anyio.run(main)
```

## 4. Use Lifespan State instead of `app.state`

Since not long ago, FastAPI supports the [lifespan state], which defines a standard way to manage objects that need to be created at
startup, and need to be used in the request-response cycle.

The `app.state` is not recommended to be used anymore. You should use the [lifespan state] instead.

Using the `app.state`, you'd do something like this:

```py
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from httpx import AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncClient(app=app) as client:
        app.state.client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root(request: Request):
    client = request.app.state.client
    response = await client.get("/")
    return response.json()
```

Using the lifespan state, you'd do something like this:

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypedDict, cast

from fastapi import FastAPI, Request
from httpx import AsyncClient


class State(TypedDict):
    client: AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    async with AsyncClient(app=app) as client:
        yield {"client": client}


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root(request: Request) -> dict[str, Any]:
    client = cast(AsyncClient, request.state.client)
    response = await client.get("/")
    return response.json()
```

## 5. Enable AsyncIO debug mode

If you want to find the endpoints that are blocking the event loop, you can enable the AsyncIO debug mode.

When you enable it, Python will print a warning message when a task takes more than 100ms to execute.

Run the following code with `PYTHONASYNCIODEBUG=1 python main.py`:

```py
import os
import time

import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def read_root():
    time.sleep(1)  # Blocking call
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, loop="uvloop")
```

If you call the endpoint, you will see the following message:

```bash
INFO:     Started server process [19319]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:50036 - "GET / HTTP/1.1" 200 OK
Executing <Task finished name='Task-3' coro=<RequestResponseCycle.run_asgi() done, defined at /uvicorn/uvicorn/protocols/http/httptools_impl.py:408> result=None created at /uvicorn/uvicorn/protocols/http/httptools_impl.py:291> took 1.009 seconds
```

You can read more about it on the [official documentation](https://docs.python.org/3/library/asyncio-dev.html#debug-mode).

## 6. Implement a Pure ASGI Middleware instead of `BaseHTTPMiddleware`

The [`BaseHTTPMiddleware`][base-http-middleware] is the simplest way to create a middleware in FastAPI.

> [!NOTE]
> The `@app.middleware("http")` decorator is a wrapper around the `BaseHTTPMiddleware`.

There were some issues with the `BaseHTTPMiddleware`, but most of the issues were fixed in the latest versions.
That said, there's still a performance penalty when using it.

To avoid the performance penalty, you can implement a [Pure ASGI middleware]. The downside is that it's more complex to implement.

Check the Starlette's documentation to learn how to implement a [Pure ASGI middleware].

## 7. Your dependencies may be running on threads

If the function is non-async and you use it as a dependency, it will run in a thread.

In the following example, the `http_client` function will run in a thread:

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from httpx import AsyncClient
from fastapi import FastAPI, Request, Depends


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, AsyncClient]]:
    async with AsyncClient() as client:
        yield {"client": client}


app = FastAPI(lifespan=lifespan)


def http_client(request: Request) -> AsyncClient:
    return request.state.client


@app.get("/")
async def read_root(client: AsyncClient = Depends(http_client)):
    return await client.get("/")
```

To run in the event loop, you need to make the function async:
```py
# ...

async def http_client(request: Request) -> AsyncClient:
    return request.state.client

# ...
```

As an exercise for the reader, let's learn a bit more about how to check the running threads.

You can run the following with `python main.py`:

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from anyio.to_thread import current_default_thread_limiter
from httpx import AsyncClient
from fastapi import FastAPI, Request, Depends


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, AsyncClient]]:
    async with AsyncClient() as client:
        yield {"client": client}


app = FastAPI(lifespan=lifespan)


# Change this function to be async, and rerun this application.
def http_client(request: Request) -> AsyncClient:
    return request.state.client


@app.get("/")
async def read_root(client: AsyncClient = Depends(http_client)): ...


async def monitor_thread_limiter():
    limiter = current_default_thread_limiter()
    threads_in_use = limiter.borrowed_tokens
    while True:
        if threads_in_use != limiter.borrowed_tokens:
            print(f"Threads in use: {limiter.borrowed_tokens}")
            threads_in_use = limiter.borrowed_tokens
        await anyio.sleep(0)


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(app="main:app")
    server = uvicorn.Server(config)

    async def main():
        async with anyio.create_task_group() as tg:
            tg.start_soon(monitor_thread_limiter)
            await server.serve()

    anyio.run(main)
```

If you call the endpoint, you will see the following message:

```bash
❯ python main.py
INFO:     Started server process [23966]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
Threads in use: 1
INFO:     127.0.0.1:57848 - "GET / HTTP/1.1" 200 OK
Threads in use: 0
```

Replace the `def http_client` with `async def http_client` and rerun the application.
You will not see the message `Threads in use: 1`, because the function is running in the event loop.

> [!TIP]
> You can use the [FastAPI Dependency] package that I've built to make it explicit when a dependency should run in a thread.

## 10. Use `pytest.mark.anyio` instead of `pytest.mark.asyncio`

You already have [`anyio`](https://github.com/agronholm/anyio) installed, since it's a dependency of Starlette.
Which means, you can use `pytest.mark.anyio` instead of `pytest.mark.asyncio`.

```py
import pytest

@pytest.mark.anyio
async def test_async_function(): ...
```

By default, `anyio` runs every test that has the marker twice, once with `trio` and another time with `asyncio`.
You probably want to restrict that by using either one or the other, in case you are testing an application,
and not a package:

```py
import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"  # or "trio"
```

You can read more about it on the
[`anyio` documentation](https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on).

[uvicorn]: https://uvicorn.dev/
[run_sync]: https://anyio.readthedocs.io/en/stable/threads.html#running-a-function-in-a-worker-thread
[run_in_threadpool]: https://github.com/encode/starlette/blob/9f16bf5c25e126200701f6e04330864f4a91a898/starlette/concurrency.py#L36-L42
[increase-threadpool]: https://anyio.readthedocs.io/en/stable/threads.html#adjusting-the-default-maximum-worker-thread-count
[websockets-iter-data]: https://starlette.dev/websockets/#iterating-data
[florimondmanca]: https://github.com/sponsors/florimondmanca
[asgi-lifespan]: https://github.com/florimondmanca/asgi-lifespan
[lifespan state]: https://asgi.readthedocs.io/en/latest/specs/lifespan.html#lifespan-state
[The FastAPI Expert]: https://github.com/Kludex
[base-http-middleware]: https://starlette.dev/middleware/#basehttpmiddleware
[pure ASGI middleware]: https://starlette.dev/middleware/#pure-asgi-middleware
[FastAPI Dependency]: https://github.com/kludex/fastapi-dependency
