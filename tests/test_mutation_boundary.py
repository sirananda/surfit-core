from __future__ import annotations

import json
import sqlite3
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from surfit.runtime.mutation_boundary import MutationBoundaryConfig, MutationBoundaryService


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def _start_local_server() -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_service(*, replay_max_uses: int = 1000) -> MutationBoundaryService:
    return MutationBoundaryService(
        MutationBoundaryConfig(
            token_secret="boundary-test-secret",
            mutation_token_ttl_seconds=60,
            demo_safe_mode=True,
            proxy_timeout_seconds=2,
            proxy_max_response_bytes=1024 * 1024,
            token_replay_max_uses=replay_max_uses,
            token_replay_grace_seconds=60,
            market_intel_templates={"market_intelligence_digest_v1"},
            prod_config_target="demo_artifacts/prod_config.json",
            prod_config_allowed_keys={"logging.level"},
        ),
        resolve_connector_type=lambda template_id: "github"
        if template_id == "ENTERPRISE_GITHUB_GOVERNANCE_V1"
        else None,
        canonicalize_policy_manifest=_canonical,
        sha256_text=_sha256,
    )


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE waves (
            wave_id TEXT PRIMARY KEY,
            policy_manifest_hash TEXT,
            policy_manifest_json TEXT,
            tenant_id TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wave_id TEXT,
            decision TEXT,
            reason TEXT,
            rule TEXT,
            node TEXT
        )
        """
    )
    conn.commit()
    return conn


def _log_decision(conn: sqlite3.Connection, wave_id: str, decision: str, reason: str, rule: str, node: str) -> None:
    conn.execute(
        "INSERT INTO decisions (wave_id, decision, reason, rule, node) VALUES (?, ?, ?, ?, ?)",
        (wave_id, decision, reason, rule, node),
    )


class MutationBoundaryTests(unittest.TestCase):
    def test_missing_token_is_denied(self):
        service = _build_service()
        conn = _make_conn()
        try:
            status, payload = service.proxy_http(
                conn,
                {
                    "method": "GET",
                    "url": "http://127.0.0.1/demo",
                    "wave_mutation_token": None,
                },
                log_decision=_log_decision,
            )
            self.assertEqual(status, 403)
            self.assertEqual(payload["reason_code"], "TOKEN_MISSING")
        finally:
            conn.close()

    def test_proxy_allow_with_token_policy_runtime_intersection(self):
        service = _build_service()
        conn = _make_conn()
        server, port = _start_local_server()
        try:
            target_url = f"http://127.0.0.1:{port}/repo/review_commit"
            manifest_payload = {
                "http_proxy_allowlist": {
                    "allowed_domains": ["127.0.0.1"],
                    "allowed_methods": ["GET"],
                    "allowed_url_prefixes": [f"http://127.0.0.1:{port}/repo/"],
                },
                "template_runtime_scopes": {
                    "ENTERPRISE_GITHUB_GOVERNANCE_V1": {
                        "allowlisted_paths": ["/repo/docs/"],
                        "allowlisted_tools": ["github.review_commit"],
                        "allowlisted_actions": ["review_commit"],
                        "allowlisted_repos": ["surfit-demo-repo"],
                    }
                },
            }
            manifest_json = _canonical(manifest_payload)
            manifest_hash = _sha256(manifest_json)
            conn.execute(
                "INSERT INTO waves (wave_id, policy_manifest_hash, policy_manifest_json, tenant_id) VALUES (?, ?, ?, ?)",
                ("wave-allow", manifest_hash, manifest_json, "tenant_a"),
            )
            conn.commit()

            scope = service.build_mutation_scope(
                "ENTERPRISE_GITHUB_GOVERNANCE_V1",
                {
                    "connector_base_url": f"http://127.0.0.1:{port}",
                    "allowed_connector_prefixes": [f"http://127.0.0.1:{port}/repo/"],
                },
                manifest_payload,
            )
            token, _, _, _ = service.mint_wave_mutation_token(
                wave_id="wave-allow",
                agent_id="github_governance_agent",
                policy_manifest_hash=manifest_hash,
                policy_version="enterprise_github_governance_policy_v1",
                wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                scope=scope,
            )

            status, payload = service.proxy_http(
                conn,
                {
                    "method": "GET",
                    "url": target_url,
                    "wave_mutation_token": token,
                    "governance_context": {
                        "tool": "github.review_commit",
                        "target_path": "/repo/docs/update.md",
                        "requested_repo": "surfit-demo-repo",
                        "requested_action": "review_commit",
                    },
                },
                log_decision=_log_decision,
                api_tenant_id="tenant_a",
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "ALLOWED")
            self.assertEqual(payload["status_code"], 200)
        finally:
            server.shutdown()
            server.server_close()
            conn.close()

    def test_replay_threshold_is_enforced(self):
        service = _build_service(replay_max_uses=1)
        conn = _make_conn()
        server, port = _start_local_server()
        try:
            target_url = f"http://127.0.0.1:{port}/repo/review_commit"
            manifest_payload = {
                "http_proxy_allowlist": {
                    "allowed_domains": ["127.0.0.1"],
                    "allowed_methods": ["GET"],
                    "allowed_url_prefixes": [f"http://127.0.0.1:{port}/repo/"],
                }
            }
            manifest_json = _canonical(manifest_payload)
            manifest_hash = _sha256(manifest_json)
            conn.execute(
                "INSERT INTO waves (wave_id, policy_manifest_hash, policy_manifest_json, tenant_id) VALUES (?, ?, ?, ?)",
                ("wave-replay", manifest_hash, manifest_json, "tenant_a"),
            )
            conn.commit()
            token, _, _, _ = service.mint_wave_mutation_token(
                wave_id="wave-replay",
                agent_id="agent",
                policy_manifest_hash=manifest_hash,
                policy_version="policy",
                wave_template_id="market_intelligence_digest_v1",
                scope={
                    "http_proxy": {
                        "allowed_domains": ["127.0.0.1"],
                        "allowed_methods": ["GET"],
                        "allowed_url_prefixes": [f"http://127.0.0.1:{port}/repo/"],
                    }
                },
            )

            status1, _ = service.proxy_http(
                conn,
                {"method": "GET", "url": target_url, "wave_mutation_token": token},
                log_decision=_log_decision,
                api_tenant_id="tenant_a",
            )
            status2, payload2 = service.proxy_http(
                conn,
                {"method": "GET", "url": target_url, "wave_mutation_token": token},
                log_decision=_log_decision,
                api_tenant_id="tenant_a",
            )
            self.assertEqual(status1, 200)
            self.assertEqual(status2, 403)
            self.assertEqual(payload2["reason_code"], "TOKEN_REPLAY_DETECTED")
        finally:
            server.shutdown()
            server.server_close()
            conn.close()


if __name__ == "__main__":
    unittest.main()
