import base64
import hashlib
import re
import secrets
from uuid import RFC_4122, UUID, uuid7


def issue_token() -> tuple[UUID, str, bytes]:
    token_id = uuid7()
    secret = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii")

    return token_id, f"ngt_{token_id}.{encoded}", hashlib.sha256(secret).digest()


def parse_token(value: str) -> tuple[UUID, bytes] | None:
    match = re.fullmatch(r"ngt_([0-9a-f-]{36})\.([A-Za-z0-9_-]{43})", value)

    if match is None:
        return None

    try:
        token_id = UUID(match[1])
        secret = base64.b64decode(match[2] + "=", altchars=b"-_", validate=True)
    except ValueError:
        return None

    if (
        token_id.version != 7
        or token_id.variant != RFC_4122
        or str(token_id) != match[1]
    ):
        return None

    if base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii") != match[2]:
        return None

    return token_id, hashlib.sha256(secret).digest()
