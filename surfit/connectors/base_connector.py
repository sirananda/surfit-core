from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConnectorExecutionResult:
    allowed: bool
    reason_code: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    @property
    @abstractmethod
    def connector_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def system_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_actions(self) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def prepare_context(self, context_refs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    def execute(
        self,
        *,
        wave_id: str,
        wave_mutation_token: str,
        context: dict[str, Any],
        approved_by: str,
        policy_manifest_hash: str,
        policy_version: str,
    ) -> ConnectorExecutionResult:
        return self.execute_action(
            wave_id=wave_id,
            wave_mutation_token=wave_mutation_token,
            context=context,
            approved_by=approved_by,
            policy_manifest_hash=policy_manifest_hash,
            policy_version=policy_version,
        )
