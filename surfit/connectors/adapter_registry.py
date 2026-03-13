from __future__ import annotations

from typing import Any, Callable

from connectors.adapter_registry import (
    ConnectorValidationError,
    dispatch_connector_action as legacy_dispatch_connector_action,
    prepare_connector_context as legacy_prepare_connector_context,
)

from .base_connector import BaseConnector, ConnectorExecutionResult


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
    product runtime is connector-agnostic.
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
        return {
            "create_branch",
            "commit_file",
            "open_pull_request",
            "review_commit",
            "merge_pull_request",
            "approval_artifact.create",
        }

    def prepare_context(self, context_refs: dict[str, Any]) -> dict[str, Any]:
        return legacy_prepare_connector_context("github", context_refs)

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
        payload = legacy_dispatch_connector_action(
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


__all__ = ["ConnectorRegistry", "LegacyGitHubConnector", "ConnectorValidationError"]
