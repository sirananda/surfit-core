from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_allowlists(path: Path) -> None:
    payload = {
        "policy_manifest_version": "gateway-contract-v1",
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


def _load_api_module(allowlists_path: Path, artifacts_root: Path):
    if "anthropic" not in sys.modules:
        fake = types.ModuleType("anthropic")

        class _FakeAnthropic:
            def __init__(self, *args, **kwargs):
                pass

            class messages:
                @staticmethod
                def create(*args, **kwargs):
                    raise RuntimeError("anthropic stub")

        fake.Anthropic = _FakeAnthropic
        sys.modules["anthropic"] = fake

    os.environ["SURFIT_POLICY_ALLOWLISTS_PATH"] = str(allowlists_path)
    os.environ["SURFIT_RUNTIME_ARTIFACTS_ROOT"] = str(artifacts_root)
    os.environ["SURFIT_DEFAULT_TENANT_ID"] = "tenant_contract"

    if "api" in sys.modules:
        del sys.modules["api"]
    import api  # type: ignore

    importlib.reload(api)
    return api


class ExecutionGatewayContractTests(unittest.TestCase):
    def test_allow_deny_pending_contracts(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            _write_allowlists(allowlists)
            api = _load_api_module(allowlists, artifacts_root)
            client = TestClient(api.app)

            allow_payload = {
                "tenant_id": "tenant_a",
                "wave_id": "wave-allow-contract",
                "wave_type": "connector_execution",
                "system": "github",
                "action": "open_pull_request",
                "risk_level": "medium",
                "approval_required": False,
                "required_execution_sequence": [],
                "trigger_type": "api",
                "context": {"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                "agent_id": "gateway_agent",
                "token_scope": ["open_pull_request"],
                "pinned_policy_manifest": ["open_pull_request"],
                "runtime_rules": ["open_pull_request"],
            }
            allow_resp = client.post("/api/runtime/execution-gateway/evaluate", json=allow_payload)
            self.assertEqual(allow_resp.status_code, 200)
            allow_body = allow_resp.json()
            self.assertEqual(allow_body["decision"], "ALLOW")

            deny_payload = {
                **allow_payload,
                "wave_id": "wave-deny-contract",
                "action": "merge_pull_request",
                "token_scope": ["merge_pull_request"],
                "pinned_policy_manifest": ["open_pull_request"],
                "runtime_rules": ["open_pull_request"],
            }
            deny_resp = client.post("/api/runtime/execution-gateway/evaluate", json=deny_payload)
            self.assertEqual(deny_resp.status_code, 200)
            deny_body = deny_resp.json()
            self.assertEqual(deny_body["decision"], "DENY")
            self.assertEqual(deny_body["reason_code"], "TOKEN_SCOPE_INTERSECTION_EMPTY")

            pending_payload = {
                **allow_payload,
                "wave_id": "wave-pending-contract",
                "action": "merge_pull_request",
                "approval_required": True,
                "token_scope": ["merge_pull_request"],
                "pinned_policy_manifest": ["merge_pull_request"],
                "runtime_rules": ["merge_pull_request"],
                "approval_linkage": {},
            }
            pending_resp = client.post("/api/runtime/execution-gateway/evaluate", json=pending_payload)
            self.assertEqual(pending_resp.status_code, 200)
            pending_body = pending_resp.json()
            self.assertEqual(pending_body["decision"], "PENDING_APPROVAL")
            artifact_path = Path(pending_body["artifact"]["artifact_path"])
            self.assertTrue(artifact_path.exists(), f"Expected artifact to be created at {artifact_path}")


if __name__ == "__main__":
    unittest.main()

