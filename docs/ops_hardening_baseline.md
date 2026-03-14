# Surfit Ops Hardening Baseline (Hetzner Ubuntu 24.04)

## 1) Production env requirements

Set these values in `.env` before deploy:

- `SURFIT_ENV=prod`
- `SURFIT_REQUIRE_EXPLICIT_PROD_CONFIG=1`
- `SURFIT_TOKEN_SECRET` (high-entropy)
- `SURFIT_API_KEYS_JSON` (explicit API key -> tenant map)
- `SURFIT_DEFAULT_TENANT_ID` (must not be `tenant_demo`)
- `POSTGRES_PASSWORD`, `DATABASE_URL`
- `REDIS_URL`

Immediate rotation required:

- Any placeholder values from `.env.example`
- Any previously shared API keys
- Any token secret ever committed or copied in chat

## 2) UFW baseline

```bash
cd /root/surfit
bash scripts/ops/setup_ufw.sh
```

Rollback if lockout risk (from server console):

```bash
ufw disable
```

## 3) Docker logs rotation

Compose already sets per-service log rotation. Optionally enforce daemon default:

```bash
cd /root/surfit
bash scripts/ops/configure_docker_log_rotation.sh
```

## 4) PostgreSQL backups

Manual backup:

```bash
cd /root/surfit
bash scripts/ops/postgres_backup.sh
```

Install daily cron (02:15 UTC, keep 7 days):

```bash
cd /root/surfit
bash scripts/ops/install_postgres_backup_cron.sh
```

Restore (basic):

```bash
gunzip -c /root/backups/postgres/<file>.sql.gz | docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

## 5) Dashboard key expiry monitoring

Run once:

```bash
cd /root/surfit
bash scripts/ops/run_dashboard_key_expiry_check.sh
```

Install daily cron (08:00 UTC):

```bash
cd /root/surfit
bash scripts/ops/install_dashboard_key_expiry_cron.sh
```

Log output path:

- `/var/log/surfit/dashboard_key_expiry.log`

SLA:

- `WARNING`: rotate within 48 hours
- `EXPIRED`: rotate immediately and reissue dashboard link

## 6) Deploy helper

```bash
cd /root/surfit
bash deploy.sh
```

## 7) Health checks

- Liveness: `GET /healthz`
- Readiness: `GET /readyz` (checks db, redis, policy manifest path)

## 8) Remaining risks

- Single-node deployment (no HA)
- No centralized metrics/alerts yet
- Secrets still env-file based (acceptable for current beta, not final)
