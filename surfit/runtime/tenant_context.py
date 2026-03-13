from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    policy_tenant_id: str
    artifact_root: Path


class TenantContextResolver:
    def __init__(self, *, artifacts_root: str | Path, default_tenant_id: str = "tenant_demo"):
        self.artifacts_root = Path(artifacts_root)
        self.default_tenant_id = default_tenant_id

    def resolve(self, tenant_id: str | None, wave_id: str) -> TenantContext:
        resolved = str(tenant_id or self.default_tenant_id).strip() or self.default_tenant_id
        artifact_root = self.artifacts_root / resolved / str(wave_id)
        return TenantContext(
            tenant_id=resolved,
            policy_tenant_id=resolved,
            artifact_root=artifact_root,
        )

