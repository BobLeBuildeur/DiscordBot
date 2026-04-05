# HTTP admin flows (create user, reset password)

Optional endpoints under `/auth` for operators or integrated tools. **Use TLS in production**; responses include a **one-time plaintext password**.

## Create user (`POST /auth/users`)

Disabled unless `AUTH_HTTP_CREATE_USER_ENABLED=true`. When disabled, the service returns **403**.

```mermaid
flowchart TD
  createReq[POST /auth/users]
  envGate[AUTH_HTTP_CREATE_USER_ENABLED]
  createReq --> envGate
  envGate -->|false| denyCreate[403]
  envGate -->|true| exists{user file exists?}
  exists -->|yes| conflict[409]
  exists -->|no| writeUser[Write user JSON role analyst]
```

Body: `{ "username": "<email-shaped>" }`. Response **201**: `{ "username", "password" }` (random 8 alphanumeric characters).

## Reset password (`POST /auth/users/reset-password`)

Requires `Authorization: Bearer <JWT>` issued by this service. **Authorization:** the token’s `sub` (normalized) must equal the body `username`, **or** the token’s `role` must be `admin`.

```mermaid
flowchart TD
  resetReq[POST /auth/users/reset-password]
  jwt[JWT Bearer]
  authz{sub equals target or role admin}
  resetReq --> jwt
  jwt -->|missing or invalid| u401[401]
  jwt --> authz
  authz -->|no| u403[403]
  authz -->|yes| userExists{user on disk?}
  userExists -->|no| u404[404]
  userExists -->|yes| updateHash[Update password_hash]
```

Body: `{ "username": "<email-shaped>" }`. Response **200**: `{ "username", "password" }` (new random 8 alphanumeric characters).
