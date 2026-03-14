# Surfit Deployment Recovery Runbook

Last updated: March 14, 2026

This runbook is the operator source of truth for deploy, recovery, validation, and rollback of Surfit on Hetzner.

## Scope

- Host: Hetzner Ubuntu 24.04
- Server IP: `46.62.145.237`
- Stack: `surfit-api`, `surfit-nginx`, `surfit-postgres`, `surfit-redis`
- Compose reality on this host: `docker-compose` v1 (not `docker compose` v2)

## 1) Environment Identification (Do This First)

Run these checks before any command block.

### Local Mac checks

```bash
hostname
whoami
pwd
```

Expected: your Mac host/user and a path like `/Users/...`.

### Hetzner server checks

```bash
ssh root@46.62.145.237
hostname
whoami
pwd
```

Expected: host like `surfit-mvp`, user `root`, path usually `/root`.

Never run `/root/surfit` commands from local Mac.

## 2) Golden Deploy Flow

### A. Local machine (code sync)

```bash
cd ~/Desktop/files
git status
git add <changed-files>
git commit -m "<message>"
git push origin main
```

### B. Server deploy

```bash
ssh root@46.62.145.237
cd /root/surfit
git pull --ff-only origin main
cp -f .env.example .env
nano .env
```

Set required keys in `.env`:

- `SURFIT_ENV=prod`
- `SURFIT_API_PORT=8000`
- `SURFIT_REQUIRE_EXPLICIT_PROD_CONFIG=1`
- `SURFIT_TOKEN_SECRET`
- `SURFIT_API_KEYS_JSON`
- `SURFIT_DEFAULT_TENANT_ID` (not `tenant_demo`)
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `SURFIT_POLICY_ALLOWLISTS_PATH=/app/policies/allowlists.json`

Bring stack up:

```bash
cd /root/surfit
docker-compose up -d --build
```

## 3) Health Verification Block

```bash
cd /root/surfit
docker-compose ps
curl -s http://localhost/healthz | python3 -m json.tool
curl -s http://localhost/readyz | python3 -m json.tool
```

Good state:

- `surfit-api` = `Up (healthy)`
- `surfit-nginx` = `Up`
- `surfit-postgres` = `Up (healthy)`
- `surfit-redis` = `Up (healthy)`
- `/healthz.status` = `ok`
- `/readyz.status` = `ready`

## 4) Common Failure Modes

### A) Local vs server shell confusion

Symptom:

- `cd: /root/surfit: no such file or directory`
- `docker-compose: command not found` (on Mac)

Cause: server commands run in local shell.

Fix:

```bash
ssh root@46.62.145.237
cd /root/surfit
```

Verify: `hostname`, `pwd`, `whoami`.

### B) Missing deployment files in repo

Symptom:

- `Can't find a suitable configuration file`

Cause: `docker-compose.yml` or related files not committed/pulled.

Fix:

```bash
cd /root/surfit
git pull --ff-only origin main
ls -la docker-compose.yml Dockerfile .env.example nginx.conf
```

Verify: files exist in `/root/surfit`.

### C) `docker-compose` vs `docker compose` mismatch

Symptom:

- `docker: unknown command: docker compose`

Cause: host only has Compose v1.

Fix: use `docker-compose` commands on this host.

Verify:

```bash
docker-compose version
```

### D) Prod startup blocked by missing policy manifest

Symptom:

- API startup fails with strict prod config error mentioning `SURFIT_POLICY_ALLOWLISTS_PATH`.

Cause: `/app/policies/allowlists.json` missing.

Fix:

```bash
cd /root/surfit
mkdir -p policies
ls -la policies/allowlists.json
```

If missing, create/populate `policies/allowlists.json` then restart:

```bash
docker-compose up -d --build
```

Verify: `/readyz.checks.policy_manifest_path.ready` is `true`.

### E) Postgres auth mismatch / stale volume

Symptom:

- `/readyz` returns `database.ready=false`
- detail contains `password authentication failed`

Cause:

- `POSTGRES_PASSWORD` and `DATABASE_URL` mismatch
- changed password after volume init

Fix: see Section 5 (destructive reset).

Verify: `/readyz.checks.database.ready` is `true`.

### F) Malformed `.env`

Symptom:

- `Python-dotenv could not parse statement starting at line 1/2`

Cause:

- junk lines (e.g. pasted shell commands) or invalid format.

Fix:

```bash
cd /root/surfit
sed -i '/^cd \/root\/surfit$/d;/^nano \.env$/d' .env
perl -i -pe 's/^\x{FEFF}//' .env
nl -ba .env | sed -n '1,30p'
```

Verify: no parse warnings on `docker-compose ps`.

### G) Broken `surfit/connectors/adapter_registry.py`

Symptom:

- API crash with `SyntaxError: 'return' outside function`

Cause: malformed Python file in deploy branch.

Fix:

```bash
cd /root/surfit
python3 -m py_compile surfit/connectors/adapter_registry.py
```

If compile fails, restore file from known-good commit or replace with valid module content.

Verify:

```bash
docker-compose logs --tail=120 surfit-api
```

### H) Nginx unhealthy because API is down

Symptom:

