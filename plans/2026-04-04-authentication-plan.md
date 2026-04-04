# Authentication (auth service + orchestration-web)

## Goal

Deliver end-to-end **sign-in for Analysts** using a dedicated **HTTP authentication service** that validates email-form usernames and passwords against **hashed credentials on disk**, returns **JWTs** with configurable lifetime, and wire **orchestration-web** so users without a valid token are sent to a **login** flow. **Orchestration-server** remains unchanged: it does not verify auth; any caller is assumed to have been authenticated by an **inbound plane** (reverse proxy, API gateway, mesh, etc.)—that deployment concern stays out of scope for this milestone.

**Success criteria**

- Auth service exposes a documented login endpoint; valid credentials yield a JWT; invalid credentials yield a clear error without leaking which field failed.
- **All external inputs** to the auth service (HTTP bodies, values read from user JSON files, CLI args/stdin) are **sanitized and validated** before use—see Steps (reject or normalize unsafe data; bounded lengths; no path traversal).
- User records live as **one JSON file per user** on disk; each **filename** is derived from a **fast, deterministic hash** of the normalized username (email)—for **filesystem-safe, fixed-length names** only, not a security control. Each file **must** include **`username`**, **`password_hash`** (salted password hash from Argon2/bcrypt or equivalent—full encoded string), and **`created_at`** (account creation timestamp).
- Passwords are **hashed with salt** (see Steps for how env “salt/pepper” maps to the chosen algorithm).
- JWTs are signed with **HS256** (HMAC-SHA-256); signing secret and password-stretching secrets come from **environment variables**; default JWT TTL is **30 days**, overridable by env.
- Orchestration-web: unauthenticated visitors are **redirected to login**; login collects **email + password** with client-side validation (**email format**, password **≥ 8 alphanumeric characters**); all HTTP auth concerns go through an **adapter** so the UI can swap backends later.
- Orchestration-web **attaches the JWT** to every **orchestration-server** API call (`Authorization: Bearer …`) when a token is present (**Step 8**). **Orchestration-server does not read or validate this header in this milestone**—the behavior is **future-proofing** for an inbound plane or later server-side auth.
- Tests cover auth hashing/verification and critical API behavior; web tests or E2E smoke as appropriate for the stack.

**Won’t do (this milestone)**

- Add authentication middleware or JWT validation inside **orchestration-server** (explicitly excluded).
- Replace or implement the **inbound plane** (TLS termination, OAuth at edge, mTLS, etc.).
- Full account lifecycle (registration UI, password reset email, MFA, SSO)—only what’s needed for login + token issuance unless listed in Steps.

---

## Preconditions

- **Runtime:** Python 3.11+ (aligned with other services) or Node—pick one stack for `services/auth-service/` and document it in the service README; keep dependencies minimal (e.g. FastAPI + `pyjwt` + `passlib`/`argon2-cffi`, or equivalent).
- **Deployment:** Decide where user files live (e.g. `AUTH_USERS_DIR` mounted volume in prod). Local dev uses a gitignored directory under the service or `./data/users`.
- **User file names:** Normalize the username (email: trim, lowercase), then compute a **fast** digest (e.g. **SHA-256** over UTF-8 bytes, hex-encoded) and use that string plus a fixed extension (e.g. `.json`) as the filename. This avoids reserved characters and path traversal; it is **not** for hiding emails (hash is not salted; treat as a label). Use **stdlib** `hashlib` in Python—no slow password algorithms for filenames.
- **JWT signing:** Use **HS256** only. Supply a single **shared signing secret** via environment (e.g. `JWT_SIGNING_SECRET`)—long, random, not committed. Tokens must set header `alg: HS256` and use the same secret for signing at issuance (any future verifier—e.g. inbound plane—uses this secret or a derived key distribution story documented in ops).
- **“Salt” env:** For password hashing, prefer **Argon2id** or **bcrypt** with **per-password salt** embedded in the stored hash string. A separate env var can act as **application pepper** (global secret mixed into hashing) if required—name it explicitly (e.g. `AUTH_PASSWORD_PEPPER`) to avoid confusing it with per-user salt stored in each user file.
- **Orchestration-web** can call the auth service from the **browser** (cross-origin) or via a **same-origin BFF**—precondition is CORS (if browser → auth API directly) or proxy config. Document `PUBLIC_AUTH_API_URL` (or server-only proxy) in the web service env.
- **Input handling:** Implementation must treat every value from the network, disk, or CLI as untrusted until validated—centralize rules (e.g. Pydantic models + explicit string cleanup) and document max lengths in README.

