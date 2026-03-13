from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surfit.runtime.artifact_service import ArtifactService
from surfit.runtime.execution_gateway import ExecutionGateway
from surfit.runtime.models import GatewayDecision, GovernedActionRequest, WaveModel
from surfit.runtime.policy_manifest_loader import PolicyManifestLoader
from surfit.runtime.policy_engine import DefaultPolicyEngine
from surfit.runtime.token_validation import TokenValidationLayer
from surfit.storage.artifact_store import FileArtifactStore


class RuntimeProductSkeletonTests(unittest.TestCase):
    def _write_manifest(self, root: Path) -> None:
        payload = {
            "policy_manifest_version": "runtime-test-v1",
            "agent_wave_allowlist": {"agent-a": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"]},
            "template_policy_allowlist": {"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": ["enterprise_multistage_execution_governance_policy_v1"]},
            "http_proxy_allowlist": {"allowed_domains": [], "allowed_methods": [], "allowed_url_prefixes": []},
            "template_runtime_scopes": {
                "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {
                    "allowlisted_actions": ["create_branch", "open_pull_request", "merge_pull_request"],
                    "github_policy": {"require_approval_for_actions": ["merge_pull_request"]},
                }
            },
        }
        (root / "allowlists.json").write_text(json.dumps(payload), encoding="utf-8")

    def _gateway(self, root: Path) -> ExecutionGateway:
        self._write_manifest(root)
        return ExecutionGateway(
            policy_engine=DefaultPolicyEngine(
                PolicyManifestLoader(base_dir=root, default_manifest_name="allowlists.json")
            ),
            token_validation=TokenValidationLayer(),
            artifact_service=ArtifactService(FileArtifactStore(root)),
        )

    def test_gateway_allows_when_invariant_and_policy_pass(self):
        with tempfile.TemporaryDirectory() as td:
            gateway = self._gateway(Path(td))
            req = GovernedActionRequest(
                wave=WaveModel(
                    wave_id="wave-allow-1",
                    wave_type="connector_execution",
                    system="github",
                    action="open_pull_request",
                    risk_level="medium",
                    approval_required=False,
                    required_execution_sequence=["create_branch"],
                    approval_rules={},
                    execution_timeout=30,
                    trigger_type="api",
                    context={
                        "wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                        "runtime_rules": {"allowlisted_actions": ["open_pull_request", "create_branch"]},
                    },
                ),
                agent_id="agent-a",
                tenant_id="tenant_demo",
                orchestrator_id="orchestrator-1",
                token_scope={"open_pull_request", "create_branch"},
                pinned_policy_manifest={"open_pull_request", "create_branch"},
                runtime_rules={"open_pull_request", "create_branch"},
                execution_path_evidence={"actions": ["create_branch"]},
            )
            out = gateway.evaluate(req)
            self.assertEqual(out.decision, GatewayDecision.ALLOW)
            self.assertEqual(out.reason_code, "POLICY_ALLOW")
            self.assertTrue((Path(td) / f"{out.artifact.artifact_id}.json").exists())

    def test_gateway_returns_pending_approval(self):
        with tempfile.TemporaryDirectory() as td:
            gateway = self._gateway(Path(td))
            req = GovernedActionRequest(
                wave=WaveModel(
                    wave_id="wave-pending-1",
                    wave_type="connector_execution",
                    system="github",
                    action="merge_pull_request",
                    risk_level="medium",
                    approval_required=True,
                    required_execution_sequence=[],
                    approval_rules={"required_for_actions": ["merge_pull_request"]},
                    execution_timeout=30,
                    trigger_type="api",
                    context={"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                ),
                agent_id="agent-a",
                tenant_id="tenant_demo",
                token_scope={"merge_pull_request"},
                pinned_policy_manifest={"merge_pull_request"},
                runtime_rules={"merge_pull_request"},
                approval_linkage={},
            )
            out = gateway.evaluate(req)
            self.assertEqual(out.decision, GatewayDecision.PENDING_APPROVAL)
            self.assertEqual(out.reason_code, "APPROVAL_REQUIRED")

    def test_gateway_denies_when_scope_intersection_empty(self):
        with tempfile.TemporaryDirectory() as td:
            gateway = self._gateway(Path(td))
            req = GovernedActionRequest(
                wave=WaveModel(
                    wave_id="wave-deny-1",
                    wave_type="connector_execution",
                    system="github",
                    action="commit_file",
                    risk_level="low",
                    approval_required=False,
                    required_execution_sequence=[],
                    approval_rules={},
                    execution_timeout=30,
                    trigger_type="api",
                    context={"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                ),
                agent_id="agent-a",
                tenant_id="tenant_demo",
                token_scope={"commit_file"},
                pinned_policy_manifest={"open_pull_request"},
                runtime_rules={"merge_pull_request"},
            )
            out = gateway.evaluate(req)
            self.assertEqual(out.decision, GatewayDecision.DENY)
            self.assertEqual(out.reason_code, "TOKEN_SCOPE_INTERSECTION_EMPTY")


if __name__ == "__main__":
    unittest.main()
