#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

APP_DIR="${APP_DIR:-/root/surfit}"
CRON_LINE="15 2 * * * $APP_DIR/scripts/ops/postgres_backup.sh >> /var/log/surfit-postgres-backup.log 2>&1"

( crontab -l 2>/dev/null | grep -v "surfit-postgres-backup"; echo "$CRON_LINE" ) | crontab -

echo "Installed cron job: $CRON_LINE"