---

## Used Tools

- **Auth service:** HTTP framework (FastAPI recommended for consistency with orchestration-server), **request/response validation** (e.g. Pydantic v2) for sanitized login payloads and user records, password hashing library (Argon2id or bcrypt), JWT library with **HS256** support (e.g. PyJWT `algorithm="HS256"`).
- **Orchestration-web:** SvelteKit, existing `PUBLIC_ORCHESTRATION_API_URL` pattern in `services/orchestration-web/src/lib/api.ts`; new public env for auth base URL; `fetch` for login.
- **Tests:** `pytest` for auth service; Vitest/Playwright or SvelteKit testing utilities for web if already present—otherwise add the lightest viable test layer.
- **Lint/format:** Match each service’s existing tooling (e.g. `ruff` for Python).
- **UI design system audit:** [.cursor/skills/audit-ui-design-system/SKILL.md](.cursor/skills/audit-ui-design-system/SKILL.md) — run when changing orchestration-web UI; execute its step documents in order and fix reported issues before merge.

---

## Files touched (planned)

Inventory for implementation. **New** = add file; **Modify** = change existing file. Paths follow the layout in Steps; if the team prefers a route group (e.g. `(app)/`) for auth vs public routes, adjust filenames accordingly while keeping the same responsibilities.

| Path | Kind | Overview |
|------|------|----------|
| `services/auth-service/pyproject.toml` | New | Dependencies (FastAPI, PyJWT, hashing lib, pytest, ruff), package definition, entry points if any. |
| `services/auth-service/README.md` | New | How to run, env vars (`JWT_SIGNING_SECRET`, `AUTH_USERS_DIR`, `JWT_EXPIRES_DAYS`, CORS), HS256, user bootstrap, ops note (reverse proxy). |
| `services/auth-service/.env.example` | New | Placeholder variable names only; no real secrets. |
| `services/auth-service/.gitignore` | New | User data dir, `.env`, `__pycache__`, venv, etc. |
| `services/auth-service/auth_service/__init__.py` | New | Package marker. |
| `services/auth-service/auth_service/config.py` | New | Load settings from environment (paths, secrets, TTL, CORS origins). |
| `services/auth-service/auth_service/security.py` | New | Password hashing/verification (Argon2id/bcrypt + optional pepper), JWT creation (**HS256**). |
| `services/auth-service/auth_service/validation.py` (or inline in models) | New | Sanitized types / helpers: login body, user JSON schema, max lengths, strip dangerous characters. |
| `services/auth-service/auth_service/users.py` | New | Username normalization; **fast hash → filename** (e.g. SHA-256 hex + `.json`); load/parse JSON user record (`username`, `password_hash`, `created_at`) with **validated, sanitized fields**. |
| `services/auth-service/auth_service/app.py` | New | FastAPI app: CORS, `POST` login route, `GET` health, wire security + users; **validated** request bodies only. |
| `auth-create-user` (console script → `auth_service.cli`) | New | Operator CLI: create JSON user file (`username`, `password_hash`, `created_at`) under `AUTH_USERS_DIR`. |
| `services/auth-service/tests/conftest.py` | New | Temp `AUTH_USERS_DIR`, test `JWT_SIGNING_SECRET`, `TestClient` app fixture. |
| `services/auth-service/tests/test_security.py` | New | Unit tests: hash verify, JWT claims/exp, HS256 signature check. |
| `services/auth-service/tests/test_api.py` | New | API tests: login success/failure, malformed body, health. |
| `services/orchestration-web/src/lib/auth/types.ts` | New | Types for credentials, token response, adapter interface. |
| `services/orchestration-web/src/lib/auth/adapter.ts` | New | Default adapter: `fetch` to auth service using `PUBLIC_AUTH_API_URL`. |
| `services/orchestration-web/src/lib/auth/token.ts` | New | Single place to read/write/clear stored JWT (e.g. `sessionStorage`). |
| `services/orchestration-web/src/lib/auth/index.ts` | New | Public exports for routes and tests. |
| `services/orchestration-web/src/lib/auth/adapter.mock.ts` | New (optional) | Stub adapter for tests or local demo without auth service. |
| `services/orchestration-web/src/routes/login/+page.svelte` | New | Login UI (email/password), client validation, submit via adapter, store token, redirect. |
| `services/orchestration-web/src/routes/+layout.svelte` | Modify | Auth gate: if no valid token and not on `/login`, redirect to `/login`; allow login route through. |
| `services/orchestration-web/src/routes/+layout.ts` | New (optional) | If using `load` for redirects instead of only client-side guard—pick one pattern. |
| `services/orchestration-web/src/lib/api.ts` | Modify | **Step 8:** attach `Authorization: Bearer <jwt>` to all orchestration API requests when a token exists (`getSession`, SSE `startSession` / `sendMessage`, etc.). |
| `services/orchestration-web/README.md` | Modify | Document `PUBLIC_AUTH_API_URL`, local dev with auth service, and that **orchestration-server currently ignores** the Bearer token. |
| `services/orchestration-web/package.json` | Modify (optional) | Only if adding a test runner dep or script for adapter tests. |
| `services/orchestration-web/src/lib/auth/adapter.test.ts` | New (optional) | Mock `fetch`, assert adapter request/response handling. |
| `services/orchestration-server/README.md` | Modify | Note: orchestration-web sends `Authorization: Bearer` (**Step 8**); this service **does not** validate JWTs in this PoC. |

