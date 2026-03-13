#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/root/surfit}"
BACKUP_DIR="${BACKUP_DIR:-/root/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "Missing $APP_DIR/.env"
  exit 1
fi

set -a
source .env
set +a

: "${POSTGRES_DB:?POSTGRES_DB is required in .env}"
: "${POSTGRES_USER:?POSTGRES_USER is required in .env}"

mkdir -p "$BACKUP_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$BACKUP_DIR/${POSTGRES_DB}_${TS}.sql.gz"

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$OUT"

find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete: $OUT"
