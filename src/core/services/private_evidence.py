import hashlib
from dataclasses import dataclass

from src.core import Err, Ok, Result

# Real file signatures, never the client Content-Type (OWASP upload rules).
SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
)


@dataclass(frozen=True, slots=True)
class EvidenceRejected:
    reason: str


def detect_content_type(content: bytes) -> str | None:
    for signature, content_type in SIGNATURES:
        if content.startswith(signature):
            return content_type

    return None


def validate_capture(
    content: bytes, max_bytes: int
) -> Result[tuple[str, str], EvidenceRejected]:
    """Shared private-capture validation for subscriptions and billing (D24/D28):
    size bound, real signature and integrity digest. Bytes never enter the
    database, the journal or logs."""
    if len(content) == 0 or len(content) > max_bytes:
        return Err(EvidenceRejected("invalid_size"))

    content_type = detect_content_type(content)

    if content_type is None:
        return Err(EvidenceRejected("invalid_type"))

    return Ok((content_type, hashlib.sha256(content).hexdigest()))
