# auth-service

Small **HTTP auth** service: file-backed users (JSON on disk), **bcrypt** passwords, **HS256** JWT access tokens.

**Further docs:** [docs/http-admin-flows.md](docs/http-admin-flows.md) — Mermaid diagrams for optional HTTP create-user and reset-password flows.

## Run

Bootstrap once (creates `.venv`, installs deps, copies `.env.example` → `.env` if needed):

```bash
# From monorepo root
./scripts/auth-service/bootstrap.sh
```

Equivalent scripts also live next to this service (same behavior):

```bash
cd services/auth-service
./scripts/bootstrap.sh
```

Activate the venv in your **current** shell (must `source` it):

```bash
# From monorepo root
source scripts/auth-service/activate-venv.sh
```

Or:

```bash
source services/auth-service/scripts/activate-venv.sh
```

Manual setup (equivalent to bootstrap):

```bash
cd services/auth-service
cp .env.example .env   # set JWT_SIGNING_SECRET (min 16 chars; use 32+ for HS256)
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

Create a user file (`pip install -e .` installs the `auth-create-user` command; bcrypt stores a hash, not plaintext):

```bash
cd services/auth-service
source ./scripts/activate-venv.sh   # or activate your venv
# Ensure JWT_SIGNING_SECRET is set (e.g. in .env)
auth-create-user --username analyst@example.com
```

Use `--role admin` or `--role analyst` (default is **analyst**):

```bash
auth-create-user --username admin@example.com --role admin
```

Password is prompted twice if omitted. You can pass it explicitly (avoid shell history on shared machines):

```bash
auth-create-user --username analyst@example.com --password 'yourPassword123'
```

Start the API (factory app — reads `.env` on startup):

```bash
uvicorn auth_service.app:create_app --factory --host 0.0.0.0 --port 8090
```

## Environment

| Variable | Description |
|----------|-------------|
| `JWT_SIGNING_SECRET` | **Required.** Shared secret for HS256 JWT signing. |
| `AUTH_USERS_DIR` | Directory for per-user JSON files (default `data/users`). |
| `JWT_EXPIRES_DAYS` | Access token lifetime in days (default `30`). |
| `AUTH_PASSWORD_PEPPER` | Optional string mixed into bcrypt input. |
| `AUTH_CORS_ORIGINS` | Comma-separated allowed origins, or `*` (dev). |
| `AUTH_HTTP_CREATE_USER_ENABLED` | If `true`, allow `POST /auth/users` to create users with a random password. Default **`false`**; when disabled the endpoint returns **403**. |

## User files

- **Filename:** `sha256(utf8(normalized_username)).hexdigest() + ".json"` (label only; not for secrecy).
- **JSON fields:** `username` (email), `password_hash` (bcrypt), `created_at` (ISO 8601, UTC `Z` recommended), **`role`** — required, either `admin` or `analyst`.

## JWT

Access tokens are **HS256**. Besides `sub`, `iat`, and `exp`, each token includes a **`role`** claim (`admin` or `analyst`) matching the user file.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Body: `{ "email", "password" }` → `{ "access_token", "token_type": "bearer" }` (JWT includes `role`) |
| `POST` | `/auth/users` | Body: `{ "username" }` (email-shaped). **403** if `AUTH_HTTP_CREATE_USER_ENABLED` is not `true`. **201** with `{ "username", "password" }` (random 8 alphanumeric) or **409** if user exists. New users get `role` **analyst**. |
| `POST` | `/auth/users/reset-password` | Header: `Authorization: Bearer <jwt>`. Body: `{ "username" }`. Resets password only if JWT `sub` matches `username` or JWT `role` is **admin**. **200** with `{ "username", "password" }`, **401**/**403**/**404** as appropriate. |
| `GET` | `/health` | Liveness |

Responses that return a generated **password** are sensitive: use **TLS** in production and treat the value as secret.


## Ops

In production, place a reverse proxy in front of this service and **orchestration-web** / **orchestration-server**; restrict `AUTH_CORS_ORIGINS` to known web origins.

## Tests

```bash
pytest
```
