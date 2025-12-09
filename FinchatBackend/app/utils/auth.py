import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(calc, expected)


def _b64url_encode(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def encode_jwt(payload: dict, secret: str, expires_minutes: int = 60) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    payload_with_exp = {**payload, "exp": int(exp.timestamp())}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload_with_exp, separators=(",", ":")).encode("utf-8"))
    signing_input = header_b64 + b"." + payload_b64
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    token = signing_input + b"." + _b64url_encode(signature)
    return token.decode("ascii")


def decode_jwt(token: str, secret: str) -> Optional[dict]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        exp = payload.get("exp")
        if exp and datetime.now(tz=timezone.utc).timestamp() > exp:
            return None
        return payload
    except Exception:
        return None
