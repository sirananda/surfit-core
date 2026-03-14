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
        "policy_manifest_version": "tenant-dashboard-access-v2",
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


def _write_dashboard_access(path: Path) -> None:
    payload = {
        "tenants": [
            {
                "tenant_id": "tenant_a",
                "display_name": "Tenant Alpha",
                "logo_url": "https://cdn.example.com/tenant-alpha.svg",
                "theme": {"accent": "#117a5c"},
                "dashboard_access_key": "tenant-a-key",
                "key_created_at": "2026-03-10T10:00:00+00:00",
                "key_expires_at": "2099-03-10T10:00:00+00:00",
                "key_rotated_at": "2026-03-14T09:00:00+00:00",
            },
            {
                "tenant_id": "tenant_b",
                "display_name": "Tenant Beta",
                "logo_url": "",
                "theme": {"accent": "#225588"},
                "dashboard_access_key": "tenant-b-key",
                "key_created_at": "2026-03-11T10:00:00+00:00",
                "key_expires_at": None,
                "key_rotated_at": None,
            },
            {
                "tenant_id": "tenant_expired",
                "display_name": "Tenant Expired",
                "logo_url": "",
                "theme": {},
                "dashboard_access_key": "expired-key",
                "key_created_at": "2025-01-01T00:00:00+00:00",
                "key_expires_at": "2025-12-31T23:59:59+00:00",
                "key_rotated_at": "2025-06-01T00:00:00+00:00",
            },
        ]
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_api_module(allowlists_path: Path, artifacts_root: Path, db_path: Path, dashboard_access_path: Path):
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
    os.environ["SURFIT_TENANT_DASHBOARD_CONFIG_PATH"] = str(dashboard_access_path)

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
        "decision": "ALLOW",
        "reason_code": "POLICY_ALLOW",
        "timestamp": timestamp,
        "timestamps": {"created_at": timestamp, "recorded_at": timestamp},
    }
    (target_dir / f"{artifact_id}.json").write_text(json.dumps(payload), encoding="utf-8")


