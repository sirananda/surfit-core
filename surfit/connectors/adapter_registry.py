from __future__ import annotations

from typing import Any, Callable


_GITHUB_TEMPLATES = {
    "ENTERPRISE_GITHUB_GOVERNANCE_V1",
    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1",
}


def resolve_connector_type(wave_template_id: str) -> str | None:
    if str(wave_template_id) in _GITHUB_TEMPLATES:
        return "github"
    return None


def prepare_connector_context(wave_template_id: str, context_refs: dict[str, Any]) -> dict[str, Any]:
    _ = wave_template_id
    return dict(context_refs or {})


def dispatch_connector_action(
    *,
    connector_type: str,
    wave_id: str,
    wave_mutation_token: str,
    context: dict[str, Any],
    approved_by: str,
    policy_manifest_hash: str,
    policy_version: str,
    proxy_executor: Callable[[dict[str, Any]], tuple[int, dict[str, Any]]],
) -> dict[str, Any]:
    if connector_type != "github":
        return {
            "allowed": False,
            "reason_code": "CONNECTOR_NOT_SUPPORTED",
            "message": f"Connector '{connector_type}' is not supported.",
            "summary": {},
        }

    # Import lazily so missing adapter package does not crash API startup.
    try:
        from adapters.github_connector.github_demo_service import run_governed_github_action  # type: ignore
    except Exception as exc:
        return {
            "allowed": False,
            "reason_code": "CONNECTOR_RUNTIME_UNAVAILABLE",
            "message": f"GitHub connector unavailable: {exc}",
            "summary": {},
        }

    return run_governed_github_action(
        wave_id=wave_id,
        wave_mutation_token=wave_mutation_token,
        context=context,
        approved_by=approved_by,
        policy_manifest_hash=policy_manifest_hash,
        policy_version=policy_version,
        proxy_executor=proxy_executor,
    )
