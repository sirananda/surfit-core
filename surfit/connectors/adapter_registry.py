from __future__ import annotations

from typing import Any, Callable

from .base_connector import BaseConnector, ConnectorExecutionResult


class ConnectorValidationError(ValueError):
    def __init__(self, code: str, message: str, rule: str):
        super().__init__(message)
        self.code = code
        self.message = message
        self.rule = rule


CONNECTOR_TEMPLATE_MAP: dict[str, str] = {
    "ENTERPRISE_GITHUB_GOVERNANCE_V1": "github",
    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": "github",
}


def resolve_connector_type(wave_template_id: str) -> str | None:
    return CONNECTOR_TEMPLATE_MAP.get(str(wave_template_id))


def prepare_connector_context(wave_template_id: str, context_refs: dict[str, Any]) -> dict[str, Any]:
    connector_type = resolve_connector_type(wave_template_id)
    if connector_type != "github":
        raise ConnectorValidationError("WAVE_TEMPLATE_INVALID", "Unsupported connector template.", "connector_supported")
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

    try:
        github_service = __import__(
            "adapters.github_connector.github_demo_service",
            fromlist=["run_governed_case"],
        )
    except Exception as exc:
        return {
            "allowed": False,
            "reason_code": "CONNECTOR_RUNTIME_UNAVAILABLE",
            "message": f"GitHub connector unavailable: {exc}",
            "summary": {},
        }

    connector_case = str(context.get("connector_case", "unauthorized_path"))
    repo = str(context.get("connector_repo", "surfit-demo-repo"))
    base_url = str(context.get("connector_base_url", "http://127.0.0.1:8050"))
    mode = str(context.get("connector_mode", "simulation"))
    linked_proposal_wave_id = str(context.get("linked_proposal_wave_id", "")).strip()
    approver_identity = str(context.get("approver_identity", approved_by)).strip() or approved_by

    case_result = github_service.run_governed_case(
        case_name=connector_case,
        wave_id=wave_id,
        wave_mutation_token=wave_mutation_token,
        github_base_url=base_url,
        actor=approved_by,
        repo=repo,
        mode=mode,
        linked_proposal_wave_id=linked_proposal_wave_id,
        approver_identity=approver_identity,
        proxy_executor=proxy_executor,
    )

    return {
        "allowed": bool(case_result.get("allowed")),
        "reason_code": str(case_result.get("reason_code", "UNKNOWN")),
        "message": str(case_result.get("message", "")),
        "summary": case_result.get("summary") if isinstance(case_result.get("summary"), dict) else {},
        "report_markdown": str(case_result.get("report_markdown", "")),
        "raw": case_result,
    }


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        if not connector.connector_type.strip():
            raise ValueError("connector_type is required")
        if not connector.system_name.strip():
            raise ValueError("system_name is required")
        if not connector.supported_actions:
            raise ValueError("supported_actions must not be empty")
        if connector.connector_type in self._connectors:
            raise ValueError(f"Connector type already registered: {connector.connector_type}")
        self._connectors[connector.connector_type] = connector

    def get(self, connector_type: str) -> BaseConnector | None:
        return self._connectors.get(connector_type)

    def list_types(self) -> list[str]:
        return sorted(self._connectors.keys())


class LegacyGitHubConnector(BaseConnector):
    """
    Bridge adapter so existing GitHub demo connector keeps working while
    product runtime remains connector-agnostic.
    """

    def __init__(self, proxy_executor: Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]):
        self._proxy_executor = proxy_executor

    @property
    def connector_type(self) -> str:
        return "github"

    @property
    def system_name(self) -> str:
        return "github"

    @property
    def supported_actions(self) -> set[str]:
        return {"read", "open_pull_request", "merge_pull_request"}

    def prepare_context(self, context_refs: dict[str, Any]) -> dict[str, Any]:
        return dict(context_refs or {})

    def execute_action(
        self,
        *,
        wave_id: str,
        wave_mutation_token: str,
        context: dict[str, Any],
        approved_by: str,
        policy_manifest_hash: str,
        policy_version: str,
    ) -> ConnectorExecutionResult:
        payload = dispatch_connector_action(
            connector_type="github",
            wave_id=wave_id,
            wave_mutation_token=wave_mutation_token,
            context=context,
            approved_by=approved_by,
            policy_manifest_hash=policy_manifest_hash,
            policy_version=policy_version,
            proxy_executor=self._proxy_executor,
        )
        return ConnectorExecutionResult(
            allowed=bool(payload.get("allowed")),
            reason_code=str(payload.get("reason_code", "UNKNOWN")),
            message=str(payload.get("message", "")),
            payload=payload,
        )


__all__ = [
    "ConnectorRegistry",
    "LegacyGitHubConnector",
    "ConnectorValidationError",
    "resolve_connector_type",
    "prepare_connector_context",
    "dispatch_connector_action",
]
