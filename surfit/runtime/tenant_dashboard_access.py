from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TenantDashboardIdentity:
    tenant_id: str
    display_name: str
    logo_url: str | None
    theme: dict[str, Any]
    key_created_at: str | None
    key_expires_at: str | None
    key_rotated_at: str | None


class TenantDashboardAccessService:
    """Lightweight access-key to tenant binding for the tenant dashboard."""

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)

    def _load_rows(self) -> list[dict[str, Any]]:
        if not self.config_path.exists():
            return []
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if isinstance(payload, dict):
            raw_rows = payload.get("tenants", [])
            if isinstance(raw_rows, list):
                return [row for row in raw_rows if isinstance(row, dict)]
        return []

    @staticmethod
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

    @staticmethod
    def _is_expired(expires_at: str | None) -> bool:
        expires_dt = TenantDashboardAccessService._parse_iso(expires_at)
        if expires_dt is None:
            return False
        return datetime.now(timezone.utc) >= expires_dt

    @staticmethod
    def _identity_from_row(row: dict[str, Any]) -> TenantDashboardIdentity | None:
        tenant_id = str(row.get("tenant_id") or "").strip()
        if not tenant_id:
            return None

        display_name = str(row.get("display_name") or tenant_id).strip() or tenant_id
        logo_url = str(row.get("logo_url") or "").strip() or None
        theme = row.get("theme") if isinstance(row.get("theme"), dict) else {}
        key_created_at = str(row.get("key_created_at") or "").strip() or None
        key_expires_at = str(row.get("key_expires_at") or "").strip() or None
        key_rotated_at = str(row.get("key_rotated_at") or "").strip() or None

        return TenantDashboardIdentity(
            tenant_id=tenant_id,
            display_name=display_name,
            logo_url=logo_url,
            theme=theme,
            key_created_at=key_created_at,
            key_expires_at=key_expires_at,
            key_rotated_at=key_rotated_at,
        )

    def resolve_identity(self, access_key: str) -> TenantDashboardIdentity | None:
        identity, reason = self.resolve_identity_with_reason(access_key)
        if reason is not None:
            return None
        return identity

    def resolve_identity_with_reason(self, access_key: str) -> tuple[TenantDashboardIdentity | None, str | None]:
        token = str(access_key or "").strip()
        if not token:
            return None, "MISSING"

        for row in self._load_rows():
            configured = str(row.get("dashboard_access_key") or "").strip()
            if not configured or not hmac.compare_digest(configured, token):
                continue

            if self._is_expired(str(row.get("key_expires_at") or "").strip() or None):
                return None, "EXPIRED"

            identity = self._identity_from_row(row)
            if identity is None:
                return None, "INVALID"
            return identity, None

        return None, "INVALID"

    def get_tenant_branding(self, tenant_id: str) -> dict[str, Any] | None:
        target = str(tenant_id or "").strip()
        if not target:
            return None
        for row in self._load_rows():
            row_tenant = str(row.get("tenant_id") or "").strip()
            if row_tenant != target:
                continue
            identity = self._identity_from_row(row)
            if identity is None:
                return None
            return {
                "tenant_id": identity.tenant_id,
                "display_name": identity.display_name,
                "logo_url": identity.logo_url,
                "theme": identity.theme,
                "key_created_at": identity.key_created_at,
                "key_expires_at": identity.key_expires_at,
                "key_rotated_at": identity.key_rotated_at,
            }
        return None
