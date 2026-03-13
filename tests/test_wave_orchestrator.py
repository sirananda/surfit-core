from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surfit.runtime.artifact_service import ArtifactService
from surfit.runtime.execution_gateway import ExecutionGateway
from surfit.runtime.policy_engine import DefaultPolicyEngine
from surfit.runtime.policy_manifest_loader import PolicyManifestLoader
from surfit.runtime.tenant_context import TenantContextResolver
from surfit.runtime.token_validation import TokenValidationLayer
from surfit.runtime.wave_orchestrator import (
    RuntimeGatewayOrchestratorRequest,
    WaveOrchestrator,
    WaveRunPreparationDeps,
    WaveRunPreparationRequest,
)
from surfit.runtime.wave_service import WaveService
from surfit.storage.artifact_store import FileArtifactStore


class _Req:
    def __init__(self):
        self.agent_id = "gateway_agent"
        self.wave_template_id = "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"
        self.policy_version = "enterprise_multistage_execution_governance_policy_v1"
        self.intent = "test"
        self.context_refs = {}


def _write_manifest(path: Path) -> None:
    payload = {
        "policy_manifest_version": "wave-orch-test-v1",
        "agent_wave_allowlist": {"gateway_agent": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"]},
        "template_policy_allowlist": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": ["enterprise_multistage_execution_governance_policy_v1"]
        },
        "http_proxy_allowlist": {"allowed_domains": [], "allowed_methods": ["POST"], "allowed_url_prefixes": []},
        "template_runtime_scopes": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {
                "allowlisted_actions": ["open_pull_request", "merge_pull_request"],
                "github_policy": {"require_approval_for_actions": ["merge_pull_request"]},
            }
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class WaveOrchestratorTests(unittest.TestCase):
    def test_runtime_gateway_orchestration_allow_tenant_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_manifest(tmp / "allowlists.json")
            resolver = TenantContextResolver(artifacts_root=tmp / "artifacts", default_tenant_id="tenant_default")
            orchestrator = WaveOrchestrator(resolver)
            wave_service = WaveService()
            policy_engine = DefaultPolicyEngine(PolicyManifestLoader(base_dir=tmp, default_manifest_name="allowlists.json"))
            token_validation = TokenValidationLayer()

            out = orchestrator.orchestrate_runtime_gateway(
                RuntimeGatewayOrchestratorRequest(
                    wave_id="wave-a",
                    wave_type="connector_execution",
                    system="github",
                    action="open_pull_request",
                    risk_level="medium",
                    approval_required=False,
                    required_execution_sequence=[],
                    approval_rules={},
                    execution_timeout=30,
                    trigger_type="api",
                    context={"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                    agent_id="gateway_agent",
                    tenant_id="tenant_a",
                    orchestrator_id="orch",
                    token_scope=["open_pull_request"],
                    pinned_policy_manifest=["open_pull_request"],
                    runtime_rules=["open_pull_request"],
                    policy_manifest_hash="h",
                    policy_reference="p",
                    approval_linkage=None,
                    execution_path_evidence=None,
                ),
                wave_service=wave_service,
                artifact_service_factory=lambda root: ArtifactService(FileArtifactStore(root)),
                gateway_factory=lambda artifact_service: ExecutionGateway(
                    policy_engine=policy_engine,
                    token_validation=token_validation,
                    artifact_service=artifact_service,
                ),
            )
            self.assertEqual(out.payload["decision"], "ALLOW")
            self.assertEqual(out.tenant_id, "tenant_a")
            self.assertTrue(Path(out.artifact_path).exists())
            self.assertIn("/tenant_a/wave-a/", out.artifact_path)

    def test_runtime_gateway_orchestration_pending_approval(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_manifest(tmp / "allowlists.json")
            orchestrator = WaveOrchestrator(TenantContextResolver(artifacts_root=tmp / "artifacts"))
            policy_engine = DefaultPolicyEngine(PolicyManifestLoader(base_dir=tmp, default_manifest_name="allowlists.json"))

            out = orchestrator.orchestrate_runtime_gateway(
                RuntimeGatewayOrchestratorRequest(
                    wave_id="wave-p",
                    wave_type="connector_execution",
                    system="github",
                    action="merge_pull_request",
                    risk_level="medium",
                    approval_required=True,
                    required_execution_sequence=[],
                    approval_rules={},
                    execution_timeout=30,
                    trigger_type="api",
                    context={"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                    agent_id="gateway_agent",
                    tenant_id="tenant_demo",
                    orchestrator_id=None,
                    token_scope=["merge_pull_request"],
                    pinned_policy_manifest=["merge_pull_request"],
                    runtime_rules=["merge_pull_request"],
                    policy_manifest_hash=None,
                    policy_reference=None,
                    approval_linkage={},
                    execution_path_evidence=None,
                ),
                wave_service=WaveService(),
                artifact_service_factory=lambda root: ArtifactService(FileArtifactStore(root)),
                gateway_factory=lambda artifact_service: ExecutionGateway(
                    policy_engine=policy_engine,
                    token_validation=TokenValidationLayer(),
                    artifact_service=artifact_service,
                ),
            )
            self.assertEqual(out.payload["decision"], "PENDING_APPROVAL")
            self.assertEqual(out.payload["reason_code"], "APPROVAL_REQUIRED")

    def test_prepare_wave_run_deny_path(self):
        req = _Req()
        req.agent_id = None
        orchestrator = WaveOrchestrator(TenantContextResolver(artifacts_root=ROOT / "artifacts"))
        prep, deny = orchestrator.prepare_wave_run(
            WaveRunPreparationRequest(
                req=req,
                tenant_id="tenant_demo",
                wave_id="wave-deny",
                workspace_dir=str(ROOT / "runs" / "wave-deny"),
                market_intel_templates={"marketing_digest_v1"},
                prod_config_target="demo_artifacts/prod_config.json",
            ),
            WaveRunPreparationDeps(
                load_policy_snapshot=lambda: {
                    "manifest_hash": "h",
                    "manifest_version": "v",
                    "manifest_json": "{}",
                    "agent_allowlist": {},
                    "template_policy_allowlist": {},
                    "manifest_payload": {},
                },
                log_decision=lambda *args, **kwargs: None,
                resolve_connector_type=lambda wt: None,
                prepare_wave_context=lambda **kwargs: (None, None),
                normalize_repo_relative=lambda p: p,
                is_under=lambda b, t: True,
                prepare_connector_context=lambda c, r: {},
                issue_wave_token=lambda w, a: ("t", "th", "te"),
                build_mutation_scope=lambda *args, **kwargs: {},
                mint_wave_mutation_token=lambda **kwargs: ("mt", "mth", "mte", "{}"),
                insert_wave_row=lambda **kwargs: None,
                mkdir=lambda p: None,
                commit=lambda: None,
            ),
        )
        self.assertIsNone(prep)
        self.assertIsNotNone(deny)
        self.assertEqual(deny.code, "AGENT_ID_REQUIRED")


if __name__ == "__main__":
    unittest.main()

