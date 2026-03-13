from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class GatewayDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    PENDING_APPROVAL = "PENDING_APPROVAL"


@dataclass(frozen=True)
class WaveModel:
    wave_id: str
    wave_type: str
    system: str
    action: str
    risk_level: str
    approval_required: bool = False
    required_execution_sequence: list[str] = field(default_factory=list)
    approval_rules: dict[str, Any] = field(default_factory=dict)
    execution_timeout: int | None = None
    trigger_type: str = "manual"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernedActionRequest:
    wave: WaveModel
    agent_id: str
    tenant_id: str = "tenant_demo"
    orchestrator_id: str | None = None
    token_scope: set[str] = field(default_factory=set)
    pinned_policy_manifest: set[str] = field(default_factory=set)
    runtime_rules: set[str] = field(default_factory=set)
    policy_manifest_hash: str | None = None
    policy_reference: str | None = None
    approval_linkage: dict[str, Any] | None = None
    execution_path_evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class TokenValidationResult:
    is_valid: bool
    reason_code: str
    effective_scope: set[str] = field(default_factory=set)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    decision: GatewayDecision
    reason_code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceArtifact:
    artifact_id: str
    schema_version: str
    tenant_id: str
    wave_id: str
    system: str
    action: str
    agent_id: str
    orchestrator_id: str | None
    policy_reference: str | None
    policy_manifest_hash: str | None
    decision: str
    reason_code: str
    timestamp: str
    timestamps: dict[str, str] = field(default_factory=dict)
    approval_linkage: dict[str, Any] | None = None
    execution_path_evidence: dict[str, Any] | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def build_id() -> str:
        return f"gart_{uuid.uuid4().hex[:20]}"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class GatewayResult:
    decision: GatewayDecision
    reason_code: str
    message: str
    artifact: GovernanceArtifact
    details: dict[str, Any] = field(default_factory=dict)
