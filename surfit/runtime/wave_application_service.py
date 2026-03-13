from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any, Callable

from surfit.demos.handlers._common import DemoHandlerDeps, DemoHandlerError, DemoHandlerRequest

from .wave_orchestrator import (
    WaveOrchestrator,
    WaveRunPrepDeny,
    WaveRunPreparationDeps,
    WaveRunPreparationRequest,
    WaveRunPreparationResult,
)


@dataclass(frozen=True)
class WaveRunApplicationRequest:
    req: Any
    tenant_id: str
    wave_id: str
    conn: sqlite3.Connection
    workspace_dir: str
    market_intel_templates: set[str]
    prod_config_target: str
    max_runtime_seconds: int


@dataclass(frozen=True)
class WaveRunApplicationResult:
    payload: dict[str, Any]
    http_status: int | None = None


@dataclass(frozen=True)
class WaveRunApplicationDeps:
    orchestrator: WaveOrchestrator
    build_prep_deps: Callable[[sqlite3.Connection], WaveRunPreparationDeps]
    build_handler_deps: Callable[[sqlite3.Connection], DemoHandlerDeps]
    dispatch_template_handler: Callable[[DemoHandlerRequest, DemoHandlerDeps], dict[str, Any]]
    write_manifest: Callable[[sqlite3.Connection, str, str, Any, str, dict[str, Any]], tuple[str, str]]
    update_wave_status: Callable[[sqlite3.Connection, str, str, str | None, str | None, str | None], None]
    log_decision: Callable[[sqlite3.Connection, str, str, str, str, str], None]
    sha256_file: Callable[[str], str | None]
    record_prep_deny: Callable[[sqlite3.Connection, str, Any, WaveRunPrepDeny, str, dict[str, Any]], dict[str, Any]]
    load_policy_snapshot: Callable[[], dict[str, Any]]
    monotonic: Callable[[], float]
    wave_execution_error_type: type[Exception]


class WaveApplicationService:
    def run_wave(
        self,
        request: WaveRunApplicationRequest,
        deps: WaveRunApplicationDeps,
    ) -> WaveRunApplicationResult:
        prep_req = WaveRunPreparationRequest(
            req=request.req,
            tenant_id=request.tenant_id,
            wave_id=request.wave_id,
            workspace_dir=request.workspace_dir,
            market_intel_templates=request.market_intel_templates,
            prod_config_target=request.prod_config_target,
        )
        prep_result, prep_deny = deps.orchestrator.prepare_wave_run(
            prep_req,
            deps.build_prep_deps(request.conn),
        )

        if prep_deny:
            snapshot = deps.load_policy_snapshot()
            payload = deps.record_prep_deny(
                request.conn,
                request.wave_id,
                request.req,
                prep_deny,
                request.tenant_id,
                snapshot,
            )
            return WaveRunApplicationResult(payload=payload, http_status=prep_deny.http_status)

        assert prep_result is not None
        return self._execute_wave(prep_result, request, deps)

    def _execute_wave(
        self,
        prep_result: WaveRunPreparationResult,
        request: WaveRunApplicationRequest,
        deps: WaveRunApplicationDeps,
    ) -> WaveRunApplicationResult:
        pinned_policy_manifest_hash = prep_result.policy_manifest_hash
        output_path = prep_result.prepared_context.output_path
        wave_mutation_token = prep_result.wave_mutation_token
        wave_mutation_token_expires_at = prep_result.wave_mutation_token_expires_at
        started = deps.monotonic()

        try:
            handler_request = prep_result.handler_request
            handler_deps = deps.build_handler_deps(request.conn)
            try:
                evidence = deps.dispatch_template_handler(handler_request, handler_deps)
            except DemoHandlerError as e:
                raise deps.wave_execution_error_type(e.code, e.message, e.node)
            if not evidence:
                raise deps.wave_execution_error_type("WAVE_TEMPLATE_INVALID", "Unsupported wave template.", "run_wave")

            elapsed = deps.monotonic() - started
            if elapsed > request.max_runtime_seconds:
                raise TimeoutError(f"Wave exceeded max runtime of {request.max_runtime_seconds}s")

            output_hash = deps.sha256_file(output_path)
            evidence["output_hash"] = output_hash
            evidence["workspace_dir"] = request.workspace_dir
            deps.write_manifest(
                request.conn,
                request.wave_id,
                request.workspace_dir,
                request.req,
                output_path,
                evidence,
            )
            deps.update_wave_status(
                request.conn,
                request.wave_id,
                "complete",
                None,
                None,
                None,
            )
            request.conn.commit()

            response_payload: dict[str, Any] = {
                "wave_id": request.wave_id,
                "tenant_id": request.tenant_id,
                "status": "running",
                "wave_token": wave_mutation_token,
                "wave_mutation_token": wave_mutation_token,
                "wave_mutation_token_expires_at": wave_mutation_token_expires_at,
                "policy_manifest_hash": pinned_policy_manifest_hash,
                "policy_manifest_hash_prefix": pinned_policy_manifest_hash[:12],
            }
            if isinstance(evidence, dict) and evidence.get("demo3_slack_notification"):
                response_payload["demo3_slack_notification"] = evidence.get("demo3_slack_notification")
            if isinstance(evidence, dict) and isinstance(evidence.get("connector_summary"), dict):
                response_payload["connector_summary"] = evidence.get("connector_summary")
                response_payload["demo4_summary"] = evidence.get("connector_summary")
                response_payload["demo5_summary"] = evidence.get("connector_summary")
            return WaveRunApplicationResult(payload=response_payload)

        except Exception as e:
            if isinstance(e, deps.wave_execution_error_type):
                err_code = str(getattr(e, "code", "WAVE_EXECUTION_ERROR"))
                err_node = str(getattr(e, "node", "run_wave"))
                err_message = str(e)
            elif isinstance(e, TimeoutError):
                err_code = "WAVE_TIMEOUT"
                err_node = "run_wave"
                err_message = str(e)
            else:
                err_code = "WAVE_EXECUTION_ERROR"
                err_node = "run_wave"
                err_message = str(e)

            deps.log_decision(request.conn, request.wave_id, "DENY", err_message, err_code, err_node)
            deps.update_wave_status(
                request.conn,
                request.wave_id,
                "failed",
                err_code,
                err_message,
                err_node,
            )
            request.conn.commit()
            return WaveRunApplicationResult(
                payload={
                    "wave_id": request.wave_id,
                    "tenant_id": request.tenant_id,
                    "status": "failed",
                    "error": {
                        "code": err_code,
                        "message": err_message,
                        "node": err_node,
                    },
                }
            )
