from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from surfit.demos.handlers._common import DemoHandlerRequest
from surfit.demos.handlers.context_router import ContextPrepError, PreparedWaveContext

from .artifact_service import ArtifactService
from .execution_gateway import ExecutionGateway
from .models import GovernedActionRequest
from .tenant_context import TenantContextResolver
from .wave_service import WaveService


@dataclass(frozen=True)
class RuntimeGatewayOrchestratorRequest:
    wave_id: str
    wave_type: str
    system: str
    action: str
    risk_level: str
    approval_required: bool
    required_execution_sequence: list[str]
    approval_rules: dict[str, Any]
    execution_timeout: int | None
    trigger_type: str
    context: dict[str, Any]
    agent_id: str
    tenant_id: str | None
    orchestrator_id: str | None
    token_scope: list[str]
    pinned_policy_manifest: list[str]
    runtime_rules: list[str]
    policy_manifest_hash: str | None
    policy_reference: str | None
    approval_linkage: dict[str, Any] | None
    execution_path_evidence: dict[str, Any] | None


@dataclass(frozen=True)
class RuntimeGatewayOrchestratorResult:
    tenant_id: str
    artifact_path: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class WaveRunPrepDeny:
    code: str
    message: str
    node: str
    http_status: int
    rule: str


@dataclass(frozen=True)
class WaveRunPreparationResult:
    policy_snapshot: dict[str, Any]
    policy_manifest_hash: str
    policy_manifest_version: str
    policy_manifest_json: str
    connector_type: str | None
    prepared_context: PreparedWaveContext
    wave_token: str
    wave_token_hash: str
    wave_token_expires_at: str
    wave_mutation_token: str
    wave_mutation_token_hash: str
    wave_mutation_token_expires_at: str
    wave_mutation_token_payload_json: str
    handler_request: DemoHandlerRequest


@dataclass(frozen=True)
class WaveRunPreparationRequest:
    req: Any
    tenant_id: str
    wave_id: str
    workspace_dir: str
    market_intel_templates: set[str]
    prod_config_target: str


@dataclass(frozen=True)
class WaveRunPreparationDeps:
    load_policy_snapshot: Callable[[], dict[str, Any]]
    log_decision: Callable[[str, str, str, str, str, str | None], None]
    resolve_connector_type: Callable[[str], str | None]
    prepare_wave_context: Callable[..., tuple[PreparedWaveContext | None, ContextPrepError | None]]
    normalize_repo_relative: Callable[[str], str]
    is_under: Callable[[str, str], bool]
    prepare_connector_context: Callable[[str, dict[str, Any]], dict[str, Any]]
    issue_wave_token: Callable[[str, str], tuple[str, str, str]]
    build_mutation_scope: Callable[[str, dict[str, Any], dict[str, Any]], dict[str, Any]]
    mint_wave_mutation_token: Callable[..., tuple[str, str, str, str]]
    insert_wave_row: Callable[..., None]
    mkdir: Callable[[str], None]
    commit: Callable[[], None]


