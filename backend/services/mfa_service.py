"""TOTP MFA, encrypted seed storage, QR enrollment, and recovery codes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import secrets
import struct
import time
from urllib.parse import quote

import qrcode
from cryptography.fernet import Fernet, InvalidToken

from backend.config.settings import get_settings
from backend.database.models import User


class MFAError(ValueError):
    pass


def _fernet() -> Fernet:
    digest = hashlib.sha256((get_settings().secret_key + ":mfa:v1").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode()).decode()
    except (InvalidToken, ValueError) as error:
        raise MFAError("The MFA configuration cannot be decrypted.") from error


def provisioning_uri(username: str, secret: str) -> str:
    issuer = "BloodLink"
    label = quote(f"{issuer}:{username}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def qr_data_uri(uri: str) -> str:
    image = qrcode.make(uri)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()


def _decode_secret(secret: str) -> bytes:
    return base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8), casefold=True)


def totp_code(secret: str, counter: int | None = None) -> tuple[str, int]:
    counter = int(time.time() // 30) if counter is None else counter
    digest = hmac.new(_decode_secret(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{number:06d}", counter


def verify_totp(secret: str, supplied: str, last_counter: int | None = None) -> int | None:
    normalized = "".join(character for character in supplied if character.isdigit())
    if len(normalized) != 6:
        return None
    current = int(time.time() // 30)
    for counter in range(current - 1, current + 2):
        expected, _ = totp_code(secret, counter)
        if hmac.compare_digest(expected, normalized) and (last_counter is None or counter > last_counter):
            return counter
    return None


def _recovery_digest(code: str) -> str:
    key = hashlib.sha256((get_settings().secret_key + ":mfa-recovery:v1").encode()).digest()
    normalized = code.replace("-", "").replace(" ", "").upper()
    return hmac.new(key, normalized.encode(), hashlib.sha256).hexdigest()


def generate_recovery_codes(count: int = 10) -> tuple[list[str], str]:
    codes = [f"{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}" for _ in range(count)]
    return codes, json.dumps([_recovery_digest(code) for code in codes])


def verify_user_code(user: User, supplied: str, *, allow_recovery: bool = True) -> bool:
    if not user.mfa_enabled or not user.mfa_secret_encrypted:
        return False
    counter = verify_totp(decrypt_secret(user.mfa_secret_encrypted), supplied, user.mfa_last_counter)
    if counter is not None:
        user.mfa_last_counter = counter
        return True
    if not allow_recovery or not user.mfa_recovery_codes:
        return False
    wanted = _recovery_digest(supplied)
    hashes = json.loads(user.mfa_recovery_codes)
    for index, stored in enumerate(hashes):
        if hmac.compare_digest(wanted, stored):
            hashes.pop(index)
            user.mfa_recovery_codes = json.dumps(hashes)
            return True
    return False


def recovery_codes_remaining(user: User) -> int:
    try:
        return len(json.loads(user.mfa_recovery_codes or "[]"))
    except (TypeError, ValueError):
        return 0
