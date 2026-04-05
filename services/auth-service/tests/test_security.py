from __future__ import annotations

from pathlib import Path

import jwt

from auth_service.config import Settings
from auth_service.security import create_access_token, hash_password, verify_password
from auth_service.validation import UserRole


def test_hash_and_verify_roundtrip():
    h = hash_password("secret123", None)
    assert verify_password("secret123", h, None)
    assert not verify_password("wrong", h, None)


def test_hash_with_pepper():
    h = hash_password("secret123", "pep")
    assert verify_password("secret123", h, "pep")
    assert not verify_password("secret123", h, None)


def test_jwt_hs256_claims():
    settings = Settings(
        jwt_signing_secret="x" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    token = create_access_token("user@example.com", UserRole.analyst, settings)
    payload = jwt.decode(token, settings.jwt_signing_secret, algorithms=["HS256"])
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "analyst"
    assert payload["iat"] <= payload["exp"]


def test_jwt_includes_admin_role():
    settings = Settings(
        jwt_signing_secret="x" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    token = create_access_token("admin@example.com", UserRole.admin, settings)
    payload = jwt.decode(token, settings.jwt_signing_secret, algorithms=["HS256"])
    assert payload["role"] == "admin"