**Explicitly not touched:** `services/orchestration-server/backend/**/*.py` and related server code (no auth middleware per Goal).

---

## Auth service endpoints

Base URL is the deployed origin of `services/auth-service` (e.g. `http://localhost:<port>` in dev). Final path prefix is fixed at implementation time (`/auth/...` vs `/v1/...`); the table uses the `/auth` prefix from Steps.

| Method | Path | Overview |
|--------|------|----------|
| `POST` | `/auth/login` | Accepts JSON `{ "email", "password" }` (**sanitized/validated** per Step 2). Resolves user file by **fast hash of normalized email** (filename); validates password; on success returns **HS256** JWT (`access_token`, `token_type: bearer`). On failure returns `401` without distinguishing missing user vs wrong password. |
| `GET` | `/health` | Lightweight **liveness** check for orchestration and load balancers (e.g. `200` with a small JSON body such as `{ "status": "ok" }`). No authentication required. |

**Not in scope for this milestone:** registration, refresh tokens, logout/revocation, password reset, JWKS, or introspection endpoints.

---

## Steps

### 1. Auth service scaffold (`services/auth-service/`)

1. Create a new service folder under `services/auth-service/` with its own `pyproject.toml` or `requirements.txt`, `README.md` (runtime env vars, how to create the first user file), and a small package layout (e.g. `auth_service/app.py`, `auth_service/config.py`, `auth_service/validation.py`, `auth_service/users.py`, `auth_service/security.py`).
2. **Config (env):** Define settings with clear names, for example:
   - `AUTH_USERS_DIR` — absolute or relative path to the directory containing user files.
   - `JWT_SIGNING_SECRET` — shared secret for **HS256** signing (required).
   - `JWT_EXPIRES_DAYS` — default `30`, parsed as days (or `JWT_EXPIRES_SECONDS` if sub-day TTL needed later).
   - `AUTH_PASSWORD_PEPPER` (optional) — global secret combined with hashing if required by security review.
   - `AUTH_BIND_HOST` / `AUTH_PORT` or `UVICORN_*` as per convention.
