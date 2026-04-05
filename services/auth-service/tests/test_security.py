from __future__ import annotations

from pathlib import Path

import jwt
import pytest

from auth_service.config import Settings
from auth_service.security import (
    create_access_token,
    decode_access_token,
    generate_random_password,
    hash_password,
    verify_password,
)
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


def test_generate_random_password_eight_alnum():
    p = generate_random_password()
    assert len(p) == 8
    assert all(c.isalnum() for c in p)


def test_decode_access_token_roundtrip():
    settings = Settings(
        jwt_signing_secret="x" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    token = create_access_token("actor@example.com", UserRole.analyst, settings)
    payload = decode_access_token(token, settings)
    assert payload["sub"] == "actor@example.com"
    assert payload["role"] == "analyst"


def test_decode_access_token_rejects_wrong_secret():
    settings = Settings(
        jwt_signing_secret="x" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    other = Settings(
        jwt_signing_secret="y" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    token = create_access_token("u@example.com", UserRole.analyst, settings)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, other)


def test_jwt_includes_admin_role():
    settings = Settings(
        jwt_signing_secret="x" * 32,
        jwt_expires_days=30,
        auth_users_dir=Path("/tmp"),
    )
    token = create_access_token("admin@example.com", UserRole.admin, settings)
    payload = jwt.decode(token, settings.jwt_signing_secret, algorithms=["HS256"])
    assert payload["role"] == "admin"
