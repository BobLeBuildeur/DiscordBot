from __future__ import annotations

import json
from datetime import datetime, timezone

import jwt
import pytest
from starlette.testclient import TestClient

from auth_service.app import create_app
from auth_service.config import get_settings
from auth_service.security import hash_password
from auth_service.users import user_file_path, write_user_record
from auth_service.validation import UserRecord, UserRole


@pytest.fixture
def client(auth_env):
    app = create_app(get_settings())
    return TestClient(app)


def _write_user(users_dir, email: str, password: str, *, role: UserRole = UserRole.analyst):
    normalized = email.strip().lower()
    pepper = get_settings().auth_password_pepper
    pw_hash = hash_password(password, pepper)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = UserRecord(
        username=normalized,
        password_hash=pw_hash,
        created_at=created,
        role=role,
    )
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
    payload = jwt.decode(data["access_token"], auth_env["secret"], algorithms=["HS256"])
    assert payload["role"] == "analyst"


def test_login_jwt_reflects_admin_role(client, auth_env):
    _write_user(auth_env["users_dir"], "a@example.com", "abcd1234", role=UserRole.admin)
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "abcd1234"})
    assert r.status_code == 200
    payload = jwt.decode(r.json()["access_token"], auth_env["secret"], algorithms=["HS256"])
    assert payload["role"] == "admin"


def test_login_rejects_user_file_without_role(client, auth_env):
    normalized = "legacy@example.com"
    pepper = get_settings().auth_password_pepper
    pw_hash = hash_password("abcd1234", pepper)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = user_file_path(auth_env["users_dir"], normalized)
    path.write_text(
        json.dumps(
            {
                "username": normalized,
                "password_hash": pw_hash,
                "created_at": created,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r = client.post("/auth/login", json={"email": "legacy@example.com", "password": "abcd1234"})
    assert r.status_code == 401


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


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_user_http_disabled_403(client):
    r = client.post("/auth/users", json={"username": "new@example.com"})
    assert r.status_code == 403


def test_create_user_http_enabled_201_and_login(auth_env, monkeypatch):
    monkeypatch.setenv("AUTH_HTTP_CREATE_USER_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(create_app(get_settings()))
    try:
        r = client.post("/auth/users", json={"username": "new@example.com"})
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "new@example.com"
        assert len(data["password"]) == 8
        assert all(c.isalnum() for c in data["password"])
        login = client.post(
            "/auth/login",
            json={"email": "new@example.com", "password": data["password"]},
        )
        assert login.status_code == 200
    finally:
        get_settings.cache_clear()


def test_create_user_http_duplicate_409(auth_env, monkeypatch):
    monkeypatch.setenv("AUTH_HTTP_CREATE_USER_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(create_app(get_settings()))
    try:
        assert client.post("/auth/users", json={"username": "dup@example.com"}).status_code == 201
        r = client.post("/auth/users", json={"username": "dup@example.com"})
        assert r.status_code == 409
    finally:
        get_settings.cache_clear()


def test_reset_password_missing_authorization_401(client, auth_env):
    _write_user(auth_env["users_dir"], "u@example.com", "abcd1234")
    r = client.post("/auth/users/reset-password", json={"username": "u@example.com"})
    assert r.status_code == 401


def test_reset_password_invalid_token_401(client, auth_env):
    _write_user(auth_env["users_dir"], "u@example.com", "abcd1234")
    r = client.post(
        "/auth/users/reset-password",
        json={"username": "u@example.com"},
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert r.status_code == 401


def test_reset_password_analyst_cannot_reset_other_403(client, auth_env):
    _write_user(auth_env["users_dir"], "a@example.com", "abcd1234", role=UserRole.analyst)
    _write_user(auth_env["users_dir"], "b@example.com", "abcd1234", role=UserRole.analyst)
    token = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "abcd1234"}
    ).json()["access_token"]
    r = client.post(
        "/auth/users/reset-password",
        json={"username": "b@example.com"},
        headers=_auth_header(token),
    )
    assert r.status_code == 403


def test_reset_password_self_200(client, auth_env):
    _write_user(auth_env["users_dir"], "u@example.com", "abcd1234")
    token = client.post(
        "/auth/login", json={"email": "u@example.com", "password": "abcd1234"}
    ).json()["access_token"]
    r = client.post(
        "/auth/users/reset-password",
        json={"username": "u@example.com"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200
    new_pw = r.json()["password"]
    login = client.post("/auth/login", json={"email": "u@example.com", "password": new_pw})
    assert login.status_code == 200


def test_reset_password_admin_resets_other_200(client, auth_env):
    _write_user(auth_env["users_dir"], "admin@example.com", "adminpass1", role=UserRole.admin)
    _write_user(auth_env["users_dir"], "victim@example.com", "victimpass1", role=UserRole.analyst)
    token = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    ).json()["access_token"]
    r = client.post(
        "/auth/users/reset-password",
        json={"username": "victim@example.com"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200
    new_pw = r.json()["password"]
    login = client.post(
        "/auth/login", json={"email": "victim@example.com", "password": new_pw}
    )
    assert login.status_code == 200


def test_reset_password_unknown_user_404(client, auth_env):
    _write_user(auth_env["users_dir"], "admin@example.com", "adminpass1", role=UserRole.admin)
    token = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    ).json()["access_token"]
    r = client.post(
        "/auth/users/reset-password",
        json={"username": "nobody@example.com"},
        headers=_auth_header(token),
    )
    assert r.status_code == 404
