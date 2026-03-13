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

from adapters.github_connector.github_client import GitHubActionRequest, GitHubSimulationStore, execute_github_action
from adapters.github_connector.github_policy_adapter import GitHubPolicyConstraints, evaluate_request


def _write_allowlists(path: Path, port: int) -> None:
    payload = {
        "policy_manifest_version": "demo4-test-v1",
        "agent_wave_allowlist": {
            "github_governance_agent": ["ENTERPRISE_GITHUB_GOVERNANCE_V1"],
        },
        "template_policy_allowlist": {
            "ENTERPRISE_GITHUB_GOVERNANCE_V1": ["enterprise_github_governance_policy_v1"],
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
            "ENTERPRISE_GITHUB_GOVERNANCE_V1": {
                "allowlisted_paths": ["/docs/", "/agents/output/", "/reports/"],
                "denied_paths": ["/.github/workflows/*", "/infra/*", "/security/*", "/secrets/*", "/src/*", "/app/*", "/backend/*"],
                "allowlisted_tools": [
                    "github.create_branch",
                    "github.commit_file",
                    "github.open_pull_request",
                ],
                "allowlisted_actions": ["create_branch", "commit_file", "open_pull_request"],
                "denied_actions": ["merge_pull_request", "force_push", "delete_branch"],
                "allowlisted_repos": ["surfit-demo-repo"],
                "github_policy": {
                    "allowed_repos": ["surfit-demo-repo"],
                    "allowed_paths": ["docs/*", "agents/output/*", "reports/*"],
                    "denied_paths": [".github/workflows/*", "infra/*", "security/*", "secrets/*", "src/*", "app/*", "backend/*"],
                    "allowed_actions": ["create_branch", "commit_file", "open_pull_request"],
                    "denied_actions": ["merge_pull_request", "force_push", "delete_branch"],
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
    os.environ["SURFIT_TOKEN_SECRET"] = "demo4-test-secret"
    os.environ["DEMO_SAFE_MODE"] = "1"

    if "api" in sys.modules:
        del sys.modules["api"]
    import api  # type: ignore

    importlib.reload(api)
    api.initialize_runtime_schema()
    return api


class _GitHubHandler(BaseHTTPRequestHandler):
    state = {
        "branches": {"main": {}},
        "prs": [],
    }

    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8")) if raw else {}

        if self.path == "/github/create_branch":
            branch = payload.get("branch") or "wave/unknown"
            base = payload.get("base_branch") or "main"
            if base not in self.state["branches"]:
                self.state["branches"][base] = {}
            self.state["branches"][branch] = dict(self.state["branches"][base])
            self._json({"status": "created", "branch": branch, "base_branch": base})
            return

        if self.path == "/github/commit_file":
            branch = payload.get("branch") or "main"
            path = str(payload.get("path") or "")
            content = str(payload.get("content") or "")
            self.state["branches"].setdefault(branch, {})[path] = content
            self._json({"status": "committed", "branch": branch, "path": path})
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
            self._json({"status": "opened", "pull_request": pr})
            return

        if self.path == "/github/merge_pull_request":
            self._json({"status": "merged"})
            return

        self._json({"error": "not_found"}, status=404)

    def log_message(self, format, *args):
        return


def _start_server() -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), _GitHubHandler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _as_payload(resp):
    if isinstance(resp, dict):
        return 200, resp
    status = getattr(resp, "status_code", 500)
    body = getattr(resp, "body", b"{}")
    return status, json.loads(body.decode("utf-8"))


class GitHubConnectorTests(unittest.TestCase):
    def test_policy_adapter_denials(self):
        constraints = GitHubPolicyConstraints(
            allowed_repos=["surfit-demo-repo"],
            allowed_paths=["docs/*"],
            denied_paths=[".github/workflows/*"],
            allowed_actions=["commit_file"],
            denied_actions=["merge_pull_request"],
        )
        repo_decision = evaluate_request(
            repo="other-repo",
            path="docs/x.md",
            action="commit_file",
            constraints=constraints,
            simulation_mode=True,
            real_mode_enabled=False,
        )
        self.assertFalse(repo_decision.allow)
        self.assertEqual(repo_decision.reason_code, "REPO_NOT_ALLOWED")

        path_decision = evaluate_request(
            repo="surfit-demo-repo",
            path=".github/workflows/deploy.yml",
            action="commit_file",
            constraints=constraints,
            simulation_mode=True,
            real_mode_enabled=False,
        )
        self.assertFalse(path_decision.allow)
        self.assertEqual(path_decision.reason_code, "PATH_NOT_ALLOWED")

        action_decision = evaluate_request(
            repo="surfit-demo-repo",
            path="docs/x.md",
            action="merge_pull_request",
            constraints=constraints,
            simulation_mode=True,
            real_mode_enabled=False,
        )
        self.assertFalse(action_decision.allow)
        self.assertEqual(action_decision.reason_code, "ACTION_NOT_ALLOWED")

        mode_decision = evaluate_request(
            repo="surfit-demo-repo",
            path="docs/x.md",
            action="commit_file",
            constraints=constraints,
            simulation_mode=False,
            real_mode_enabled=False,
        )
        self.assertFalse(mode_decision.allow)
        self.assertEqual(mode_decision.reason_code, "MODE_NOT_ENABLED")

    def test_simulation_state_mutations(self):
        constraints = GitHubPolicyConstraints(
            allowed_repos=["surfit-demo-repo"],
            allowed_paths=["docs/*"],
            denied_paths=[],
            allowed_actions=["create_branch", "commit_file", "open_pull_request"],
            denied_actions=["merge_pull_request"],
        )
        with tempfile.TemporaryDirectory() as td:
            store = GitHubSimulationStore(Path(td))

            create = execute_github_action(
                store=store,
                request=GitHubActionRequest(action_type="create_branch", repo="surfit-demo-repo", branch="wave/1", base_branch="main"),
                constraints=constraints,
            )
            self.assertTrue(create["decision"]["allow"])

            commit = execute_github_action(
                store=store,
                request=GitHubActionRequest(
                    action_type="commit_file",
                    repo="surfit-demo-repo",
                    branch="wave/1",
                    path="docs/proposal.md",
                    content="# proposal\n",
                    commit_message="demo",
                ),
                constraints=constraints,
            )
            self.assertTrue(commit["decision"]["allow"])
            self.assertEqual(commit["result"]["status"], "committed")

            pr = execute_github_action(
                store=store,
                request=GitHubActionRequest(
                    action_type="open_pull_request",
                    repo="surfit-demo-repo",
                    branch="wave/1",
                    base_branch="main",
                    pr_title="Demo PR",
                ),
                constraints=constraints,
            )
            self.assertTrue(pr["decision"]["allow"])
            self.assertEqual(pr["result"]["status"], "opened")

    def test_wave_demo4_end_to_end_with_proof(self):
        server, port = _start_server()
        try:
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                db = tmp / "demo4.db"
                allowlists = tmp / "allowlists.json"
                _write_allowlists(allowlists, port)
                api = _load_api_module(db, allowlists)

                path_req = api.WaveRunRequest(
                    agent_id="github_governance_agent",
                    wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                    policy_version="enterprise_github_governance_policy_v1",
                    intent="demo4 path deny",
                    context_refs={
                        "github_case": "unauthorized_path",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo4_path.md",
                    },
                )
                _, path_body = _as_payload(api.run_wave(path_req))
                self.assertEqual(path_body.get("status"), "failed")
                self.assertIn((path_body.get("error") or {}).get("code"), {"PATH_NOT_ALLOWED", "SCOPE_VIOLATION"})

                action_req = api.WaveRunRequest(
                    agent_id="github_governance_agent",
                    wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                    policy_version="enterprise_github_governance_policy_v1",
                    intent="demo4 action deny",
                    context_refs={
                        "github_case": "unauthorized_action",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo4_action.md",
                    },
                )
                _, action_body = _as_payload(api.run_wave(action_req))
                self.assertEqual(action_body.get("status"), "failed")
                self.assertIn((action_body.get("error") or {}).get("code"), {"ACTION_NOT_ALLOWED", "SCOPE_VIOLATION"})

                repo_req = api.WaveRunRequest(
                    agent_id="github_governance_agent",
                    wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                    policy_version="enterprise_github_governance_policy_v1",
                    intent="demo4 repo deny",
                    context_refs={
                        "github_case": "allowed_pr_workflow",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "unapproved-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo4_repo.md",
                    },
                )
                _, repo_body = _as_payload(api.run_wave(repo_req))
                self.assertEqual(repo_body.get("status"), "failed")
                self.assertEqual((repo_body.get("error") or {}).get("code"), "REPO_NOT_ALLOWED")

                allow_req = api.WaveRunRequest(
                    agent_id="github_governance_agent",
                    wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                    policy_version="enterprise_github_governance_policy_v1",
                    intent="demo4 allow",
                    context_refs={
                        "github_case": "allowed_pr_workflow",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "simulation",
                        "output_report_path": "./outputs/test_demo4_allow.md",
                    },
                )
                _, allow_body = _as_payload(api.run_wave(allow_req))
                self.assertEqual(allow_body.get("status"), "running")
                wave_id = allow_body.get("wave_id")
                self.assertTrue((allow_body.get("demo4_summary") or {}).get("pull_request"))

                _, bundle = _as_payload(api.export_wave_bundle(wave_id))
                bundle_path = tmp / f"wave_bundle_{wave_id}.json"
                bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
                verify = subprocess.run(
                    [sys.executable, "scripts/verify_wave_bundle.py", str(bundle_path)],
                    cwd=str(Path(__file__).resolve().parents[1]),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(verify.returncode, 0, msg=verify.stdout + verify.stderr)
                self.assertIn("PASS", verify.stdout)

                mode_req = api.WaveRunRequest(
                    agent_id="github_governance_agent",
                    wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
                    policy_version="enterprise_github_governance_policy_v1",
                    intent="demo4 real mode",
                    context_refs={
                        "github_case": "allowed_pr_workflow",
                        "github_base_url": f"http://127.0.0.1:{port}",
                        "repo": "surfit-demo-repo",
                        "mode": "real",
                        "output_report_path": "./outputs/test_demo4_real.md",
                    },
                )
                _, mode_body = _as_payload(api.run_wave(mode_req))
                self.assertEqual(mode_body.get("status"), "failed")
                self.assertEqual((mode_body.get("error") or {}).get("code"), "MODE_NOT_ENABLED")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
