from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_allowlists(path: Path) -> None:
    payload = {
        "policy_manifest_version": "wave-decisions-contract-v1",
        "agent_wave_allowlist": {"gateway_agent": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"]},
        "template_policy_allowlist": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": ["enterprise_multistage_execution_governance_policy_v1"]
        },
        "http_proxy_allowlist": {"allowed_domains": [], "allowed_methods": ["GET", "POST"], "allowed_url_prefixes": []},
        "template_runtime_scopes": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {
                "allowlisted_actions": ["read", "open_pull_request", "merge_pull_request"],
                "github_policy": {"require_approval_for_actions": ["merge_pull_request"]},
            }
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_api_module(allowlists_path: Path, artifacts_root: Path, db_path: Path):
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

    os.environ["SURFIT_ENV"] = "dev"
    os.environ["SURFIT_REQUIRE_EXPLICIT_PROD_CONFIG"] = "0"
    os.environ["SURFIT_POLICY_ALLOWLISTS_PATH"] = str(allowlists_path)
    os.environ["SURFIT_RUNTIME_ARTIFACTS_ROOT"] = str(artifacts_root)
    os.environ["SURFIT_DB_PATH"] = str(db_path)
    os.environ["SURFIT_DEFAULT_TENANT_ID"] = "tenant_default"

    if "api" in sys.modules:
        del sys.modules["api"]
    import api  # type: ignore

    importlib.reload(api)
    return api


def _write_artifact(
    *,
    artifacts_root: Path,
    tenant_id: str,
    wave_id: str,
    artifact_id: str,
    timestamp: str,
    approval_linkage: dict | None = None,
) -> None:
    target_dir = artifacts_root / tenant_id / wave_id
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_id": artifact_id,
        "schema_version": "surfit.governance_artifact.v1",
        "tenant_id": tenant_id,
        "wave_id": wave_id,
        "system": "github",
        "action": "merge_pull_request",
        "decision": "ALLOW",
        "reason_code": "POLICY_ALLOW",
        "timestamp": timestamp,
        "timestamps": {"created_at": timestamp, "recorded_at": timestamp},
        "approval_linkage": approval_linkage,
    }
    (target_dir / f"{artifact_id}.json").write_text(json.dumps(payload), encoding="utf-8")


class WaveDecisionsEndpointTests(unittest.TestCase):
    def test_wave_decision_timeline_oldest_first_with_linkage(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)

            api = _load_api_module(allowlists, artifacts_root, db_path)
            client = TestClient(api.app)

            conn = sqlite3.connect(api.DB_PATH)
            api.ensure_wave_tables(conn)
            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, policy_manifest_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-42",
                    "tenant_a",
                    "agent-a",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{"system":"github","action":"merge_pull_request"}',
                    "complete",
                    "pmh-abc123",
                    "2026-03-14T01:00:00+00:00",
                    "2026-03-14T01:00:05+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-42", "tenant_a", "ALLOW", "allow one", "RULE_ALLOW", "gateway", "2026-03-14T01:00:06+00:00", None, "h1"),
            )
            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-42", "tenant_a", "DENY", "deny two", "RULE_DENY", "gateway", "2026-03-14T01:00:07+00:00", "h1", "h2"),
            )
            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-42",
                    "wave-42",
                    "./outputs/report.md",
                    "hash",
                    "ops",
                    "2026-03-14T01:00:08+00:00",
                    "approved",
                    "approved",
                    "2026-03-14T01:00:08+00:00",
                    "2026-03-14T01:00:08+00:00",
                ),
            )
            conn.commit()
            conn.close()

            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_a",
                wave_id="wave-42",
                artifact_id="gart-42",
                timestamp="2026-03-14T01:00:09+00:00",
                approval_linkage={"linked_wave_id": "wave-42", "approval_request_id": "apr-42"},
            )

            resp = client.get("/api/runtime/waves/wave-42/decisions")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["wave_id"], "wave-42")
            self.assertEqual(body["tenant_id"], "tenant_a")
            self.assertEqual(body["artifact_id"], "gart-42")
            self.assertEqual(body["approval_request_id"], "apr-42")
            self.assertEqual(body["policy_manifest_hash"], "pmh-abc123")
            self.assertEqual(body["count"], 2)
            self.assertEqual([d["decision_id"] for d in body["decisions"]], [1, 2])
            self.assertEqual([d["reason_code"] for d in body["decisions"]], ["RULE_ALLOW", "RULE_DENY"])
            self.assertEqual(body["decisions"][0]["artifact_id"], "gart-42")
            self.assertEqual(body["decisions"][0]["approval_request_id"], "apr-42")

    def test_not_found_and_null_safe_shape(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)

            api = _load_api_module(allowlists, artifacts_root, db_path)
            client = TestClient(api.app)

            missing = client.get("/api/runtime/waves/wave-missing/decisions")
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.json()["error"]["code"], "WAVE_NOT_FOUND")

            conn = sqlite3.connect(api.DB_PATH)
            api.ensure_wave_tables(conn)
            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-empty",
                    "tenant_z",
                    "agent-z",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{}',
                    "running",
                    "2026-03-14T02:00:00+00:00",
                    "2026-03-14T02:00:01+00:00",
                ),
            )
            conn.commit()
            conn.close()

            empty = client.get("/api/runtime/waves/wave-empty/decisions")
            self.assertEqual(empty.status_code, 200)
            body = empty.json()
            self.assertEqual(body["count"], 0)
            self.assertEqual(body["decisions"], [])
            self.assertIsNone(body["artifact_id"])
            self.assertIsNone(body["approval_request_id"])
            self.assertIsNone(body["policy_manifest_hash"])


if __name__ == "__main__":
    unittest.main()
