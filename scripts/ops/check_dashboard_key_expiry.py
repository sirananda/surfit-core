#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _parse_iso(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_tenants(config_path: Path) -> list[dict]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dashboard config must be a JSON object")
    tenants = payload.get("tenants")
    if not isinstance(tenants, list):
        raise ValueError("dashboard config must contain a tenants list")
    return [row for row in tenants if isinstance(row, dict)]


def _entry_name(row: dict) -> str:
    display = str(row.get("display_name") or "").strip()
    tenant_id = str(row.get("tenant_id") or "").strip()
    return display or tenant_id or "unknown-tenant"


def _evaluate(tenants: list[dict], threshold_days: int, now: datetime) -> tuple[list[dict], int]:
    results: list[dict] = []
    worst = 0

    for row in tenants:
        name = _entry_name(row)
        tenant_id = str(row.get("tenant_id") or "").strip() or None
        expires_raw = row.get("key_expires_at")
        expires_at = _parse_iso(expires_raw)

        status = "OK"
        message = f"{name} dashboard key valid (non-expiring)"
        days_until = None
        days_since = None

        if expires_at is not None:
            delta_days = (expires_at - now).total_seconds() / 86400.0
            if delta_days < 0:
                status = "EXPIRED"
                days_since = int(abs(delta_days))
                message = f"{name} dashboard key expired {days_since} days ago"
                worst = max(worst, 2)
            elif delta_days <= threshold_days:
                status = "WARNING"
                days_until = int(delta_days)
                message = f"{name} dashboard key expires in {days_until} days"
                worst = max(worst, 1)
            else:
                days_until = int(delta_days)
                message = f"{name} dashboard key valid (expires in {days_until} days)"

        results.append(
            {
                "tenant_id": tenant_id,
                "display_name": str(row.get("display_name") or "").strip() or None,
                "status": status,
                "message": message,
                "key_expires_at": str(expires_raw).strip() if isinstance(expires_raw, str) else None,
                "days_until_expiry": days_until,
                "days_since_expiry": days_since,
            }
        )

    return results, worst


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tenant dashboard key expiry status.")
    parser.add_argument("--config", default="tenants/dashboard_access.json", help="Path to dashboard access config")
    parser.add_argument("--threshold-days", type=int, default=7, help="Warn when key expires within this many days")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output")
    args = parser.parse_args()

    if args.threshold_days < 0:
        raise ValueError("--threshold-days must be >= 0")

    config_path = Path(args.config)
    tenants = _load_tenants(config_path)
    now = datetime.now(timezone.utc)

    results, exit_code = _evaluate(tenants, args.threshold_days, now)

    if args.json:
        out = {
            "config_path": str(config_path),
            "threshold_days": args.threshold_days,
            "generated_at": now.replace(microsecond=0).isoformat(),
            "summary": {
                "ok": sum(1 for r in results if r["status"] == "OK"),
                "warning": sum(1 for r in results if r["status"] == "WARNING"),
                "expired": sum(1 for r in results if r["status"] == "EXPIRED"),
            },
            "tenants": results,
        }
        print(json.dumps(out, indent=2))
        return exit_code

    for row in results:
        print(f"{row['status']}: {row['message']}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