3. **User file format:** One file per user, **JSON only** (e.g. `{digest}.json`). **Filename:** normalize username (trim, lowercase; email-shaped), then compute a **fast** digest—e.g. **SHA-256** of the UTF-8 string, **hex** output—and use `{digest}.json`. Document the exact algorithm in README so login and `auth-create-user` stay in sync. **Required JSON fields:**
   - **`username`** — string, normalized email-shaped identifier (same string used for filename hash input).
   - **`password_hash`** — string, **salted** password hash only (e.g. Argon2id or bcrypt full digest—no plaintext passwords).
   - **`created_at`** — creation **date/time** (ISO 8601 string in UTC recommended, e.g. `2026-04-04T12:00:00Z`).
   *(The filename hash is only for stable, cross-OS safe paths—not confidentiality.)*
4. **Hashing:** On password verification, use constant-time comparison provided by the hashing library. On user creation (CLI or admin script), hash the password and write the file to the path derived from the same **filename** hash function as login.
5. **JWT:** On successful login, issue a JWT signed with **HS256** using `JWT_SIGNING_SECRET`, with claims including `sub` = normalized email, `exp` aligned with `JWT_EXPIRES_DAYS`, `iat`, and optional `iss`/`aud` if useful for future validation. Document `alg: HS256` and env vars in README.

### 2. Auth HTTP API

1. **POST `/auth/login`** (or `/v1/login`—pick one prefix and keep it stable): JSON body `{ "email": "...", "password": "..." }`. After **sanitization** (below), normalize username (trim, lowercase), compute the **same fast filename hash** as in Step 1, open that user file if present, parse JSON, **validate/sanitize user record fields** read from disk, confirm **`username`** matches the normalized identifier, then verify **`password_hash`** against the supplied password.
2. **Sanitize and validate all inputs to the auth service** (single place in code—e.g. Pydantic models + field validators or `validation.py`):
   - **HTTP login body:** Reject non-JSON or wrong top-level shape; enforce **max sizes** (e.g. email ≤ 254 chars per RFC habit, password ≤ a generous bound e.g. 1024 bytes to limit DoS while allowing passphrases); **strip** surrounding whitespace on email; reject **NUL** (`\0`) and other disallowed control characters in strings; require UTF-8 decodable payloads (return `422` when invalid).
   - **Email/username identifier:** After strip/lowercase, validate **email-shaped** pattern (same rules as product); reject empty or over-long values before filesystem use.
   - **Password (plaintext at verify time):** Treat as opaque UTF-8 bytes/string with max length only—no HTML/log echo of raw password.
   - **Filesystem:** Build paths **only** as `join(AUTH_USERS_DIR, f"{hex_digest}.json")` using **your own** hex digest from the normalized username—never concatenate raw user input into paths.
   - **User JSON loaded from disk:** After `json.load`, validate types (`username`/`password_hash`/`created_at` are strings of bounded length); **`password_hash`** must match expected hash string charset (e.g. bcrypt/argon prefix); parse **`created_at`** strictly (ISO 8601) or reject file; reject extra keys only if you choose strict schema—document choice.
   - **CLI (`auth-create-user`):** Apply the **same** normalization and length rules as login for username; read passwords safely (no argv logging); optional stdin with confirm for production scripts.
3. Responses: `200` with `{ "access_token": "<jwt>", "token_type": "bearer" }` (or similar); `401` for bad credentials; `422` for malformed body; `500` only for unexpected errors (no stack traces in responses).
4. **CORS:** If orchestration-web calls this service directly from the browser, enable CORS for known origins (mirror orchestration-server’s pattern from `backend/config.py` / env) or document that the browser must use a same-origin proxy instead.
5. **Health:** `GET /health` (or `/healthz`) for orchestration/load checks (no user-controlled input).

### 3. User bootstrap (operator workflow)

1. Ship a **CLI** (e.g. `auth-create-user` → `auth_service.cli`) to create a user file: inputs email + password (stdin or args), normalize username, derive filename via the **same fast hash** as runtime, compute salted `password_hash`, set `created_at` to now, write `{digest}.json` with **`username`**, **`password_hash`**, **`created_at`**. Alternatively document manual JSON creation with a helper command—prefer script to avoid mistakes.
2. Document in service README: **never** commit real user files; `.gitignore` the users directory.

