from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from auth_service.config import Settings, get_settings
from auth_service.security import (
    create_access_token,
    decode_access_token,
    generate_random_password,
    hash_password,
    verify_password,
)
from auth_service.users import (
    ensure_username_consistency,
    load_user_record,
    user_file_path,
    write_user_record,
)
from auth_service.validation import (
    LoginBody,
    UsernameBody,
    UserRecord,
    UserRole,
    normalized_username_from_email,
)


def extract_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    # Parse `Authorization` for routes that require a logged-in user (e.g. reset-password). We only
    # accept the Bearer scheme per RFC 6750 (`Authorization: Bearer <jwt>`); anything else is
    # rejected with 401 before reset-specific checks (e.g. 403 when not self and not admin).
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]


def _can_reset_password_for_target(payload: dict[str, Any], target_normalized: str) -> bool:
    # Caller may reset the target user only if JWT sub matches that user, or JWT role is admin.
    sub = payload.get("sub")
    if not isinstance(sub, str):
        return False
    actor = normalized_username_from_email(sub)
    role = payload.get("role")
    if actor == target_normalized:
        return True
    return role == UserRole.admin.value


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
        except (ValueError, ValidationError) as e:
            raise HTTPException(status_code=401, detail="Invalid credentials") from e

        if record is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not ensure_username_consistency(normalized, record):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(body.password, record.password_hash, resolved.auth_password_pepper):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(normalized, record.role, resolved)
        return {"access_token": token, "token_type": "bearer"}

    @router.post("/users", status_code=201)
    def create_user_http(body: UsernameBody) -> dict[str, str]:
        if not resolved.auth_http_create_user_enabled:
            raise HTTPException(
                status_code=403,
                detail=(
                    "HTTP user creation is disabled "
                    "(set AUTH_HTTP_CREATE_USER_ENABLED=true to enable)."
                ),
            )
        normalized = normalized_username_from_email(str(body.username))
        users_dir = resolved.auth_users_dir.resolve()
        path = user_file_path(users_dir, normalized)
        _assert_path_under_users_dir(users_dir, path)
        if path.is_file():
            raise HTTPException(status_code=409, detail="User already exists")
        plain = generate_random_password()
        pw_hash = hash_password(plain, resolved.auth_password_pepper)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        created = now.isoformat().replace("+00:00", "Z")
        record = UserRecord(
            username=normalized,
            password_hash=pw_hash,
            created_at=created,
            role=UserRole.analyst,
        )
        write_user_record(path, record)
        return {"username": normalized, "password": plain}

    @router.post("/users/reset-password")
    def reset_password(
        body: UsernameBody,
        bearer: Annotated[str, Depends(extract_bearer_token)],
    ) -> dict[str, str]:
        # 1. Verify JWT: Bearer string was already parsed by `extract_bearer_token`. Decode with the
        #    same HS256 secret as login; require exp/sub/role. Bad signature, wrong alg, or expired
        #    token → 401 (client must re-authenticate).
        try:
            payload = decode_access_token(bearer, resolved)
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from e

        # 2. Normalize the target account id: `UsernameBody` already enforced email-shaped input and
        #    stripped controls; lowercase + trim matches login and the on-disk `username` field.
        normalized = normalized_username_from_email(str(body.username))

        # 3. Authorize the operation: only the user identified by JWT `sub` may reset their own
        #    password, or any caller whose JWT `role` is admin may reset another user. Everyone
        #    else → 403 (authenticated but not permitted for this target).
        if not _can_reset_password_for_target(payload, normalized):
            raise HTTPException(
                status_code=403,
                detail="Not allowed to reset password for this user",
            )

        # 4. Resolve the JSON file path from the normalized username (SHA-256 hex filename) and
        #    ensure it stays under `AUTH_USERS_DIR` (no path escape).
        users_dir = resolved.auth_users_dir.resolve()
        path = user_file_path(users_dir, normalized)
        _assert_path_under_users_dir(users_dir, path)

        # 5. Load the user record: corrupt JSON → 500; missing file, invalid schema, or unreadable
        #    user object → 404 so we do not leak whether the account existed vs malformed data.
        try:
            record = load_user_record(path)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail="User record unreadable") from e
        except (ValueError, ValidationError) as e:
            raise HTTPException(status_code=404, detail="User not found") from e

        # 6. Confirm the file corresponds to this login: no row → 404; `username` inside JSON must
        #    match the normalized identifier (same check as login).
        if record is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not ensure_username_consistency(normalized, record):
            raise HTTPException(status_code=404, detail="User not found")

        # 7. Issue a new random password, bcrypt-hash it (with optional pepper), replace only
        #    `password_hash` on the record, write to the same path, return plaintext once to caller.
        plain = generate_random_password()
        new_hash = hash_password(plain, resolved.auth_password_pepper)
        updated = record.model_copy(update={"password_hash": new_hash})
        write_user_record(path, updated)
        return {"username": normalized, "password": plain}

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
