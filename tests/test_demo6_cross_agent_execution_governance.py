from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_allowlists(path: Path, port: int) -> None:
    payload = {
        "policy_manifest_version": "demo6-test-v1",
        "agent_wave_allowlist": {
            "openclaw_cross_agent_governance_agent": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"],
            "langgraph_cross_agent_governance_agent": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"],
            "internal_automation_cross_agent_agent": ["ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"],
        },
        "template_policy_allowlist": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": ["enterprise_multistage_execution_governance_policy_v1"],
        },
        "http_proxy_allowlist": {
            "allowed_domains": ["localhost", "127.0.0.1", "::1"],
            "allowed_methods": ["POST"],
            "allowed_url_prefixes": [
                f"http://127.0.0.1:{port}/github/create_branch",
                f"http://127.0.0.1:{port}/github/commit_file",
                f"http://127.0.0.1:{port}/github/open_pull_request",
                f"http://127.0.0.1:{port}/github/merge_pull_request",
            ],
        },
        "template_runtime_scopes": {
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {
                "allowlisted_paths": ["/docs/", "/agents/output/", "/reports/"],
                "denied_paths": [
                    "/.github/workflows/*",
                    "/infra/*",
                    "/security/*",
                    "/secrets/*",
                    "/src/*",
                    "/app/*",
                    "/backend/*",
                ],
                "allowlisted_tools": [
                    "github.create_branch",
                    "github.commit_file",
                    "github.open_pull_request",
                    "github.merge_pull_request",
                ],
                "allowlisted_actions": [
                    "create_branch",
                    "commit_file",
                    "open_pull_request",
                    "merge_pull_request",
                ],
                "denied_actions": ["force_push", "delete_branch"],
                "allowlisted_repos": ["surfit-demo-repo"],
                "github_policy": {
                    "allowed_repos": ["surfit-demo-repo"],
                    "allowed_paths": ["docs/*", "agents/output/*", "reports/*"],
                    "denied_paths": [
                        ".github/workflows/*",
                        "infra/*",
                        "security/*",
                        "secrets/*",
                        "src/*",
                        "app/*",
                        "backend/*",
                    ],
                    "allowed_actions": [
                        "create_branch",
                        "commit_file",
                        "open_pull_request",
                        "merge_pull_request",
                    ],
                    "denied_actions": ["force_push", "delete_branch"],
                    "require_approval_for_actions": ["merge_pull_request"],
                },
            }
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_api_module(db_path: Path, allowlists_path: Path):
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

    os.environ["SURFIT_DB_PATH"] = str(db_path)
    os.environ["SURFIT_POLICY_ALLOWLISTS_PATH"] = str(allowlists_path)
    os.environ["SURFIT_TOKEN_SECRET"] = "demo6-test-secret"
    os.environ["DEMO_SAFE_MODE"] = "1"

    if "api" in sys.modules:
        del sys.modules["api"]
    import api  # type: ignore

    importlib.reload(api)
    api.initialize_runtime_schema()
    return api


def _as_payload(resp):
    if isinstance(resp, dict):
        return 200, resp
    status = getattr(resp, "status_code", 500)
    body = getattr(resp, "body", b"{}")
    return status, json.loads(body.decode("utf-8"))


class _GitHubHandler(BaseHTTPRequestHandler):
    state = {
        "branches": {"main": {}},
        "prs": [],
    }

    def _json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8")) if raw else {}

        if self.path == "/github/create_branch":
            branch = str(payload.get("branch") or "wave/unknown")
            base = str(payload.get("base_branch") or "main")
            if base not in self.state["branches"]:
                self.state["branches"][base] = {}
            self.state["branches"][branch] = dict(self.state["branches"][base])
            self._json(
                {
                    "status": "created",
                    "github_event": {"branch": branch, "base_branch": base},
                    "decision": {"allow": True, "reason_code": "ALLOW"},
                }
            )
            return

        if self.path == "/github/commit_file":
            branch = str(payload.get("branch") or "main")
            path = str(payload.get("path") or "")
            content = str(payload.get("content") or "")
            self.state["branches"].setdefault(branch, {})[path] = content
            self._json(
                {
                    "status": "committed",
                    "github_event": {"branch": branch, "path": path},
                    "decision": {"allow": True, "reason_code": "ALLOW"},
                }
            )
            return

        if self.path == "/github/open_pull_request":
            pr_num = len(self.state["prs"]) + 1
            pr = {
                "number": pr_num,
                "title": payload.get("pr_title") or f"PR {pr_num}",
                "status": "open",
                "base_branch": payload.get("base_branch") or "main",
                "head_branch": payload.get("branch") or "wave/unknown",
            }
            self.state["prs"].append(pr)
            self._json(
                {
                    "status": "opened",
                    "github_event": {"pull_request": pr},
                    "decision": {"allow": True, "reason_code": "ALLOW"},
                }
            )
            return

        if self.path == "/github/merge_pull_request":
            approval = payload.get("approval_artifact") or {}
            linked_wave_id = str(payload.get("linked_wave_id") or "")
            approval_link = str(approval.get("linked_wave_id") or "")
            signature = str(approval.get("signature") or "")
            if not linked_wave_id or not approval_link or not signature or linked_wave_id != approval_link:
                self._json(
                    {
                        "status": "rejected",
                        "github_event": {},
                        "decision": {"allow": False, "reason_code": "APPROVAL_REQUIRED"},
                    }
                )
                return
            pr = next((x for x in self.state["prs"] if x.get("status") == "open"), None)
            if pr:
                pr["status"] = "merged"
            self._json(
                {
                    "status": "merged",
                    "github_event": {"pull_request": pr or {}},
                    "decision": {"allow": True, "reason_code": "ALLOW"},
                }
            )
            return

        self._json({"error": "not_found"}, status=404)

    def log_message(self, format: str, *args: object) -> None:
        return


def _start_server() -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), _GitHubHandler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