class TenantDashboardAccessTests(unittest.TestCase):
    def test_access_key_maps_to_tenant_branding_and_lifecycle_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            dashboard_access = tmp / "dashboard_access.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)
            _write_dashboard_access(dashboard_access)

            api = _load_api_module(allowlists, artifacts_root, db_path, dashboard_access)
            client = TestClient(api.app)

            conn = sqlite3.connect(api.DB_PATH)
            api.ensure_wave_tables(conn)
            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-tenant-a",
                    "tenant_a",
                    "agent-a",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{"system":"github","action":"read"}',
                    "complete",
                    "2026-03-14T10:00:00+00:00",
                    "2026-03-14T10:00:10+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-tenant-b",
                    "tenant_b",
                    "agent-b",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{"system":"github","action":"read"}',
                    "complete",
                    "2026-03-14T11:00:00+00:00",
                    "2026-03-14T11:00:10+00:00",
                ),
            )
            conn.commit()
            conn.close()

            resp_ctx = client.get("/api/tenant/dashboard/context", headers={"X-Surfit-Tenant-Access": "tenant-a-key"})
            self.assertEqual(resp_ctx.status_code, 200)
            ctx = resp_ctx.json()
            self.assertEqual(ctx["tenant_id"], "tenant_a")
            self.assertEqual(ctx["display_name"], "Tenant Alpha")
            self.assertEqual(ctx["logo_url"], "https://cdn.example.com/tenant-alpha.svg")
            self.assertEqual(ctx["key_created_at"], "2026-03-10T10:00:00+00:00")
            self.assertEqual(ctx["key_expires_at"], "2099-03-10T10:00:00+00:00")
            self.assertEqual(ctx["key_rotated_at"], "2026-03-14T09:00:00+00:00")

            resp_waves = client.get(
                "/api/tenant/dashboard/waves/recent",
                headers={"X-Surfit-Tenant-Access": "tenant-a-key"},
            )
            self.assertEqual(resp_waves.status_code, 200)
            body = resp_waves.json()
            self.assertEqual(body["tenant_id"], "tenant_a")
            self.assertEqual(body["count"], 1)
            self.assertEqual(body["waves"][0]["wave_id"], "wave-tenant-a")

    def test_invalid_missing_and_expired_key_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            dashboard_access = tmp / "dashboard_access.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)
            _write_dashboard_access(dashboard_access)

            api = _load_api_module(allowlists, artifacts_root, db_path, dashboard_access)
            client = TestClient(api.app)

            missing = client.get("/api/tenant/dashboard/context")
            self.assertEqual(missing.status_code, 401)

            invalid = client.get("/api/tenant/dashboard/context", headers={"X-Surfit-Tenant-Access": "wrong"})
            self.assertEqual(invalid.status_code, 403)

            expired = client.get("/api/tenant/dashboard/context", headers={"X-Surfit-Tenant-Access": "expired-key"})
            self.assertEqual(expired.status_code, 403)
            body = expired.json()
            detail = body.get("detail", {})
            self.assertEqual(detail.get("code"), "TENANT_DASHBOARD_ACCESS_EXPIRED")

    def test_missing_expiration_is_non_expiring(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            dashboard_access = tmp / "dashboard_access.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)
            _write_dashboard_access(dashboard_access)

            api = _load_api_module(allowlists, artifacts_root, db_path, dashboard_access)
            client = TestClient(api.app)

            resp_ctx = client.get("/api/tenant/dashboard/context", headers={"X-Surfit-Tenant-Access": "tenant-b-key"})
            self.assertEqual(resp_ctx.status_code, 200)
            body = resp_ctx.json()
            self.assertEqual(body["tenant_id"], "tenant_b")
            self.assertIsNone(body["key_expires_at"])

    def test_wave_decision_and_artifact_scoped_to_tenant(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            allowlists = tmp / "allowlists.json"
            dashboard_access = tmp / "dashboard_access.json"
            artifacts_root = tmp / "artifacts"
            db_path = tmp / "surfit.db"
            _write_allowlists(allowlists)
            _write_dashboard_access(dashboard_access)

            api = _load_api_module(allowlists, artifacts_root, db_path, dashboard_access)
            client = TestClient(api.app)

            conn = sqlite3.connect(api.DB_PATH)
            api.ensure_wave_tables(conn)

            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-a",
                    "tenant_a",
                    "agent-a",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{"system":"github","action":"read"}',
                    "complete",
                    "2026-03-14T10:00:00+00:00",
                    "2026-03-14T10:00:10+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO waves (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wave-b",
                    "tenant_b",
                    "agent-b",
                    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    "enterprise_multistage_execution_governance_policy_v1",
                    "runtime_check",
                    '{"system":"github","action":"read"}',
                    "complete",
                    "2026-03-14T11:00:00+00:00",
                    "2026-03-14T11:00:10+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-a", "tenant_a", "ALLOW", "ok", "POLICY_ALLOW", "gateway", "2026-03-14T10:00:11+00:00", None, "h1"),
            )
            conn.execute(
                """
                INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("wave-b", "tenant_b", "ALLOW", "ok", "POLICY_ALLOW", "gateway", "2026-03-14T11:00:11+00:00", None, "h2"),
            )
            conn.commit()
            conn.close()

            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_a",
                wave_id="wave-a",
                artifact_id="gart-a",
                timestamp="2026-03-14T10:00:12+00:00",
            )
            _write_artifact(
                artifacts_root=artifacts_root,
                tenant_id="tenant_b",
                wave_id="wave-b",
                artifact_id="gart-b",
                timestamp="2026-03-14T11:00:12+00:00",
            )

            own_wave = client.get(
                "/api/tenant/dashboard/waves/wave-a/decisions",
                headers={"X-Surfit-Tenant-Access": "tenant-a-key"},
            )
            self.assertEqual(own_wave.status_code, 200)
            self.assertEqual(own_wave.json()["tenant_id"], "tenant_a")

            other_wave = client.get(
                "/api/tenant/dashboard/waves/wave-b/decisions",
                headers={"X-Surfit-Tenant-Access": "tenant-a-key"},
            )
            self.assertEqual(other_wave.status_code, 404)

            own_artifact = client.get(
                "/api/tenant/dashboard/artifacts/gart-a",
                headers={"X-Surfit-Tenant-Access": "tenant-a-key"},
            )
            self.assertEqual(own_artifact.status_code, 200)
            self.assertEqual(own_artifact.json()["tenant_id"], "tenant_a")

            other_artifact = client.get(
                "/api/tenant/dashboard/artifacts/gart-b",
                headers={"X-Surfit-Tenant-Access": "tenant-a-key"},
            )
            self.assertEqual(other_artifact.status_code, 404)


if __name__ == "__main__":
    unittest.main()
