from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import GatewayDecision, GovernedActionRequest, PolicyDecision
from .policy_manifest_loader import PolicyManifestLoader

_RISK_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


class PolicyEngine(ABC):
    @abstractmethod
    def evaluate(self, request: GovernedActionRequest) -> PolicyDecision:
        raise NotImplementedError


class DefaultPolicyEngine(PolicyEngine):
    """Initial reusable policy engine abstraction for Surfit v1."""

    def __init__(self, policy_loader: PolicyManifestLoader):
        self.policy_loader = policy_loader

    def evaluate(self, request: GovernedActionRequest) -> PolicyDecision:
        wave = request.wave
        runtime_ctx = wave.context.get("runtime_rules") if isinstance(wave.context, dict) else None
        runtime_ctx = runtime_ctx if isinstance(runtime_ctx, dict) else {}
        wave_template_id = str(wave.context.get("wave_template_id", "")).strip() if isinstance(wave.context, dict) else ""
        manifest_scope: dict[str, Any] = {}
        if wave_template_id:
            manifest_scope = self.policy_loader.get_template_scope(
                tenant_id=request.tenant_id,
                wave_template_id=wave_template_id,
            )

        allowed_actions = runtime_ctx.get("allowlisted_actions")
        if not isinstance(allowed_actions, list):
            if isinstance(manifest_scope.get("allowlisted_actions"), list):
                allowed_actions = manifest_scope.get("allowlisted_actions")
            else:
                github_policy = manifest_scope.get("github_policy")
                if isinstance(github_policy, dict) and isinstance(github_policy.get("allowed_actions"), list):
                    allowed_actions = github_policy.get("allowed_actions")
        if isinstance(allowed_actions, list):
            normalized = {str(x) for x in allowed_actions if str(x).strip()}
            if wave.action not in normalized:
                return PolicyDecision(
                    decision=GatewayDecision.DENY,
                    reason_code="ACTION_NOT_ALLOWED",
                    message=f"Action '{wave.action}' is not allowlisted.",
                    details={"allowlisted_actions": sorted(normalized)},
                )

        max_risk = str(runtime_ctx.get("max_risk_level", "critical")).lower()
        if _RISK_RANK.get(str(wave.risk_level).lower(), 99) > _RISK_RANK.get(max_risk, 4):
            return PolicyDecision(
                decision=GatewayDecision.DENY,
                reason_code="RISK_THRESHOLD_EXCEEDED",
                message="Wave risk level exceeds runtime threshold.",
                details={"risk_level": wave.risk_level, "max_risk_level": max_risk},
            )

        required = [str(x) for x in (wave.required_execution_sequence or [])]
        if required:
            evidence = request.execution_path_evidence or {}
            observed = evidence.get("actions", [])
            observed_set = {str(x) for x in observed} if isinstance(observed, list) else set()
            missing = [step for step in required if step not in observed_set]
            if missing:
                return PolicyDecision(
                    decision=GatewayDecision.DENY,
                    reason_code="REQUIRED_EXECUTION_PATH_NOT_SATISFIED",
                    message="Required execution path steps are missing.",
                    details={"missing_steps": missing, "required_sequence": required},
                )

        approval_rules: dict[str, Any] = wave.approval_rules if isinstance(wave.approval_rules, dict) else {}
        if wave.approval_required and "required_for_actions" not in approval_rules:
            approval_rules = {**approval_rules, "required_for_actions": [wave.action]}
        if "required_for_actions" not in approval_rules:
            github_policy = manifest_scope.get("github_policy")
            if isinstance(github_policy, dict):
                required_for = github_policy.get("require_approval_for_actions")
                if isinstance(required_for, list):
                    approval_rules = {**approval_rules, "required_for_actions": [str(x) for x in required_for]}
        required_for = approval_rules.get("required_for_actions")
        if isinstance(required_for, list) and wave.action in {str(x) for x in required_for}:
            approval = request.approval_linkage or {}
            approval_id = str(approval.get("approval_id", "")).strip() if isinstance(approval, dict) else ""
            if not approval_id:
                return PolicyDecision(
                    decision=GatewayDecision.PENDING_APPROVAL,
                    reason_code="APPROVAL_REQUIRED",
                    message="Action requires approval before execution.",
                    details={"required_for_actions": required_for},
                )

        return PolicyDecision(
            decision=GatewayDecision.ALLOW,
            reason_code="POLICY_ALLOW",
            message="Policy checks passed.",
            details={},
        )
