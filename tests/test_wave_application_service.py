from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from surfit.demos.handlers._common import DemoHandlerError
from surfit.runtime.wave_application_service import (
    WaveApplicationService,
    WaveRunApplicationDeps,
    WaveRunApplicationRequest,
)
from surfit.runtime.wave_orchestrator import WaveRunPrepDeny


class _WaveExecutionError(Exception):
    def __init__(self, code: str, message: str, node: str):
        super().__init__(message)
        self.code = code
        self.node = node


class _OrchestratorStub:
    def __init__(self, prep_result, prep_deny):
        self.prep_result = prep_result
        self.prep_deny = prep_deny

    def prepare_wave_run(self, request, deps):
        return self.prep_result, self.prep_deny


class WaveApplicationServiceTests(unittest.TestCase):
    def _base_request(self, conn: sqlite3.Connection) -> WaveRunApplicationRequest:
        return WaveRunApplicationRequest(
            req=SimpleNamespace(agent_id="agent", wave_template_id="t1", policy_version="p1", intent="i", context_refs={}),
            tenant_id="tenant_a",
            wave_id="wave-1",
            conn=conn,
            workspace_dir="/tmp/wave-1",
            market_intel_templates={"market_intelligence_digest_v1"},
            prod_config_target="demo_artifacts/prod_config.json",
            max_runtime_seconds=30,
        )

    def test_successful_run_wave_composition(self):
        service = WaveApplicationService()
        conn = sqlite3.connect(":memory:")
        prep_result = SimpleNamespace(
            policy_manifest_hash="abcdef1234567890",
            prepared_context=SimpleNamespace(output_path="./outputs/report.md"),
            wave_mutation_token="tok-1",
            wave_mutation_token_expires_at="2099-01-01T00:00:00+00:00",
            handler_request=SimpleNamespace(),
        )
        status_updates: list[str] = []
        manifests_written: list[str] = []
        deps = WaveRunApplicationDeps(
            orchestrator=_OrchestratorStub(prep_result, None),
            build_prep_deps=lambda _conn: SimpleNamespace(),
            build_handler_deps=lambda _conn: SimpleNamespace(),
            dispatch_template_handler=lambda _req, _deps: {
                "demo3_slack_notification": "sent",
                "connector_summary": {"result": "ok"},
            },
            write_manifest=lambda _conn, _wave_id, _workspace_dir, _req, _output_path, _evidence: manifests_written.append(_wave_id) or ("m", "h"),
            update_wave_status=lambda _conn, _wave_id, status, _ec, _em, _en: status_updates.append(status),
            log_decision=lambda *_args, **_kwargs: None,
            sha256_file=lambda _path: "output-sha",
            record_prep_deny=lambda *_args, **_kwargs: {"status": "failed"},
            load_policy_snapshot=lambda: {"manifest_hash": "h", "manifest_version": "v", "manifest_json": "{}"},
            monotonic=lambda: 1.0,
            wave_execution_error_type=_WaveExecutionError,
        )

        try:
            result = service.run_wave(self._base_request(conn), deps)
            self.assertIsNone(result.http_status)
            self.assertEqual(result.payload["status"], "running")
            self.assertEqual(result.payload["wave_mutation_token"], "tok-1")
            self.assertEqual(result.payload["policy_manifest_hash_prefix"], "abcdef123456")
            self.assertIn("connector_summary", result.payload)
            self.assertIn("demo4_summary", result.payload)
            self.assertIn("demo5_summary", result.payload)
            self.assertEqual(status_updates[-1], "complete")
            self.assertEqual(manifests_written[-1], "wave-1")
        finally:
            conn.close()

    def test_prep_deny_is_propagated_with_status(self):
        service = WaveApplicationService()
        conn = sqlite3.connect(":memory:")
        prep_deny = WaveRunPrepDeny(
            code="AGENT_NOT_AUTHORIZED",
            message="blocked",
            node="run_wave",
            http_status=403,
            rule="agent_wave_allowlist",
        )
        deps = WaveRunApplicationDeps(
            orchestrator=_OrchestratorStub(None, prep_deny),
            build_prep_deps=lambda _conn: SimpleNamespace(),
            build_handler_deps=lambda _conn: SimpleNamespace(),
            dispatch_template_handler=lambda _req, _deps: {},
            write_manifest=lambda *_args, **_kwargs: ("", ""),
            update_wave_status=lambda *_args, **_kwargs: None,
            log_decision=lambda *_args, **_kwargs: None,
            sha256_file=lambda _path: None,
            record_prep_deny=lambda _conn, _wave_id, _req, _deny, _tenant_id, _snapshot: {
                "wave_id": _wave_id,
                "tenant_id": _tenant_id,
                "status": "failed",
                "error": {"code": _deny.code},
            },
            load_policy_snapshot=lambda: {"manifest_hash": "h", "manifest_version": "v", "manifest_json": "{}"},
            monotonic=lambda: 1.0,
            wave_execution_error_type=_WaveExecutionError,
        )

        try:
            result = service.run_wave(self._base_request(conn), deps)
            self.assertEqual(result.http_status, 403)
            self.assertEqual(result.payload["status"], "failed")
            self.assertEqual(result.payload["error"]["code"], "AGENT_NOT_AUTHORIZED")
        finally:
            conn.close()

    def test_handler_failure_maps_to_failed_payload(self):
        service = WaveApplicationService()
        conn = sqlite3.connect(":memory:")
        prep_result = SimpleNamespace(
            policy_manifest_hash="abc123",
            prepared_context=SimpleNamespace(output_path="./outputs/report.md"),
            wave_mutation_token="tok-2",
            wave_mutation_token_expires_at="2099-01-01T00:00:00+00:00",
            handler_request=SimpleNamespace(),
        )
        status_updates: list[str] = []
        deps = WaveRunApplicationDeps(
            orchestrator=_OrchestratorStub(prep_result, None),
            build_prep_deps=lambda _conn: SimpleNamespace(),
            build_handler_deps=lambda _conn: SimpleNamespace(),
            dispatch_template_handler=lambda _req, _deps: (_ for _ in ()).throw(
                DemoHandlerError("SCOPE_VIOLATION", "blocked", "demo.handler")
            ),
            write_manifest=lambda *_args, **_kwargs: ("", ""),
            update_wave_status=lambda _conn, _wave_id, status, _ec, _em, _en: status_updates.append(status),
            log_decision=lambda *_args, **_kwargs: None,
            sha256_file=lambda _path: None,
            record_prep_deny=lambda *_args, **_kwargs: {"status": "failed"},
            load_policy_snapshot=lambda: {"manifest_hash": "h", "manifest_version": "v", "manifest_json": "{}"},
            monotonic=lambda: 1.0,
            wave_execution_error_type=_WaveExecutionError,
        )

        try:
            result = service.run_wave(self._base_request(conn), deps)
            self.assertIsNone(result.http_status)
            self.assertEqual(result.payload["status"], "failed")
            self.assertEqual(result.payload["error"]["code"], "SCOPE_VIOLATION")
            self.assertEqual(status_updates[-1], "failed")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
