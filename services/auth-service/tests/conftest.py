from __future__ import annotations

import pytest

from auth_service.config import get_settings


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    secret = "unit-test-jwt-secret-min-32-bytes-xx"
    users = tmp_path / "users"
    users.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("JWT_SIGNING_SECRET", secret)
    monkeypatch.setenv("AUTH_USERS_DIR", str(users))
    monkeypatch.setenv("AUTH_CORS_ORIGINS", "*")
    get_settings.cache_clear()
    yield {"users_dir": users, "secret": secret}
    get_settings.cache_clear()