class WaveOrchestrator:
    def __init__(self, tenant_context_resolver: TenantContextResolver):
        self.tenant_context_resolver = tenant_context_resolver

    def orchestrate_runtime_gateway(
        self,
        req: RuntimeGatewayOrchestratorRequest,
        *,
        wave_service: WaveService,
        artifact_service_factory: Callable[[Path], ArtifactService],
        gateway_factory: Callable[[ArtifactService], ExecutionGateway],
    ) -> RuntimeGatewayOrchestratorResult:
        tenant_ctx = self.tenant_context_resolver.resolve(req.tenant_id, req.wave_id)
        wave = wave_service.from_payload(
            {
                "wave_id": req.wave_id,
                "wave_type": req.wave_type,
                "system": req.system,
                "action": req.action,
                "risk_level": req.risk_level,
                "approval_required": req.approval_required,
                "required_execution_sequence": req.required_execution_sequence,
                "approval_rules": req.approval_rules,
                "execution_timeout": req.execution_timeout,
                "trigger_type": req.trigger_type,
                "context": req.context,
            }
        )
        artifact_service = artifact_service_factory(tenant_ctx.artifact_root)
        gateway = gateway_factory(artifact_service)
        action_req = GovernedActionRequest(
            wave=wave,
            agent_id=req.agent_id,
            tenant_id=tenant_ctx.tenant_id,
            orchestrator_id=req.orchestrator_id,
            token_scope={str(x) for x in req.token_scope},
            pinned_policy_manifest={str(x) for x in req.pinned_policy_manifest},
            runtime_rules={str(x) for x in req.runtime_rules},
            policy_manifest_hash=req.policy_manifest_hash,
            policy_reference=req.policy_reference,
            approval_linkage=req.approval_linkage,
            execution_path_evidence=req.execution_path_evidence,
        )
        result = gateway.evaluate(action_req)
        artifact_path = str(tenant_ctx.artifact_root / f"{result.artifact.artifact_id}.json")
        payload = {
            "tenant_id": tenant_ctx.tenant_id,
            "decision": result.decision.value,
            "reason_code": result.reason_code,
            "message": result.message,
            "artifact": {
                "artifact_id": result.artifact.artifact_id,
                "schema_version": result.artifact.schema_version,
                "tenant_id": result.artifact.tenant_id,
                "wave_id": result.artifact.wave_id,
                "system": result.artifact.system,
                "action": result.artifact.action,
                "decision": result.artifact.decision,
                "reason_code": result.artifact.reason_code,
                "timestamp": result.artifact.timestamp,
                "timestamps": result.artifact.timestamps,
                "artifact_path": artifact_path,
            },
            "details": result.details,
        }
        return RuntimeGatewayOrchestratorResult(
            tenant_id=tenant_ctx.tenant_id,
            artifact_path=artifact_path,
            payload=payload,
        )

    def prepare_wave_run(
        self,
        request: WaveRunPreparationRequest,
        deps: WaveRunPreparationDeps,
    ) -> tuple[WaveRunPreparationResult | None, WaveRunPrepDeny | None]:
        req = request.req
        policy_snapshot = deps.load_policy_snapshot()
        pinned_policy_manifest_hash = policy_snapshot["manifest_hash"]
        pinned_policy_manifest_version = policy_snapshot["manifest_version"]
        pinned_policy_manifest_json = policy_snapshot["manifest_json"]
        runtime_agent_allowlist = policy_snapshot["agent_allowlist"]
        runtime_template_allowlist = policy_snapshot["template_policy_allowlist"]

        if not req.agent_id:
            return None, WaveRunPrepDeny("AGENT_ID_REQUIRED", "agent_id is required", "run_wave", 403, "agent_id_present")

        allowed_templates = runtime_agent_allowlist.get(req.agent_id, set())
        if req.wave_template_id not in allowed_templates:
            return None, WaveRunPrepDeny(
                "AGENT_NOT_AUTHORIZED",
                f"agent_id '{req.agent_id}' is not authorized for wave_template_id '{req.wave_template_id}'",
                "run_wave",
                403,
                "agent_wave_allowlist",
            )
        deps.log_decision(request.wave_id, "ALLOW", "agent-wave allowlist satisfied", "agent_wave_allowlist", "run_wave", request.tenant_id)

        allowed_policies = runtime_template_allowlist.get(req.wave_template_id, set())
        if req.policy_version not in allowed_policies:
            return None, WaveRunPrepDeny(
                "POLICY_VERSION_INVALID",
                f"policy_version '{req.policy_version}' is invalid for wave_template_id '{req.wave_template_id}'",
                "run_wave",
                422,
                "template_policy_allowlist",
            )
        deps.log_decision(request.wave_id, "ALLOW", "policy version valid for template", "template_policy_allowlist", "run_wave", request.tenant_id)

        connector_type = deps.resolve_connector_type(req.wave_template_id)
        prepared_ctx, prep_err = deps.prepare_wave_context(
            wave_template_id=req.wave_template_id,
            context_refs=req.context_refs,
            intent=req.intent,
            connector_type=connector_type,
            market_intel_templates=request.market_intel_templates,
            prod_config_target=request.prod_config_target,
            normalize_repo_relative=deps.normalize_repo_relative,
            is_under=deps.is_under,
            prepare_connector_context=deps.prepare_connector_context,
        )
        if prep_err:
            return None, WaveRunPrepDeny(prep_err.code, prep_err.message, prep_err.node, prep_err.http_status, prep_err.rule)
        assert prepared_ctx is not None
        if prepared_ctx.context_updates:
            req.context_refs.update(prepared_ctx.context_updates)
        for event in prepared_ctx.decisions:
            deps.log_decision(request.wave_id, event.decision, event.reason, event.rule, event.node, request.tenant_id)

        token, token_hash, token_expires_at = deps.issue_wave_token(request.wave_id, req.agent_id)
        mutation_scope = deps.build_mutation_scope(req.wave_template_id, req.context_refs, policy_snapshot["manifest_payload"])
        wave_mutation_token, wave_mutation_token_hash, wave_mutation_token_expires_at, wave_mutation_token_payload_json = deps.mint_wave_mutation_token(
            wave_id=request.wave_id,
            agent_id=req.agent_id,
            policy_manifest_hash=pinned_policy_manifest_hash,
            policy_version=req.policy_version,
            wave_template_id=req.wave_template_id,
            scope=mutation_scope,
        )

        deps.mkdir(request.workspace_dir)
        deps.insert_wave_row(
            wave_id=request.wave_id,
            req=req,
            tenant_id=request.tenant_id,
            status="running",
            workspace_dir=request.workspace_dir,
            wave_token_hash=token_hash,
            wave_token_expires_at=token_expires_at,
            policy_manifest_hash=pinned_policy_manifest_hash,
            policy_manifest_version=pinned_policy_manifest_version,
            policy_manifest_json=pinned_policy_manifest_json,
            wave_mutation_token=wave_mutation_token,
            wave_mutation_token_hash=wave_mutation_token_hash,
            wave_mutation_token_expires_at=wave_mutation_token_expires_at,
            wave_mutation_token_payload_json=wave_mutation_token_payload_json,
        )
        deps.log_decision(request.wave_id, "ALLOW", "wave token issued", "wave_token_issue", "run_wave", request.tenant_id)
        deps.commit()

        handler_request = DemoHandlerRequest(
            wave_id=request.wave_id,
            wave_template_id=req.wave_template_id,
            wave_token=token,
            wave_mutation_token=wave_mutation_token,
            workspace_dir=request.workspace_dir,
            output_path=prepared_ctx.output_path,
            approved_by=req.agent_id,
            context_refs=req.context_refs,
            connector_type=connector_type,
            connector_context=dict(prepared_ctx.connector_context),
            policy_manifest_hash=pinned_policy_manifest_hash,
            policy_version=req.policy_version,
            input_csv_path=prepared_ctx.input_path,
            target_path=prepared_ctx.target_path,
            sources=list(prepared_ctx.sources),
            snapshot_dir=str(prepared_ctx.snapshot_dir or ""),
            run_id=request.wave_id,
            brief_goal=prepared_ctx.brief_goal,
            references=list(prepared_ctx.reference_paths),
            attempted_action=prepared_ctx.attempted_action,
            repo_base_url=prepared_ctx.repo_base_url,
            integration_case=prepared_ctx.integration_case,
            integration_base_url=prepared_ctx.integration_base_url,
        )
        return WaveRunPreparationResult(
            policy_snapshot=policy_snapshot,
            policy_manifest_hash=pinned_policy_manifest_hash,
            policy_manifest_version=pinned_policy_manifest_version,
            policy_manifest_json=pinned_policy_manifest_json,
            connector_type=connector_type,
            prepared_context=prepared_ctx,
            wave_token=token,
            wave_token_hash=token_hash,
            wave_token_expires_at=token_expires_at,
            wave_mutation_token=wave_mutation_token,
            wave_mutation_token_hash=wave_mutation_token_hash,
            wave_mutation_token_expires_at=wave_mutation_token_expires_at,
            wave_mutation_token_payload_json=wave_mutation_token_payload_json,
            handler_request=handler_request,
        ), None

