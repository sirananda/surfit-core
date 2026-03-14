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
        "policy_manifest_version": "recent-waves-contract-v1",
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
    decision: str,
    reason_code: str,
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
        "action": "read",
        "decision": decision,
        "reason_code": reason_code,
        "timestamp": timestamp,
        "timestamps": {"created_at": timestamp, "recorded_at": timestamp},
        "approval_linkage": approval_linkage,
    }
    (target_dir / f"{artifact_id}.json").write_text(json.dumps(payload), encoding="utf-8")


class RecentWavesEndpointTests(unittest.TestCase):
    def test_recent_waves_tenant_scope_limit_and_shape(self):
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

            rows = [
                ("wave-1", "tenant_a", "agent-a", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"read","wave_type":"runtime_check"}', "complete", "2026-03-14T01:00:00+00:00", "2026-03-14T01:00:10+00:00"),
                ("wave-2", "tenant_a", "agent-a", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"open_pull_request"}', "running", "2026-03-14T02:00:00+00:00", "2026-03-14T02:00:10+00:00"),
                ("wave-3", "tenant_a", "agent-a", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"merge_pull_request"}', "complete", "2026-03-14T03:00:00+00:00", "2026-03-14T03:00:10+00:00"),
                ("wave-x", "tenant_b", "agent-b", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"read"}', "complete", "2026-03-14T04:00:00+00:00", "2026-03-14T04:00:10+00:00"),
            ]
            conn.executemany(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-3", "tenant_a", "ALLOW", "policy checks passed", "POLICY_ALLOW", "gateway", "2026-03-14T03:00:11+00:00", None, "hash1"),
            )
            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-2", "tenant_a", "DENY", "approval required", "APPROVAL_REQUIRED", "gateway", "2026-03-14T02:00:11+00:00", None, "hash2"),
            )
            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-123",
                    "wave-3",
                    "./outputs/report.md",
                    "proposed_hash",
                    "ops-user",
                    "2026-03-14T03:00:12+00:00",
                    "approved",
                    "approved",
                    "2026-03-14T03:00:12+00:00",
                    "2026-03-14T03:00:12+00:00",
                ),
            )
            conn.commit()
            conn.close()

            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_a",
                wave_id="wave-3",
                artifact_id="gart-wave3",
                decision="ALLOW",
                reason_code="POLICY_ALLOW",
                timestamp="2026-03-14T03:00:13+00:00",
                approval_linkage={"linked_wave_id": "wave-3", "approval_request_id": "apr-123"},
            )
            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_a",
                wave_id="wave-2",
                artifact_id="gart-wave2",
                decision="DENY",
                reason_code="APPROVAL_REQUIRED",
                timestamp="2026-03-14T02:00:12+00:00",
            )

            resp = client.get("/api/runtime/waves/recent", params={"tenant_id": "tenant_a", "limit": 2})
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["tenant_id"], "tenant_a")
            self.assertEqual(body["count"], 2)
            self.assertEqual(len(body["waves"]), 2)
            self.assertEqual([row["wave_id"] for row in body["waves"]], ["wave-3", "wave-2"])

            row0 = body["waves"][0]
            self.assertEqual(row0["latest_decision"], "ALLOW")
            self.assertEqual(row0["latest_reason_code"], "POLICY_ALLOW")
            self.assertEqual(row0["artifact_id"], "gart-wave3")
            self.assertEqual(row0["approval_request_id"], "apr-123")
            self.assertEqual(row0["approval_wave_id"], "wave-3")
            self.assertEqual(row0["system"], "github")
            self.assertEqual(row0["action"], "merge_pull_request")
            self.assertIn("last_event_at", row0)

            for item in body["waves"]:
                self.assertIn("wave_id", item)
                self.assertIn("tenant_id", item)
                self.assertIn("template_id", item)
                self.assertIn("status", item)
                self.assertIn("latest_decision", item)
                self.assertIn("latest_reason_code", item)
                self.assertIn("artifact_id", item)
                self.assertIn("created_at", item)
                self.assertIn("updated_at", item)
                self.assertIn("last_event_at", item)

    def test_empty_results_and_limit_cap_and_required_tenant(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)

            api = _load_api_module(allowlists, artifacts_root, db_path)
            client = TestClient(api.app)

            empty_resp = client.get("/api/runtime/waves/recent", params={"tenant_id": "tenant_none", "limit": 500})
            self.assertEqual(empty_resp.status_code, 200)
            empty_body = empty_resp.json()
            self.assertEqual(empty_body["tenant_id"], "tenant_none")
            self.assertEqual(empty_body["limit"], 100)
            self.assertEqual(empty_body["count"], 0)
            self.assertEqual(empty_body["waves"], [])

            missing_resp = client.get("/api/runtime/waves/recent")
            self.assertEqual(missing_resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
