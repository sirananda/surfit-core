#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/root/surfit}"
LOG_DIR="${SURFIT_LOG_DIR:-/var/log/surfit}"
LOG_FILE="${SURFIT_DASHBOARD_KEY_EXPIRY_LOG:-$LOG_DIR/dashboard_key_expiry.log}"
THRESHOLD_DAYS="${SURFIT_DASHBOARD_KEY_THRESHOLD_DAYS:-7}"
CHECK_SCRIPT="$APP_DIR/scripts/ops/check_dashboard_key_expiry.py"
WEBHOOK_URL="${SURFIT_OPS_WEBHOOK_URL:-}"

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

if [[ ! -f "$CHECK_SCRIPT" ]]; then
  {
    printf '[%s] [ERROR] Missing check script: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$CHECK_SCRIPT"
  } | tee -a "$LOG_FILE"
  exit 2
fi

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
TEXT_OUT="$(python3 "$CHECK_SCRIPT" --config "$APP_DIR/tenants/dashboard_access.json" --threshold-days "$THRESHOLD_DAYS" 2>&1)"
STATUS=$?
set -e

SUMMARY="OK"
if [[ $STATUS -eq 1 ]]; then
  SUMMARY="WARNING"
elif [[ $STATUS -eq 2 ]]; then
  SUMMARY="EXPIRED"
fi

{
  printf '\n[%s] [DASHBOARD_KEY_EXPIRY_CHECK] status=%s exit_code=%s threshold_days=%s\n' "$TS" "$SUMMARY" "$STATUS" "$THRESHOLD_DAYS"
  printf '%s\n' "$TEXT_OUT"
} | tee -a "$LOG_FILE"

if [[ -n "$WEBHOOK_URL" && $STATUS -ne 0 ]]; then
  PAYLOAD=$(printf '{"source":"surfit-dashboard-key-expiry","timestamp":"%s","status":"%s","exit_code":%s}' "$TS" "$SUMMARY" "$STATUS")
  curl -sS -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d "$PAYLOAD" >/dev/null || true
fi

exit $STATUS
