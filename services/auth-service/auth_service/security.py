"""Password hashing (bcrypt) and HS256 JWT issuance."""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from auth_service.config import Settings
from auth_service.validation import UserRole

_ALPHANUM = string.ascii_letters + string.digits


def apply_pepper(password: str, pepper: str | None) -> bytes:
    if not pepper:
        return password.encode("utf-8")
    return (pepper + password).encode("utf-8")


def hash_password(plain: str, pepper: str | None) -> str:
    data = apply_pepper(plain, pepper)
    hashed = bcrypt.hashpw(data, bcrypt.gensalt())
    return hashed.decode("ascii")


def verify_password(plain: str, password_hash: str, pepper: str | None) -> bool:
    try:
        stored = password_hash.encode("ascii")
    except UnicodeEncodeError:
        return False
    data = apply_pepper(plain, pepper)
    return bcrypt.checkpw(data, stored)


def generate_random_password(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHANUM) for _ in range(length))


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify HS256 JWT from this service; raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_signing_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "sub", "role"]},
    )


def create_access_token(subject_username: str, role: UserRole, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.jwt_expires_days)
    payload = {
        "sub": subject_username,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "role": role.value,
    }
    return jwt.encode(
        payload,
        settings.jwt_signing_secret,
        algorithm="HS256",
    )