class Demo6CrossAgentExecutionGovernanceTests(unittest.TestCase):
    def test_cross_agent_governance_is_origin_neutral(self):
        server, port = _start_server()
        try:
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                db = tmp / "demo6.db"
                allowlists = tmp / "allowlists.json"
                _write_allowlists(allowlists, port)
                api = _load_api_module(db, allowlists)

                openclaw_req = api.WaveRunRequest(
                    agent_id="openclaw_cross_agent_governance_agent",
                    wave_template_id="ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    policy_version="enterprise_multistage_execution_governance_policy_v1",
                    intent="demo6 openclaw protected path",
                    context_refs={
                        "github_case": "cross_agent_openclaw_protected_path",
                        "agent_origin": "OpenClaw Agent",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo6_openclaw_deny.md",
                    },
                )
                _, openclaw_body = _as_payload(api.run_wave(openclaw_req))
                self.assertEqual((openclaw_body.get("connector_summary") or {}).get("reason_code"), "PATH_NOT_ALLOWED")
                self.assertEqual((openclaw_body.get("connector_summary") or {}).get("decision"), "DENY")
                openclaw_wave_id = openclaw_body.get("wave_id")
                self.assertTrue(openclaw_wave_id)
                _, openclaw_bundle = _as_payload(api.export_wave_bundle(openclaw_wave_id))
                openclaw_chain = openclaw_bundle.get("decision_chain") or []
                self.assertTrue(any((evt.get("decision") == "DENY" and evt.get("rule") == "PATH_NOT_ALLOWED") for evt in openclaw_chain))

                langgraph_req = api.WaveRunRequest(
                    agent_id="langgraph_cross_agent_governance_agent",
                    wave_template_id="ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    policy_version="enterprise_multistage_execution_governance_policy_v1",
                    intent="demo6 langgraph bounded workflow",
                    context_refs={
                        "github_case": "cross_agent_langgraph_pr_workflow",
                        "agent_origin": "LangGraph Agent",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo6_langgraph_allow.md",
                    },
                )
                _, langgraph_body = _as_payload(api.run_wave(langgraph_req))
                self.assertEqual(langgraph_body.get("status"), "running")
                langgraph_wave_id = langgraph_body.get("wave_id")
                self.assertTrue(langgraph_wave_id)
                langgraph_summary = (langgraph_body.get("connector_summary") or {})
                self.assertEqual(langgraph_summary.get("agent_origin"), "LangGraph Agent")
                self.assertEqual(langgraph_summary.get("reason_code"), "ALLOW")
                self.assertEqual(langgraph_summary.get("action_sequence"), ["create_branch", "commit_file", "open_pull_request"])

                internal_req = api.WaveRunRequest(
                    agent_id="internal_automation_cross_agent_agent",
                    wave_template_id="ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    policy_version="enterprise_multistage_execution_governance_policy_v1",
                    intent="demo6 internal merge without approval",
                    context_refs={
                        "github_case": "cross_agent_internal_merge_without_approval",
                        "agent_origin": "Internal Automation Script",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "linked_proposal_wave_id": langgraph_wave_id,
                        "output_report_path": "./outputs/test_demo6_internal_deny.md",
                    },
                )
                _, internal_body = _as_payload(api.run_wave(internal_req))
                self.assertEqual((internal_body.get("connector_summary") or {}).get("reason_code"), "APPROVAL_REQUIRED")
                self.assertEqual((internal_body.get("connector_summary") or {}).get("decision"), "DENY")
                internal_wave_id = internal_body.get("wave_id")
                self.assertTrue(internal_wave_id)
                _, internal_bundle = _as_payload(api.export_wave_bundle(internal_wave_id))
                internal_chain = internal_bundle.get("decision_chain") or []
                self.assertTrue(any((evt.get("decision") == "DENY" and evt.get("rule") == "APPROVAL_REQUIRED") for evt in internal_chain))

                langgraph_path_req = api.WaveRunRequest(
                    agent_id="langgraph_cross_agent_governance_agent",
                    wave_template_id="ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
                    policy_version="enterprise_multistage_execution_governance_policy_v1",
                    intent="demo6 langgraph protected path parity",
                    context_refs={
                        "github_case": "cross_agent_openclaw_protected_path",
                        "agent_origin": "LangGraph Agent",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo6_langgraph_path_deny.md",
                    },
                )
                _, langgraph_path_body = _as_payload(api.run_wave(langgraph_path_req))
                self.assertEqual((langgraph_path_body.get("connector_summary") or {}).get("reason_code"), "PATH_NOT_ALLOWED")
                self.assertEqual((langgraph_path_body.get("connector_summary") or {}).get("decision"), "DENY")

                self.assertEqual(
                    (openclaw_body.get("connector_summary") or {}).get("reason_code"),
                    (langgraph_path_body.get("connector_summary") or {}).get("reason_code"),
                )

                _, deny_bundle = _as_payload(api.export_wave_bundle(openclaw_wave_id))
                self.assertEqual((deny_bundle.get("wave") or {}).get("wave_id"), openclaw_wave_id)

                _, allow_bundle = _as_payload(api.export_wave_bundle(langgraph_wave_id))
                self.assertEqual((allow_bundle.get("wave") or {}).get("wave_id"), langgraph_wave_id)
                bundle_path = tmp / f"wave_bundle_{langgraph_wave_id}.json"
                bundle_path.write_text(json.dumps(allow_bundle, indent=2) + "\n", encoding="utf-8")
                verify = subprocess.run(
                    [sys.executable, "scripts/verify_wave_bundle.py", str(bundle_path)],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(verify.returncode, 0, msg=verify.stdout + verify.stderr)
                self.assertIn("PASS", verify.stdout)

                _, audit_verify = _as_payload(api.verify_audit(langgraph_wave_id))
                self.assertEqual(audit_verify.get("integrity_status"), "VALID")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
