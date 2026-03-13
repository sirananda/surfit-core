from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ContextPrepError:
    code: str
    message: str
    rule: str
    http_status: int = 422
    node: str = "run_wave"


@dataclass(frozen=True)
class ContextPrepDecision:
    decision: str
    reason: str
    rule: str
    node: str


@dataclass(frozen=True)
class PreparedWaveContext:
    output_path: str
    input_path: str = "n/a"
    snapshot_dir: str | None = None
    sources: list[str] = field(default_factory=list)
    target_path: str = "n/a"
    brief_goal: str = ""
    reference_paths: list[str] = field(default_factory=list)
    repo_base_url: str = ""
    attempted_action: str = ""
    integration_case: str = ""
    integration_base_url: str = ""
    connector_context: dict[str, Any] = field(default_factory=dict)
    context_updates: dict[str, Any] = field(default_factory=dict)
    decisions: list[ContextPrepDecision] = field(default_factory=list)


def prepare_wave_context(
    *,
    wave_template_id: str,
    context_refs: dict[str, Any],
    intent: str,
    connector_type: str | None,
    market_intel_templates: set[str],
    prod_config_target: str,
    normalize_repo_relative: Callable[[str], str],
    is_under: Callable[[str, str], bool],
    prepare_connector_context: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> tuple[PreparedWaveContext | None, ContextPrepError | None]:
    if wave_template_id == "production_config_change_v1":
        target_path = str(context_refs.get("target_path", ""))
        output_path = str(context_refs.get("output_report_path", ""))
        if not target_path or not output_path:
            return None, ContextPrepError("BAD_CONTEXT", "Missing required context: target_path and output_report_path", "context_required_fields")
        normalized = normalize_repo_relative(target_path)
        if normalized != normalize_repo_relative(prod_config_target):
            return None, ContextPrepError("PATH_VIOLATION", "target_path is not allowlisted for production_config_agent", "target_path_allowlist")
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_report_path must be under ./outputs/", "output_path_prefix")
        return PreparedWaveContext(
            output_path=output_path,
            target_path=target_path,
            decisions=[ContextPrepDecision("ALLOW", "target path allowlisted", "target_path_allowlist", "run_wave")],
        ), None

    if wave_template_id in market_intel_templates:
        sources = context_refs.get("sources", [])
        output_path = str(context_refs.get("output_digest_path", ""))
        snapshot_dir = str(context_refs.get("snapshot_dir", "./data/marketing_snapshots"))
        if not sources or not output_path:
            return None, ContextPrepError("BAD_CONTEXT", "Missing required context: sources and output_digest_path", "context_required_fields")
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_digest_path must be under ./outputs/", "output_path_prefix")
        return PreparedWaveContext(
            output_path=output_path,
            snapshot_dir=snapshot_dir,
            sources=[str(x) for x in sources],
            decisions=[ContextPrepDecision("ALLOW", "output path within allowed prefix", "output_path_prefix", "run_wave")],
        ), None

    if wave_template_id == "surfit_builder_brief_v1":
        output_path = str(context_refs.get("output_brief_path", ""))
        write_approval = bool(context_refs.get("write_approval", False))
        if not write_approval:
            return None, ContextPrepError(
                "APPROVAL_REQUIRED",
                "Builder write approval required (set context_refs.write_approval=true).",
                "builder_write_approval",
                http_status=403,
            )
        if not output_path:
            return None, ContextPrepError("BAD_CONTEXT", "Missing required context: output_brief_path", "context_required_fields")
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_brief_path must be under ./outputs/", "output_path_prefix")
        brief_goal = str(context_refs.get("brief_goal", intent or "Build Surfit roadmap"))
        reference_paths = context_refs.get("reference_paths", ["README.md", "docs/m14_runtime_alignment.md"])
        sanitized = []
        for p in reference_paths[:10]:
            norm = normalize_repo_relative(str(p))
            if norm == "README.md" or norm.startswith("docs/"):
                sanitized.append(norm)
        if not sanitized:
            sanitized = ["README.md"]
        return PreparedWaveContext(
            output_path=output_path,
            brief_goal=brief_goal,
            reference_paths=sanitized,
            decisions=[ContextPrepDecision("ALLOW", "builder paths validated", "builder_context_validation", "run_wave")],
        ), None

    if wave_template_id == "ENTERPRISE_CHANGE_CONTROL_V1":
        repo_base_url = str(context_refs.get("repo_base_url", "http://127.0.0.1:8040")).strip()
        attempted_action = str(context_refs.get("attempted_action", "pull_request")).strip() or "pull_request"
        allowed_action = str(context_refs.get("allowed_action", "pull_request")).strip() or "pull_request"
        output_path = str(context_refs.get("output_report_path", "./outputs/enterprise_change_control_report.md"))
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_report_path must be under ./outputs/", "output_path_prefix")
        if attempted_action not in {"pull_request", "merge", "config_change"}:
            return None, ContextPrepError("BAD_CONTEXT", "attempted_action must be one of pull_request, merge, config_change", "attempted_action_allowed")
        return PreparedWaveContext(
            output_path=output_path,
            repo_base_url=repo_base_url,
            attempted_action=attempted_action,
            context_updates={"allowed_enterprise_prefix": f"{repo_base_url.rstrip('/')}/repo/{allowed_action}"},
            decisions=[ContextPrepDecision("ALLOW", "enterprise template context validated", "enterprise_context_validation", "run_wave")],
        ), None

    if wave_template_id == "ENTERPRISE_INTEGRATION_GOVERNANCE_V1":
        integration_base_url = str(context_refs.get("integration_base_url", "http://127.0.0.1:8040")).strip()
        integration_case = str(context_refs.get("integration_case", "github")).strip().lower() or "github"
        output_path = str(context_refs.get("output_report_path", "./outputs/enterprise_integration_governance_report.md"))
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_report_path must be under ./outputs/", "output_path_prefix")
        if integration_case not in {"github", "aws", "slack"}:
            return None, ContextPrepError("BAD_CONTEXT", "integration_case must be github, aws, or slack", "integration_case_allowed")
        updates = {
            "allowed_integration_prefixes": [
                f"{integration_base_url.rstrip('/')}/repo/file_update",
                f"{integration_base_url.rstrip('/')}/aws/iam/modify_policy",
                f"{integration_base_url.rstrip('/')}/slack/channel/post_message",
            ]
        }
        return PreparedWaveContext(
            output_path=output_path,
            integration_case=integration_case,
            integration_base_url=integration_base_url,
            context_updates=updates,
            decisions=[ContextPrepDecision("ALLOW", "enterprise integration template context validated", "enterprise_integration_context_validation", "run_wave")],
        ), None

    if connector_type is not None:
        try:
            connector_context = prepare_connector_context(connector_type, context_refs)
        except Exception as e:
            code = getattr(e, "code", "BAD_CONTEXT")
            message = getattr(e, "message", str(e))
            rule = getattr(e, "rule", "connector_context_validation")
            return None, ContextPrepError(code, message, rule)
        output_path = str(connector_context.get("output_report_path", context_refs.get("output_report_path", "./outputs/connector_report.md")))
        if not is_under("./outputs", output_path):
            return None, ContextPrepError("PATH_VIOLATION", "output_report_path must be under ./outputs/", "output_path_prefix")
        return PreparedWaveContext(
            output_path=output_path,
            connector_context=connector_context,
            context_updates=connector_context,
            decisions=[ContextPrepDecision("ALLOW", "connector template context validated", "connector_context_validation", "run_wave")],
        ), None

    input_path = str(context_refs.get("input_csv_path", ""))
    output_path = str(context_refs.get("output_report_path", ""))
    if not input_path or not output_path:
        return None, ContextPrepError("BAD_CONTEXT", "Missing required context paths", "context_required_fields")
    if not is_under("./data", input_path):
        return None, ContextPrepError("PATH_VIOLATION", "input_csv_path must be under ./data/", "input_path_prefix")
    if not is_under("./outputs", output_path):
        return None, ContextPrepError("PATH_VIOLATION", "output_report_path must be under ./outputs/", "output_path_prefix")
    return PreparedWaveContext(
        output_path=output_path,
        input_path=input_path,
        decisions=[ContextPrepDecision("ALLOW", "input/output paths validated", "path_constraints", "run_wave")],
    ), None

