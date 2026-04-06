# Manual Droplet + GitHub Actions CD (no IaC, no Docker)

## Goal

Run the full stack on **one manually provisioned VM** (e.g. DigitalOcean Droplet) with **nginx** as the only public HTTP(S) edge, and **deploy updates** by a **GitHub Actions workflow** that SSHs in, pulls **`main`**, installs dependencies (**npm**, **pip**), and starts services.

**Services on the VM:**

| Role | Component |
|------|-----------|
| Front controller / API gateway | **nginx** |
| Web UI | **orchestration-web** |
| APIs | **orchestration-server**, **auth-service** |
| MCP | **books-mcp** (used by orchestration per `config/mcp-registry.json`) |

**Success:** Pushes to **`main`** trigger CD that refreshes the repo on the server and restarts processes without Docker or Terraform.

**Out of scope (explicit):**

- **IaC / Terraform** — Droplet is created and configured **manually** (or by ad-hoc scripts not tracked as product IaC here).
- **Docker** — Processes run on the host with **Python venvs** and **Node** as in local dev docs.
- **CI** — No lint/test gates in this workstream.

---

## Preconditions

1. **VM** (Ubuntu LTS recommended) with a **deploy user** (e.g. `deploy`) and SSH key-based login for GitHub Actions.
2. **Repository** cloned once on the server to a fixed path (e.g. `/opt/orchestration` or `/home/deploy/app`) pointing at this monorepo; `main` is the deploy branch.
3. **Toolchains:** Node **20.19+** or **22.12+** (per `orchestration-web` README), **Python 3.11+** for Python services; **nginx** installed; optional **certbot** for Let’s Encrypt if you terminate TLS on nginx.
4. **Secrets:** API keys and JWT secrets provided via **environment files** or **systemd `EnvironmentFile=`** (not committed). GitHub Actions uses **repository secrets** for SSH private key and optionally for copying env content if you automate that.
5. **Networking:** Firewall (host or cloud) allows **22** (SSH, restrict to GitHub Actions egress IPs if practical), **80**/**443** for nginx. Python services listen on **127.0.0.1** only; **nginx** proxies to them.

---

## Used Tools

| Tool | Role |
|------|------|
| **nginx** | TLS (optional), static or `proxy_pass` to Node, reverse proxy for `/orchestrator` and auth routes |
| **systemd** (recommended) | One **unit per long-running service** (orchestration-server, auth-service, orchestration-web if using adapter-node, books-mcp only if run as standalone—see below) |
| **Python venv** | `pip install -e` for `services/orchestration-server`, `services/auth-service`, `services/books-mcp` |
| **npm** | `npm ci` / `npm run build` in `services/orchestration-web` |
| **GitHub Actions** | On `push` to `main`: SSH → `git pull` → install deps → start/restart services |

---

## Architecture (single VM)

- **Internet → nginx (80/443)** → UI (static files or local Node) and **proxy_pass** to **127.0.0.1:8000** (orchestration), **127.0.0.1:8090** (auth), etc., matching your nginx `location` blocks.
- **books-mcp:** Today the orchestrator spawns **`python -m books_mcp`** with cwd under the repo (`config/mcp-registry.json`). On the VM, ensure the registry paths resolve from the clone and venv so **`books_mcp`** is importable (venv activation or `PATH`). No separate “start books-mcp” process is required unless you change that integration.

---

## One-time manual provisioning (operator checklist)

1. Create Droplet, add SSH keys, configure firewall (80, 443, 22).
2. Install: `nginx`, `git`, `certbot` (if using Let’s Encrypt), Node (nvm or distro), Python 3 + `python3-venv`.
3. Create deploy user, clone repo to **`DEPLOY_ROOT`**, `git checkout main`.
4. Create Python venvs (one shared venv under `DEPLOY_ROOT/.venv` or per-service venvs) and run `pip install -e` from each `services/*/pyproject.toml` as needed.
5. In `services/orchestration-web`, add `.env` for production **`PUBLIC_*`** URLs (same origin as nginx HTTPS URL).
6. Configure **nginx** server blocks: root or `proxy_pass` for UI; `proxy_pass` for API paths; optional SSL `listen 443 ssl` with cert paths from certbot.
7. Create **systemd units** (or a single wrapper script invoked by systemd) that:
   - `WorkingDirectory=` the service directory under the clone
   - `EnvironmentFile=` a root-only file with secrets
   - `ExecStart=` `uvicorn ... --host 127.0.0.1 --port ...` for Python services; for web, either **`npm run preview`** / **node** with adapter-node on `127.0.0.1`, or **`adapter-static`** + nginx `root` only
8. `systemctl enable --now` each unit; verify only nginx listens on public interfaces.

---

## GitHub Actions workflow (CD only)

**Trigger:** `push` to `main` (and optionally `workflow_dispatch` for manual redeploy).

**Steps:**

1. **SSH into the droplet** using a private key stored in **GitHub Secrets** (`SSH_PRIVATE_KEY`, `KNOWN_HOSTS`, `DEPLOY_HOST`, `DEPLOY_USER`).
2. **`cd $DEPLOY_ROOT && git fetch origin && git checkout main && git pull --ff-only`**
3. **Install dependencies**
   - `services/orchestration-web`: `npm ci` (or `npm install`) and `npm run build` if the web app is built on the server
   - Python services: activate venv(s) and `pip install -e .` for each changed package, or a single script that reinstalls all three
4. **Start services** — Prefer **`systemctl restart`** on named units (e.g. `orchestration-server`, `auth-service`, `orchestration-web`) rather than raw `nohup`, so restarts are reliable and logged.

**Minimal example shape (illustrative):**

```yaml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.DEPLOY_SSH_PRIVATE_KEY }}
      - name: Deploy
        run: |
          ssh -o StrictHostKeyChecking=yes "${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }}" <<'EOF'
            set -euo pipefail
            cd "${DEPLOY_ROOT}"
            git fetch origin main && git checkout main && git pull --ff-only
            # npm + pip steps; then:
            sudo systemctl restart orchestration-server auth-service orchestration-web
            sudo nginx -t && sudo systemctl reload nginx
          EOF
```

Adjust `DEPLOY_ROOT` via secret or a small env file on the server.

---

## Secure environment variables

- Keep production `.env` or `/etc/orchestration/*.env` with mode **600**, owner root or deploy user, referenced by **systemd `EnvironmentFile=`**.
- Do **not** commit secrets. GitHub Actions should not echo env files in logs.
- Rotating keys: edit the env file on the VM and `systemctl restart` affected units.

---

## Guardrails

- **Bind backends to 127.0.0.1** so nothing except nginx is reachable from the internet on app ports.
- **nginx -t** before **reload** in the workflow after config changes.
- **git pull --ff-only** avoids surprise merge commits; protect `main` if you require linear history.
- Document **Python path** for `books_mcp` so orchestration discovery succeeds after deploy.

---

## Follow-ups (deferred)

- IaC/Terraform when you want reproducible infra.
- Docker/Compose when you want stronger isolation and repeatable images.
- CI (tests/lint) before deploy.

---

## Summary

**Manually** provision one VM with nginx and toolchains; run **orchestration-web**, **orchestration-server**, **auth-service**, and **books-mcp** (via orchestration) using **venv + systemd**, with **nginx** as gateway. **GitHub Actions** on **`main`** SSHs in, **pulls**, **npm/pip installs**, and **restarts** services—no Terraform, no Docker, no CI in this workstream.
