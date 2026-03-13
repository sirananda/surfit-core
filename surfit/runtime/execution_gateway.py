from __future__ import annotations

from .artifact_service import ArtifactService
from .models import GatewayDecision, GatewayResult, GovernedActionRequest
from .policy_engine import PolicyEngine
from .token_validation import TokenValidationLayer


class ExecutionGateway:
    """Connector-agnostic decision gateway for governed runtime actions."""

    def __init__(
        self,
        *,
        policy_engine: PolicyEngine,
        token_validation: TokenValidationLayer,
        artifact_service: ArtifactService,
    ):
        self.policy_engine = policy_engine
        self.token_validation = token_validation
        self.artifact_service = artifact_service

    def evaluate(self, request: GovernedActionRequest) -> GatewayResult:
        token_result = self.token_validation.validate_scope_intersection(
            token_scope=request.token_scope,
            pinned_policy_manifest=request.pinned_policy_manifest,
            runtime_rules=request.runtime_rules,
        )
        if not token_result.is_valid:
            artifact = self.artifact_service.build(
                request=request,
                decision=GatewayDecision.DENY,
                reason_code=token_result.reason_code,
                details=token_result.details,
            )
            self.artifact_service.persist(artifact)
            return GatewayResult(
                decision=GatewayDecision.DENY,
                reason_code=token_result.reason_code,
                message="Token scope validation failed.",
                artifact=artifact,
                details=token_result.details,
            )

        policy_decision = self.policy_engine.evaluate(request)
        artifact = self.artifact_service.build(
            request=request,
            decision=policy_decision.decision,
            reason_code=policy_decision.reason_code,
            details={
                "policy": policy_decision.details,
                "token_scope_effective": sorted(token_result.effective_scope),
            },
        )
        self.artifact_service.persist(artifact)
        return GatewayResult(
            decision=policy_decision.decision,
            reason_code=policy_decision.reason_code,
            message=policy_decision.message,
            artifact=artifact,
            details={
                "policy": policy_decision.details,
                "token_scope_effective": sorted(token_result.effective_scope),
            },
        )

