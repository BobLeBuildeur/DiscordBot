"""Username → filesystem path (SHA-256 hex) and JSON user records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from auth_service.validation import UserRecord, normalized_username_from_email


def username_to_filename_digest(username_normalized: str) -> str:
    """SHA-256 hex of UTF-8 normalized username — filename label only, not a security boundary."""
    h = hashlib.sha256(username_normalized.encode("utf-8")).hexdigest()
    return f"{h}.json"


def user_file_path(users_dir: Path, username_normalized: str) -> Path:
    name = username_to_filename_digest(username_normalized)
    return (users_dir / name).resolve()


def load_user_record(path: Path) -> UserRecord | None:
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("user file must be a JSON object")
    return UserRecord.model_validate(data)


def write_user_record(path: Path, record: UserRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = record.model_dump(mode="json")
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ensure_username_consistency(normalized: str, record: UserRecord) -> bool:
    # Compare normalized forms; on-disk `username` is email-shaped.
    return normalized_username_from_email(str(record.username)) == normalized
