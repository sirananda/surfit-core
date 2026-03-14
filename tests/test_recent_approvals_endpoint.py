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
        "policy_manifest_version": "recent-approvals-contract-v1",
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


class RecentApprovalsEndpointTests(unittest.TestCase):
    def test_tenant_scope_ordering_limit_shape(self):
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

            waves = [
                ("wave-a", "tenant_a", "agent-a", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"merge_pull_request"}', "running", "2026-03-14T01:00:00+00:00", "2026-03-14T01:00:01+00:00"),
                ("wave-b", "tenant_a", "agent-a", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"open_pull_request"}', "complete", "2026-03-14T02:00:00+00:00", "2026-03-14T02:00:01+00:00"),
                ("wave-c", "tenant_b", "agent-b", "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1", "enterprise_multistage_execution_governance_policy_v1", "runtime_check", '{"system":"github","action":"read"}', "complete", "2026-03-14T03:00:00+00:00", "2026-03-14T03:00:01+00:00"),
            ]
            conn.executemany(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                waves,
            )

            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-old",
                    "wave-a",
                    "./outputs/report.md",
                    "h1",
                    None,
                    None,
                    "pending",
                    "pending",
                    "2026-03-14T01:10:00+00:00",
                    "2026-03-14T01:10:00+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-new",
                    "wave-b",
                    "./outputs/report.md",
                    "h2",
                    "ops",
                    "2026-03-14T02:10:00+00:00",
                    "approved",
                    "approved",
                    "2026-03-14T02:10:00+00:00",
                    "2026-03-14T02:10:00+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-other-tenant",
                    "wave-c",
                    "./outputs/report.md",
                    "h3",
                    "ops",
                    "2026-03-14T03:10:00+00:00",
                    "approved",
                    "approved",
                    "2026-03-14T03:10:00+00:00",
                    "2026-03-14T03:10:00+00:00",
                ),
            )

            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-b", "tenant_a", "ALLOW", "approved", "POLICY_ALLOW", "gateway", "2026-03-14T02:10:01+00:00", None, "h10"),
            )
            conn.commit()
            conn.close()

            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_a",
                wave_id="wave-b",
                artifact_id="gart-wave-b",
                timestamp="2026-03-14T02:10:02+00:00",
                approval_linkage={
                    "approval_request_id": "apr-new",
                    "approval_wave_id": "wave-b",
                    "linked_wave_id": "wave-b",
                },
            )

            resp = client.get("/api/runtime/approvals/recent", params={"tenant_id": "tenant_a", "limit": 1})
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["tenant_id"], "tenant_a")
            self.assertEqual(body["limit"], 1)
            self.assertEqual(body["count"], 1)
            self.assertEqual(len(body["approvals"]), 1)

            item = body["approvals"][0]
            self.assertEqual(item["approval_request_id"], "apr-new")
            self.assertEqual(item["wave_id"], "wave-b")
            self.assertEqual(item["approval_status"], "approved")
            self.assertEqual(item["latest_decision"], "ALLOW")
            self.assertEqual(item["artifact_id"], "gart-wave-b")
            self.assertEqual(item["approval_wave_id"], "wave-b")
            self.assertEqual(item["linked_wave_id"], "wave-b")
            self.assertEqual(item["system"], "github")
            self.assertEqual(item["action"], "open_pull_request")

            for field in [
                "approval_request_id",
                "tenant_id",
                "wave_id",
                "approval_wave_id",
                "linked_wave_id",
                "approval_status",
                "template_id",
                "system",
                "action",
                "latest_decision",
                "artifact_id",
                "created_at",
                "updated_at",
                "last_event_at",
            ]:
                self.assertIn(field, item)

    def test_empty_and_limit_cap_and_required_tenant(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)

            api = _load_api_module(allowlists, artifacts_root, db_path)
            client = TestClient(api.app)

            empty_resp = client.get("/api/runtime/approvals/recent", params={"tenant_id": "tenant_none", "limit": 999})
            self.assertEqual(empty_resp.status_code, 200)
            empty_body = empty_resp.json()
            self.assertEqual(empty_body["tenant_id"], "tenant_none")
            self.assertEqual(empty_body["limit"], 100)
            self.assertEqual(empty_body["count"], 0)
            self.assertEqual(empty_body["approvals"], [])

            missing_resp = client.get("/api/runtime/approvals/recent")
            self.assertEqual(missing_resp.status_code, 422)

    def test_null_safe_optional_fields(self):
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
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-null",
                    "tenant_n",
                    "agent-n",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{}',
                    "running",
                    "2026-03-14T04:00:00+00:00",
                    "2026-03-14T04:00:01+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO approval_requests (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "apr-null",
                    "wave-null",
                    "./outputs/report.md",
                    "h-null",
                    None,
                    None,
                    None,
                    "pending",
                    "2026-03-14T04:00:02+00:00",
                    "2026-03-14T04:00:02+00:00",
                ),
            )
            conn.commit()
            conn.close()

            resp = client.get("/api/runtime/approvals/recent", params={"tenant_id": "tenant_n", "limit": 20})
            self.assertEqual(resp.status_code, 200)
            item = resp.json()["approvals"][0]
            self.assertIsNone(item["approval_wave_id"])
            self.assertIsNone(item["linked_wave_id"])
            self.assertIsNone(item["latest_decision"])
            self.assertIsNone(item["artifact_id"])
            self.assertIsNone(item["system"])
            self.assertIsNone(item["action"])


if __name__ == "__main__":
    unittest.main()
