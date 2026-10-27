import base64
import hmac


def sign_position(payload: bytes, key: bytes) -> str:
    encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.digest(key, encoded, "sha256")

    return (encoded + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode(
        "ascii"
    )


def verify_position(value: str, key: bytes) -> bytes | None:
    if len(value) > 8192:
        return None

    try:
        encoded, signature = value.encode("ascii").split(b".")
        expected = base64.urlsafe_b64encode(hmac.digest(key, encoded, "sha256")).rstrip(
            b"="
        )
        # Compare the MAC before parsing the signed body.
        # https://docs.python.org/3.15/library/hmac.html#hmac.compare_digest
        if not hmac.compare_digest(signature, expected):
            return None

        payload = base64.b64decode(
            encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True
        )

        if base64.urlsafe_b64encode(payload).rstrip(b"=") != encoded:
            return None

        return payload
    except ValueError, UnicodeError:
        return None