### 4. Orchestration-server (explicit non-changes)

1. **Do not** add auth dependencies, JWT middleware, or `Authorization` parsing to `services/orchestration-server/backend/app.py` or routers for this milestone.
2. Add a **short note** in orchestration-server README: traffic may be authenticated upstream; **this PoC does not validate `Authorization: Bearer`** on orchestrator routes even though orchestration-web **sends** the JWT (**Step 8**) for future use.

### 5. Orchestration-web — adapter and token handling

1. **Adapter pattern:** Add `services/orchestration-web/src/lib/auth/` (or `src/lib/adapters/auth/`) with:
   - An interface/type describing **login**(credentials) → token (or error).
   - A **default implementation** that calls the auth service HTTP API using `PUBLIC_AUTH_API_URL` (or `$env/static/public` equivalent). No orchestration API URLs inside the adapter.
   - A **stub/mock** implementation for tests or local demo (optional but keeps swap story real).
2. **Token storage:** Store the JWT in **sessionStorage** or **localStorage** (plus in-memory if needed), with a short comment that httpOnly cookies are a deployment follow-up. **One module** owns read/write/clear of the token. **Step 8** wires this token into orchestration `fetch` calls via `Authorization: Bearer` (server ignores it until a later milestone).
3. **Validation (client):** Before calling the adapter:
   - Email: valid email shape (HTML5-style regex or a small validator; align with “username as email”).
   - Password: **at least 8 characters**, **alphanumeric only** (reject spaces/symbols if that is the literal rule—if “alphanumeric” was meant loosely, confirm product intent; otherwise implement `[a-zA-Z0-9]{8,}` or similar).

### 6. Orchestration-web — routes and guards

1. Add a **`/login` route** (e.g. `src/routes/login/+page.svelte`) with a form (email, password) using existing design tokens from `tokens.css` and existing patterns; **if a new standalone login component is required**, follow `.cursor/rules/frontend-design-system.mdc`: prefer composing existing primitives; obtain approval if introducing a new shared `.svelte` component.
2. **Layout guard:** In `src/routes/+layout.svelte` (or a nested layout wrapping authenticated pages), check for a valid token:
   - If missing/invalid and the route is not `/login` (and static assets), **redirect** to `/login` using SvelteKit’s `goto` from `onMount`/`$effect` or a **`+layout.ts` load** that runs in the browser—pick the idiomatic SvelteKit 2 pattern already used in the repo.
3. **Post-login:** After successful login, persist token and **redirect** to the main app (`/` or `/session/...` as appropriate).
4. **Logout (minimal):** Clear token and redirect to `/login` (button or dev-only control acceptable for PoC).

### 7. Orchestration-web — design system audit

After login, layout guard, and any other **orchestration-web** UI or global style changes for this feature:

1. Run the **[audit-ui-design-system](.cursor/skills/audit-ui-design-system/SKILL.md)** workflow: read `SKILL.md`, then execute its **step files in order** (e.g. [steps/01-semantics.md](.cursor/skills/audit-ui-design-system/steps/01-semantics.md)), scoped to the touched surfaces—at minimum `services/orchestration-web/src/routes/login/`, `services/orchestration-web/src/routes/+layout.svelte`, and `services/orchestration-web/src/lib/styles/**` if modified; widen to `services/orchestration-web/**/*.svelte` if the skill’s default scope is appropriate.
2. Produce or review the **findings report** (token semantics vs [.cursor/design/tokens.md](.cursor/design/tokens.md), undocumented `var(--*)`, literals, etc., per the skill).
3. **Address every finding** before considering the UI work complete: fix token usage, document new named tokens in `.cursor/design/tokens.md` and `tokens.css` when adding first use, and align with [.cursor/rules/frontend-design-system.mdc](.cursor/rules/frontend-design-system.mdc). Re-run the audit if substantial edits follow.

