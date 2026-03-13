#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/root/surfit}"
cd "$APP_DIR"

PREV_COMMIT="$(git rev-parse HEAD)"
echo "Current commit: $PREV_COMMIT"

git pull --ff-only origin main

docker compose up -d --build

docker compose ps

echo "Running smoke checks..."
curl -fsS http://localhost/healthz >/dev/null
curl -fsS http://localhost/readyz >/dev/null

echo "Deploy complete."
echo "Rollback hint: git checkout $PREV_COMMIT && docker compose up -d --build"
