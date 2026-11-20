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


def _import_s3(bucket: str | None = None):
    import httpx2
    from aioaws.s3 import S3Client, S3Config

    config = S3Config(
        aws_access_key=storage_settings.STORAGE_KEY or "",
        aws_secret_key=storage_settings.STORAGE_SECRET or "",
        aws_region=storage_settings.STORAGE_REGION or "",
        aws_s3_bucket=bucket or storage_settings.STORAGE_BUCKET or "",
        aws_host=storage_settings.STORAGE_ENDPOINT,
    )
    http_client = httpx2.AsyncClient()

    return S3Client(http_client, config), http_client


def _local_path(account_id: UUID, attachment_id: UUID) -> Path:
    return (
        Path(storage_settings.STORAGE_ROOT) / str(account_id) / f"{attachment_id}.bin"
    )


async def save(account_id: UUID, attachment_id: UUID, content: bytes) -> str:
    if _s3_enabled():
        client, http_client = _import_s3()
        key = f"{account_id}/{attachment_id}"

        try:
            await client.upload(key, content)
            return f"s3://{storage_settings.STORAGE_BUCKET}/{key}"
        finally:
            await http_client.aclose()

    target = _local_path(account_id, attachment_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")

    try:
        temporary.write_bytes(content)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)

    return str(target.resolve())


async def fetch(storage_key: str) -> bytes:
    if storage_key.startswith("s3://"):
        bucket, separator, key = storage_key.removeprefix("s3://").partition("/")

        if not bucket or not separator or not key:
            raise StorageError("invalid storage key")

        client, http_client = _import_s3(bucket)

        try:
            return await client.download(key)
        finally:
            await http_client.aclose()

    target = Path(storage_key)

    if not target.is_absolute():
        target = Path(storage_settings.STORAGE_ROOT) / f"{storage_key}.bin"

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
