"""Private attachment storage backends.

Two interchangeable backends selected by configuration: S3 through aioaws
(source: https://github.com/odiseo0/aioaws, v0.16) when the bucket and
credentials are set, and a private server directory for local development.
Bytes live outside the database and the journal in both backends.
"""

import base64
import hashlib
from pathlib import Path
from uuid import UUID

from src.settings.storage_settings import storage_settings


class StorageError(Exception):
    """Attachment bytes could not be stored or retrieved."""


def _s3_enabled() -> bool:
    return bool(
        storage_settings.STORAGE_BUCKET
        and storage_settings.STORAGE_KEY
        and storage_settings.STORAGE_SECRET
        and storage_settings.STORAGE_REGION
    )


def _import_s3():
    import builtins
    import typing

    builtins.Union = getattr(builtins, "Union", typing.Union)
    builtins.Optional = getattr(builtins, "Optional", typing.Optional)

    import httpx2
    from aioaws.s3 import S3Client, S3Config

    config = S3Config(
        aws_access_key=storage_settings.STORAGE_KEY or "",
        aws_secret_key=storage_settings.STORAGE_SECRET or "",
        aws_region=storage_settings.STORAGE_REGION or "",
        aws_s3_bucket=storage_settings.STORAGE_BUCKET or "",
        aws_host=storage_settings.STORAGE_ENDPOINT,
    )
    return S3Client(httpx2.AsyncClient(), config)


def _local_path(account_id: UUID, attachment_id: UUID) -> Path:
    return Path(storage_settings.STORAGE_ROOT) / str(account_id) / f"{attachment_id}.bin"


async def save(account_id: UUID, attachment_id: UUID, content: bytes) -> str:
    if _s3_enabled():
        client = _import_s3()
        key = f"{account_id}/{attachment_id}"
        await client.upload(key, content)
        return f"s3://{storage_settings.STORAGE_BUCKET}/{key}"

    target = _local_path(account_id, attachment_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return f"{account_id}/{attachment_id}"


async def fetch(account_id: UUID, attachment_id: UUID) -> bytes:
    if _s3_enabled():
        client = _import_s3()
        return await client.download(f"{account_id}/{attachment_id}")

    target = _local_path(account_id, attachment_id)

    if not target.is_file():
        raise StorageError("attachment bytes missing")

    return target.read_bytes()


def decode_and_verify(content_base64: str, expected_sha256: str) -> bytes:
    try:
        content = base64.b64decode(content_base64, validate=True)
    except ValueError as error:
        raise StorageError("invalid base64 content") from error

    if hashlib.sha256(content).hexdigest() != expected_sha256.lower():
        raise StorageError("content does not match its digest")

    return content


__all__ = ["StorageError", "decode_and_verify", "fetch", "save"]
