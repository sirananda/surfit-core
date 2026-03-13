from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class PolicyManifest:
    tenant_id: str
    source_path: str
    version: str
    manifest_hash: str
    payload: dict[str, Any]


class PolicyManifestLoader:
    """Tenant-aware JSON policy manifest loader with validation and cache."""

    REQUIRED_ROOT_FIELDS = {
        "agent_wave_allowlist",
        "template_policy_allowlist",
        "template_runtime_scopes",
        "http_proxy_allowlist",
    }

    def __init__(self, *, base_dir: str | Path, default_manifest_name: str = "allowlists.json"):
        self.base_dir = Path(base_dir)
        self.default_manifest_name = default_manifest_name
        self._cache: dict[tuple[str, str], tuple[float, PolicyManifest]] = {}
        self._lock = Lock()

    def load_manifest(self, tenant_id: str = "tenant_demo") -> PolicyManifest:
        source = self._resolve_manifest_path(tenant_id)
        key = (tenant_id, str(source))
        mtime = source.stat().st_mtime
        with self._lock:
            cached = self._cache.get(key)
            if cached and cached[0] == mtime:
                return cached[1]
            payload = self._normalize(self._read_json(source))
            self._validate(payload, source)
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            manifest_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            version_raw = payload.get("policy_manifest_version")
            version = (
                str(version_raw).strip()
                if version_raw is not None and str(version_raw).strip()
                else f"{source.name}@sha256:{manifest_hash}"
            )
            manifest = PolicyManifest(
                tenant_id=tenant_id,
                source_path=str(source),
                version=version,
                manifest_hash=manifest_hash,
                payload=payload,
            )
            self._cache[key] = (mtime, manifest)
            return manifest

    def get_template_scope(self, *, tenant_id: str, wave_template_id: str) -> dict[str, Any]:
        manifest = self.load_manifest(tenant_id)
        scopes = manifest.payload.get("template_runtime_scopes")
        if not isinstance(scopes, dict):
            return {}
        scope = scopes.get(str(wave_template_id))
        return dict(scope) if isinstance(scope, dict) else {}

    def _resolve_manifest_path(self, tenant_id: str) -> Path:
        tenant_specific = self.base_dir / tenant_id / self.default_manifest_name
        if tenant_specific.exists():
            return tenant_specific
        root_manifest = self.base_dir / self.default_manifest_name
        if root_manifest.exists():
            return root_manifest
        raise FileNotFoundError(f"Policy manifest not found at {tenant_specific} or {root_manifest}")

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Policy manifest must be a JSON object: {path}")
        return payload

    @classmethod
    def _validate(cls, payload: dict[str, Any], source: Path) -> None:
        missing = [field for field in cls.REQUIRED_ROOT_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"Policy manifest missing required fields {missing}: {source}")

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        out = dict(payload)
        for key in ("agent_wave_allowlist", "template_policy_allowlist"):
            raw = out.get(key)
            if not isinstance(raw, dict):
                out[key] = {}
                continue
            normalized: dict[str, list[str]] = {}
            for k, v in raw.items():
                if isinstance(v, list):
                    normalized[str(k)] = [str(x) for x in v]
            out[key] = normalized

        scopes = out.get("template_runtime_scopes")
        if not isinstance(scopes, dict):
            out["template_runtime_scopes"] = {}

        http_allow = out.get("http_proxy_allowlist")
        if not isinstance(http_allow, dict):
            out["http_proxy_allowlist"] = {"allowed_domains": [], "allowed_methods": [], "allowed_url_prefixes": []}
        return out