### 8. Attach JWT to orchestration-server calls (future-proofing)

**Implement** in `services/orchestration-web/src/lib/api.ts`: for every request to **`PUBLIC_ORCHESTRATION_API_URL`** (including **`fetch`** and **SSE** `streamSSE` used by `getSession`, `startSession`, `sendMessage`), add `Authorization: Bearer <access_token>` when the stored JWT is present (read via the token module from Step 5—no duplicate storage logic in `api.ts`).

- **Purpose:** When orchestration-server or an inbound proxy later validates JWTs, the client is already sending the token; no separate “wire auth header” milestone.
- **Current behavior:** **Orchestration-server does not inspect `Authorization`** in this milestone (see Step 4). The header is **inert** server-side—document this in **orchestration-web** and **orchestration-server** READMEs so operators are not surprised.
- **CORS:** If `allow_credentials` and fixed origins are required later for cookie-based flows, note it as follow-up; Bearer in a header from the SPA is the pattern here.

### 9. Tests and docs

1. **Auth service unit tests:** Password hash/verify round-trip, wrong password, missing user file, **deterministic filename from username** (same input → same path), **valid/invalid user JSON** (required `username`, `password_hash`, `created_at`), JWT claims/exp, and signature verification with **HS256** + same secret.
2. **Auth service API tests:** Login success/failure via `TestClient`; **oversized/malformed bodies**; NUL in strings; invalid JSON; path-safe behavior (no escape from `AUTH_USERS_DIR`).
3. **Web:** Smoke test login adapter with mocked `fetch` if no E2E harness; optional unit/integration check that **`api.ts` adds `Authorization`** when a token is set (mock token module).
4. **Root-level ops note:** In auth service README, describe how a reverse proxy would sit in front of orchestration-web and orchestration-server in production; auth service URL exposed only where needed.

---

## TODOs and codebase markers

- Searched orchestration area: existing `TODO`s in `prompts.py` and `openai_client.py` are **unrelated** to auth; no merge required into this plan.
- If new TODOs are added during implementation, tie them to **Follow-ups** below rather than orphan comments.

---

## Guardrails

- **Secrets:** No secrets or real user files committed; `.gitignore` user data dirs; example env in `.env.example` only with placeholders.
- **JWT:** Issue and verify (in tests or docs) with **HS256** only; reject unexpected `alg` if adding verification later.
- **Password storage:** JSON `password_hash` field only—salted hashes (Argon2id/bcrypt), not custom crypto; never store plaintext passwords.
- **User JSON schema:** Every user file includes **`username`**, **`password_hash`**, **`created_at`**; reject or migrate records missing required keys.
- **User file paths:** Filename = fast hash (e.g. SHA-256 hex) of normalized email; algorithm fixed and documented; normalize email before hashing so lookups are stable. Cryptographic collision resistance of SHA-256 is sufficient for accidental collision avoidance; this is **not** a substitute for password hashing.
- **Input sanitization:** All auth service entry points apply Step 2 rules; no raw client or file data trusted without validation; document limits in README.
- **Orchestration-server boundary:** No auth logic added there for this feature; orchestration-web still **sends** `Authorization: Bearer` per **Step 8**—document that the server **ignores** it until a later milestone.
- **Frontend:** Auth **login** only through the **adapter**; `api.ts` imports the **token** helper to attach Bearer to orchestration calls—do not duplicate auth service URLs inside `api.ts`.
- **Quality:** Run linters/tests for touched services before merge; manual smoke: login, refresh page (token persists per chosen storage), access app, logout.
- **Design system:** Complete Step 7 (audit-ui-design-system skill) for orchestration-web UI changes; no unresolved audit findings before merge.

---

## Follow-ups / deferred work

- httpOnly cookie-based sessions and CSRF strategy for browser-only deployments.
- Asymmetric signing (e.g. RS256) and JWKS if multiple services must verify tokens without sharing a symmetric secret.
- Server-side session revocation list and password reset flows.
- Orchestration-server **JWT validation** when product requires defense in depth (client already sends Bearer per **Step 8**).
