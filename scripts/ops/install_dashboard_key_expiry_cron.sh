#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

APP_DIR="${APP_DIR:-/root/surfit}"
CRON_EXPR="${SURFIT_DASHBOARD_KEY_CRON_EXPR:-0 8 * * *}"
RUNNER="$APP_DIR/scripts/ops/run_dashboard_key_expiry_check.sh"
CRON_TAG="surfit-dashboard-key-expiry"
CRON_LINE="$CRON_EXPR APP_DIR=$APP_DIR $RUNNER # $CRON_TAG"

( crontab -l 2>/dev/null | grep -v "$CRON_TAG"; echo "$CRON_LINE" ) | crontab -

echo "Installed cron job: $CRON_LINE"
echo "Log file: /var/log/surfit/dashboard_key_expiry.log"
