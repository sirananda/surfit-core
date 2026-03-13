#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

mkdir -p /etc/docker
if [[ -f /etc/docker/daemon.json && "${FORCE:-0}" != "1" ]]; then
  echo "/etc/docker/daemon.json already exists. Review manually or rerun with FORCE=1."
  exit 1
fi

cp -f /etc/docker/daemon.json "/etc/docker/daemon.json.bak.$(date +%s)" 2>/dev/null || true
cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "5"
  }
}
JSON

systemctl restart docker

echo "Docker log rotation configured."
