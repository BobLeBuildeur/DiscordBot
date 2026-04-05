"""CLI: create a user JSON file under AUTH_USERS_DIR."""

from __future__ import annotations

import argparse
import getpass
from datetime import datetime, timezone

from pydantic import EmailStr, TypeAdapter, ValidationError

from auth_service.config import get_settings
from auth_service.security import hash_password
from auth_service.users import user_file_path, write_user_record
from auth_service.validation import UserRecord, UserRole, normalized_username_from_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user file for auth-service.")
    parser.add_argument(
        "--username",
        required=True,
        help="Email-shaped username (same rules as login email)",
    )
    parser.add_argument(
        "--role",
        choices=[r.value for r in UserRole],
        default=UserRole.analyst.value,
        help="Application role (default: analyst)",
    )
    parser.add_argument(
        "--password",
        help="Plain password (if omitted, prompts securely)",
    )
    args = parser.parse_args()

    try:
        email = TypeAdapter(EmailStr).validate_python(args.username.strip())
    except ValidationError as e:
        raise SystemExit(f"Invalid username/email: {e}") from e

    normalized = normalized_username_from_email(str(email))
    password = args.password if args.password is not None else getpass.getpass("Password: ")
    password2 = getpass.getpass("Password (again): ") if args.password is None else password
    if password != password2:
        raise SystemExit("Passwords do not match")

    settings = get_settings()
    pepper = settings.auth_password_pepper
    pw_hash = hash_password(password, pepper)
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    role = UserRole(args.role)
    record = UserRecord(
        username=normalized,
        password_hash=pw_hash,
        created_at=created,
        role=role,
    )
    path = user_file_path(settings.auth_users_dir.resolve(), normalized)
    if path.exists():
        raise SystemExit(f"User file already exists: {path}")

    write_user_record(path, record)
    print(f"Wrote user file: {path}")


if __name__ == "__main__":
    main()
