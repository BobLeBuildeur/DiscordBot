"""Sanitized request and user-record models."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

MAX_EMAIL_LEN = 254
MAX_PASSWORD_LEN = 1024
MAX_HASH_STRING_LEN = 512
MAX_CREATED_AT_LEN = 64

# Reject ASCII control characters (0x00–0x1F) and DEL.
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _reject_controls(value: str, field: str) -> str:
    if _CONTROL_RE.search(value):
        raise ValueError(f"{field} contains disallowed control characters")
    return value


class LoginBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LEN)

    @field_validator("email", mode="before")
    @classmethod
    def email_strip(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email")
    @classmethod
    def email_controls(cls, v: str) -> str:
        return _reject_controls(v, "email")

    @field_validator("password")
    @classmethod
    def password_controls(cls, v: str) -> str:
        return _reject_controls(v, "password")


class UserRecord(BaseModel):
    """Validated on-disk JSON for a single user."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    username: EmailStr
    password_hash: str = Field(..., min_length=1, max_length=MAX_HASH_STRING_LEN)
    created_at: str = Field(..., min_length=1, max_length=MAX_CREATED_AT_LEN)

    @field_validator("username")
    @classmethod
    def username_controls(cls, v: str) -> str:
        return _reject_controls(v, "username")

    @field_validator("password_hash")
    @classmethod
    def password_hash_shape(cls, v: str) -> str:
        v = _reject_controls(v, "password_hash")
        if not (v.startswith("$2b$") or v.startswith("$2a$") or v.startswith("$argon2")):
            raise ValueError("password_hash must be a bcrypt or argon2 digest string")
        return v

    @field_validator("created_at")
    @classmethod
    def created_at_iso(cls, v: str) -> str:
        v = _reject_controls(v, "created_at")
        raw = v.replace("Z", "+00:00")
        datetime.fromisoformat(raw)
        return v


def normalized_username_from_email(email: str) -> str:
    """Trim + lowercase; caller must have validated email shape."""
    return email.strip().lower()
