from __future__ import annotations

from dataclasses import asdict
from typing import Any
from pathlib import Path

from surfit.storage.artifact_store import ArtifactStore

from .models import GatewayDecision, GovernanceArtifact, GovernedActionRequest


class ArtifactService:
    def __init__(self, store: ArtifactStore):
        self.store = store

    def build(
        self,
        *,
        request: GovernedActionRequest,
        decision: GatewayDecision,
        reason_code: str,
        details: dict[str, Any] | None = None,
    ) -> GovernanceArtifact:
        wave = request.wave
        now_iso = GovernanceArtifact.now_iso()
        return GovernanceArtifact(
            artifact_id=GovernanceArtifact.build_id(),
            schema_version="surfit.governance_artifact.v1",
            tenant_id=request.tenant_id,
            wave_id=wave.wave_id,
            system=wave.system,
            action=wave.action,
            agent_id=request.agent_id,
            orchestrator_id=request.orchestrator_id,
            policy_reference=request.policy_reference,
            policy_manifest_hash=request.policy_manifest_hash,
            decision=decision.value,
            reason_code=reason_code,
            timestamp=now_iso,
            timestamps={"created_at": now_iso, "recorded_at": now_iso},
            approval_linkage=request.approval_linkage,
            execution_path_evidence=request.execution_path_evidence,
            details=details or {},
        )

    def persist(self, artifact: GovernanceArtifact) -> str:
        return self.store.save(artifact.artifact_id, asdict(artifact))


class ArtifactRetrievalService:
    """Retrieval-ready artifact boundary for runtime APIs."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        target_name = f"{artifact_id}.json"
        for path in self.root.rglob(target_name):
            try:
                payload = self._read_json(path)
            except Exception:
                continue
            if str(payload.get("artifact_id", "")).strip() == artifact_id:
                payload["_artifact_path"] = str(path)
                return payload
        return None

    def list_recent(self, *, tenant_id: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if tenant_id:
            search_root = self.root / tenant_id
            if not search_root.exists():
                return []
            candidates = search_root.rglob("*.json")
        else:
            candidates = self.root.rglob("*.json")
        for path in candidates:
            try:
                payload = self._read_json(path)
            except Exception:
                continue
            artifact_id = str(payload.get("artifact_id", "")).strip()
            if not artifact_id:
                continue
            payload["_artifact_path"] = str(path)
            records.append(payload)
        records.sort(
            key=lambda item: str((item.get("timestamps") or {}).get("created_at", item.get("timestamp", ""))),
            reverse=True,
        )
        out = []
        for row in records[: max(1, int(limit))]:
            out.append(
                {
                    "artifact_id": row.get("artifact_id"),
                    "tenant_id": row.get("tenant_id"),
                    "wave_id": row.get("wave_id"),
                    "decision": row.get("decision"),
                    "reason_code": row.get("reason_code"),
                    "timestamp": row.get("timestamp"),
                    "artifact_path": row.get("_artifact_path"),
                }
            )
        return out

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact payload must be a JSON object")
        return payload
