from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from auth_service.config import Settings, get_settings
from auth_service.security import create_access_token, verify_password
from auth_service.users import ensure_username_consistency, load_user_record, user_file_path
from auth_service.validation import LoginBody, normalized_username_from_email


def _cors_allow_origins(settings: Settings) -> list[str]:
    raw = settings.cors_origins.strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _assert_path_under_users_dir(users_dir: Path, path: Path) -> None:
    users_dir = users_dir.resolve()
    path = path.resolve()
    try:
        path.relative_to(users_dir)
    except ValueError as e:
        raise HTTPException(status_code=500, detail="Invalid user storage path") from e


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    router = APIRouter()

    @router.post("/login")
    def login(body: LoginBody) -> dict[str, str]:
        normalized = normalized_username_from_email(str(body.email))
        users_dir = resolved.auth_users_dir.resolve()
        path = user_file_path(users_dir, normalized)
        _assert_path_under_users_dir(users_dir, path)

        try:
            record = load_user_record(path)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail="User record unreadable") from e
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Invalid credentials") from e

        if record is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not ensure_username_consistency(normalized, record):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(body.password, record.password_hash, resolved.auth_password_pepper):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(normalized, resolved)
        return {"access_token": token, "token_type": "bearer"}

    app = FastAPI(title="Auth service", version="0.1.0")
    app.state.settings = resolved

    allow = _cors_allow_origins(resolved)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow,
        allow_credentials=allow != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/auth", tags=["auth"])

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def __getattr__(name: str):
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
