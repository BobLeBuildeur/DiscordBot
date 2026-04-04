from __future__ import annotations

from datetime import datetime, timezone

import pytest
from starlette.testclient import TestClient

from auth_service.app import create_app
from auth_service.config import get_settings
from auth_service.security import hash_password
from auth_service.users import write_user_record
from auth_service.validation import UserRecord


@pytest.fixture
def client(auth_env):
    app = create_app(get_settings())
    return TestClient(app)


def _write_user(users_dir, email: str, password: str):
    normalized = email.strip().lower()
    pepper = get_settings().auth_password_pepper
    pw_hash = hash_password(password, pepper)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = UserRecord(username=normalized, password_hash=pw_hash, created_at=created)
    from auth_service.users import user_file_path

    path = user_file_path(users_dir, normalized)
    write_user_record(path, record)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_success(client, auth_env):
    _write_user(auth_env["users_dir"], "u@example.com", "abcd1234")
    r = client.post("/auth/login", json={"email": "u@example.com", "password": "abcd1234"})
    assert r.status_code == 200
    data = r.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


def test_login_failure(client, auth_env):
    _write_user(auth_env["users_dir"], "u@example.com", "abcd1234")
    r = client.post("/auth/login", json={"email": "u@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_user(client, auth_env):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "abcd1234"})
    assert r.status_code == 401


def test_login_nul_rejected(client, auth_env):
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "x\u0000y"})
    assert r.status_code == 422


def test_login_invalid_email_422(client, auth_env):
    r = client.post("/auth/login", json={"email": "not-an-email", "password": "abcd1234"})
    assert r.status_code == 422


def test_login_oversized_email_422(client, auth_env):
    huge = "a" * 300 + "@x.com"
    r = client.post("/auth/login", json={"email": huge, "password": "abcd1234"})
    assert r.status_code == 422
