from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class DemoHandlerError(Exception):
    code: str
    message: str
    node: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class DemoHandlerRequest:
    wave_id: str
    wave_template_id: str
    wave_token: str
    wave_mutation_token: str
    workspace_dir: str
    output_path: str
    approved_by: str
    context_refs: dict[str, Any] = field(default_factory=dict)
    connector_type: str | None = None
    connector_context: dict[str, Any] = field(default_factory=dict)
    policy_manifest_hash: str = ""
    policy_version: str = ""
    input_csv_path: str = ""
    target_path: str = ""
    sources: list[str] = field(default_factory=list)
    snapshot_dir: str = ""
    run_id: str = ""
    brief_goal: str = ""
    references: list[str] = field(default_factory=list)
    attempted_action: str = ""
    repo_base_url: str = ""
    integration_case: str = ""
    integration_base_url: str = ""


@dataclass(frozen=True)
class DemoHandlerDeps:
    project_root: Path
    ocean_proxy_http: Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]
    commit_output_write: Callable[..., str]
    log_decision: Callable[[str, str, str, str, str], None]
    dispatch_connector_action: Callable[..., dict[str, Any]]
    sha256_text: Callable[[str], str]
    sha256_file: Callable[[str], str | None]
    anthropic_module: Any


def execute_connector_case(
    request: DemoHandlerRequest,
    deps: DemoHandlerDeps,
    *,
    strict_deny: bool,
) -> dict[str, Any]:
    connector_type = str(request.connector_type or "")
    case_result = deps.dispatch_connector_action(
        connector_type=connector_type,
        wave_id=request.wave_id,
        wave_mutation_token=request.wave_mutation_token,
        context=request.connector_context,
        approved_by=request.approved_by,
        policy_manifest_hash=request.policy_manifest_hash,
        policy_version=request.policy_version,
    )
    allowed = bool(case_result.get("allowed"))
    reason_code = str(case_result.get("reason_code", "UNKNOWN"))
    message = str(case_result.get("message", ""))
    deps.log_decision(
        request.wave_id,
        "ALLOW" if allowed else "DENY",
        message if message else f"connector {connector_type} decision",
        reason_code if reason_code else "connector_decision",
        f"connector.{connector_type}.proxy",
    )

    rendered = str(case_result.get("report_markdown", ""))
    if not rendered:
        rendered = (
            f"# Connector Governance Report\n\n"
            f"Wave ID: {request.wave_id}\n"
            f"Connector: {connector_type}\n"
            f"Decision: {'ALLOW' if allowed else 'DENY'}\n"
            f"Reason code: {reason_code}\n"
            f"Message: {message}\n"
        )

    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content=rendered,
        node=f"connector.{connector_type}.write",
    )

    if not allowed and strict_deny:
        raise DemoHandlerError(
            code=reason_code if reason_code else "SCOPE_VIOLATION",
            message=f"{reason_code}: {message}",
            node=f"connector.{connector_type}.proxy",
        )

    summary = case_result.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    return {
        "workspace_output": workspace_output,
        "connector_type": connector_type,
        "connector_summary": summary,
        "decision_status": "ALLOWED" if allowed else "DENIED",
        "reason_code": reason_code,
    }
