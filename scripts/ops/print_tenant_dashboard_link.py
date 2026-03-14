#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dashboard config must be a JSON object")
    tenants = payload.get("tenants")
    if not isinstance(tenants, list):
        raise ValueError("dashboard config must contain a tenants list")
    return payload


def _find_tenant(payload: dict, tenant_id: str) -> dict:
    for row in payload.get("tenants", []):
        if isinstance(row, dict) and str(row.get("tenant_id") or "").strip() == tenant_id:
            return row
    raise ValueError(f"tenant_id not found: {tenant_id}")


def _normalize_base_url(url: str) -> str:
    out = str(url or "").strip().rstrip("/")
    if not out:
        raise ValueError("--base-url is required")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Print tenant dashboard link from tenant config")
    parser.add_argument("--tenant-id", required=True, help="Tenant ID")
    parser.add_argument("--base-url", required=True, help="Base URL, e.g. https://surfit.example.com")
    parser.add_argument("--config", default="tenants/dashboard_access.json", help="Path to tenant dashboard config")
    args = parser.parse_args()

    config_path = Path(args.config)
    payload = _load_config(config_path)
    tenant = _find_tenant(payload, args.tenant_id)

    key = str(tenant.get("dashboard_access_key") or "").strip()
    if not key:
        raise ValueError("dashboard_access_key is missing for tenant")

    base_url = _normalize_base_url(args.base_url)
    link = f"{base_url}/tenant-dashboard?k={key}"

    print(f"tenant_id={args.tenant_id}")
    print(f"display_name={str(tenant.get('display_name') or '').strip() or args.tenant_id}")
    print(f"key_expires_at={tenant.get('key_expires_at')}")
    print(f"tenant_dashboard_url={link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
