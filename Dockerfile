# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder: resolves locked dependencies and builds the project wheel with uv.
# Only build tooling lives here; nothing from this stage ships except .venv.
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.15-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# gcc/make for wheels without cp315 binaries; git for the aioaws git dependency.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY src ./src

# --no-dev drops test tooling; --no-editable installs the built wheel so the
# runtime image needs no source copy at all.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ---------------------------------------------------------------------------
# Runtime: minimal image with only the virtualenv (app + dependencies).
# ---------------------------------------------------------------------------
FROM python:3.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

RUN useradd --create-home app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health/live',timeout=4)" || exit 1

CMD ["sh", "-c", "uvicorn src.application:app --host 0.0.0.0 --port ${PORT:-8000}"]