- `ERROR: for nginx Container "..." is unhealthy`
- upstream 502/503 via nginx

Cause: API boot failure (config/import/startup crash).

Fix:

1. Fix API root cause first.
2. Recreate stack:

```bash
cd /root/surfit
docker-compose down --remove-orphans
docker-compose up -d --build
```

Verify: API healthy and `/readyz` ready.

## 5) Postgres Auth + Volume Reset Procedure (Destructive)

Use this only when `/readyz` shows Postgres auth failure after env change.

1) Confirm mismatch:

```bash
cd /root/surfit
curl -s http://localhost/readyz | python3 -m json.tool
grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|DATABASE_URL)=' .env
```

2) Fix `.env` values:

- `POSTGRES_PASSWORD` must match `DATABASE_URL` password.
- If password has special chars, URL-encode in `DATABASE_URL`.
  - `#` -> `%23`
  - `!` -> `%21`

3) Destructive reset (recreates DB data volume):

```bash
cd /root/surfit
docker-compose down
docker volume rm surfit_postgres_data
docker-compose up -d --build
```

4) Verify:

```bash
curl -s http://localhost/readyz | python3 -m json.tool
```

## 6) Policy Manifest Requirement

Prod startup requires policy file resolved at:

- env: `SURFIT_POLICY_ALLOWLISTS_PATH`
- expected container path: `/app/policies/allowlists.json`

Server check:

```bash
cd /root/surfit
ls -la policies/allowlists.json
grep '^SURFIT_POLICY_ALLOWLISTS_PATH=' .env
```

Container check:

```bash
docker-compose exec surfit-api ls -la /app/policies/allowlists.json
```

## 7) `.env` Rules

Required keys:

- `SURFIT_ENV`
- `SURFIT_API_PORT`
- `SURFIT_REQUIRE_EXPLICIT_PROD_CONFIG`
- `SURFIT_TOKEN_SECRET`
- `SURFIT_API_KEYS_JSON`
- `SURFIT_DEFAULT_TENANT_ID`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `SURFIT_POLICY_ALLOWLISTS_PATH`

Rules:

- rotate secrets immediately after incident response
- do not keep placeholder values in prod
- URL-encode special chars in `DATABASE_URL` password
- no shell commands/junk lines inside `.env`

## 8) Firewall / Backup / Logging Baseline

### UFW baseline

```bash
cd /root/surfit
bash scripts/ops/setup_ufw.sh
```

Expected inbound allows:

- `22/tcp`
- `80/tcp`
- `443/tcp`

Everything else inbound denied.

### Backups

Manual backup:

```bash
cd /root/surfit
bash scripts/ops/postgres_backup.sh
```

Output path:

- `/root/backups/postgres`

Cron install:

```bash
cd /root/surfit
bash scripts/ops/install_postgres_backup_cron.sh
```

### Logging

- Compose has per-service log rotation config.
- Optional host daemon log rotation script:

```bash
cd /root/surfit
bash scripts/ops/configure_docker_log_rotation.sh
```

Note: daemon script restarts Docker.

## 9) Rollback Block

Use when latest deploy is unstable.

```bash
cd /root/surfit
PREV_COMMIT=$(git rev-parse HEAD~1)
git checkout "$PREV_COMMIT"
docker-compose down --remove-orphans
docker-compose up -d --build
docker-compose ps
curl -s http://localhost/readyz | python3 -m json.tool
```

To return to main later:

```bash
cd /root/surfit
git checkout main
git pull --ff-only origin main
docker-compose up -d --build
```

## 10) Operator Checklists

### Fast deploy checklist

- [ ] Confirm shell context with `hostname`, `whoami`, `pwd`
- [ ] `git push` from local
- [ ] `git pull --ff-only` on server
- [ ] Validate `.env` keys and formatting
- [ ] `docker-compose up -d --build`
- [ ] `/healthz` = ok
- [ ] `/readyz` = ready

### Fast recovery checklist

- [ ] Identify first failing symptom from logs
- [ ] Verify `adapter_registry.py` compiles
- [ ] Verify policy manifest file exists
- [ ] Verify `.env` parse integrity
- [ ] Verify DB auth alignment; reset volume only if auth mismatch persists
- [ ] Rebuild + verify health/readiness

## 11) Current Known Good Snapshot

As of this runbook update, known-good runtime result:

- `docker-compose ps` shows all 4 services up and healthy
- `GET /healthz` returns `status: ok`
- `GET /readyz` returns `status: ready`

## 12) Dashboard Key Expiry Ops Loop

Use this to prevent tenant dashboard link lockouts.

### Install daily check

```bash
cd /root/surfit
bash scripts/ops/install_dashboard_key_expiry_cron.sh
```

Default schedule: `08:00 UTC` daily.

### Run on demand

```bash
cd /root/surfit
bash scripts/ops/run_dashboard_key_expiry_check.sh
```

Log path:

- `/var/log/surfit/dashboard_key_expiry.log`

Exit semantics from checker:

- `0`: no warnings
- `1`: warning keys present (expiring soon)
- `2`: expired keys present

Operator SLA:

- `WARNING`: rotate affected keys within 48 hours.
- `EXPIRED`: rotate immediately and reissue tenant dashboard link.
