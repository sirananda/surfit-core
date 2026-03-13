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
        "policy_manifest_version": "artifact-contract-v1",
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


class ArtifactContractTests(unittest.TestCase):
    def test_artifact_schema_and_retrieval_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            _write_allowlists(allowlists)
            api = _load_api_module(allowlists, artifacts_root)
            client = TestClient(api.app)

            payload = {
                "tenant_id": "tenant_a",
                "wave_id": "wave-artifact-contract",
                "wave_type": "connector_execution",
                "system": "github",
                "action": "merge_pull_request",
                "risk_level": "medium",
                "approval_required": True,
                "required_execution_sequence": [],
                "trigger_type": "api",
                "context": {"wave_template_id": "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
                "agent_id": "gateway_agent",
                "token_scope": ["merge_pull_request"],
                "pinned_policy_manifest": ["merge_pull_request"],
                "runtime_rules": ["merge_pull_request"],
                "approval_linkage": {},
            }
            eval_resp = client.post("/api/runtime/execution-gateway/evaluate", json=payload)
            self.assertEqual(eval_resp.status_code, 200)
            body = eval_resp.json()
            artifact = body["artifact"]
            self.assertEqual(artifact["schema_version"], "surfit.governance_artifact.v1")
            self.assertEqual(artifact["tenant_id"], "tenant_a")
            self.assertEqual(body["decision"], "PENDING_APPROVAL")
            self.assertIn("created_at", artifact["timestamps"])
            artifact_id = artifact["artifact_id"]

            get_resp = client.get(f"/api/runtime/artifacts/{artifact_id}")
            self.assertEqual(get_resp.status_code, 200)
            retrieved = get_resp.json()
            self.assertEqual(retrieved["artifact_id"], artifact_id)
            self.assertEqual(retrieved["tenant_id"], "tenant_a")
            self.assertEqual(retrieved["decision"], "PENDING_APPROVAL")
            self.assertEqual(retrieved["reason_code"], "APPROVAL_REQUIRED")
            self.assertTrue(Path(retrieved["artifact_path"]).exists())

            list_resp = client.get("/api/runtime/artifacts", params={"tenant_id": "tenant_a", "limit": 10})
            self.assertEqual(list_resp.status_code, 200)
            listing = list_resp.json()
            self.assertGreaterEqual(len(listing["artifacts"]), 1)
            self.assertEqual(listing["artifacts"][0]["tenant_id"], "tenant_a")


if __name__ == "__main__":
    unittest.main()
