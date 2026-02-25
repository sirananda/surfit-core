"""
SurFit V1 — Core Data Models
RunContext, ToolResult, PolicyDecision, LogEntry
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class NodeType(str, Enum):
    START = "start"
    END = "end"
    TOOL_CALL = "tool_call"
    APPROVAL_GATE = "approval_gate"


@dataclass
class RunContext:
    """Immutable-ish context threaded through every node execution."""
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    saw_id: str = "saw_board_metrics_v1"
    policy_id: str = "policy_board_metrics_v1"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    operator: str = "bizops_analyst"
    approver: str = "bizops_manager"
    # Accumulator for node outputs keyed by node_id
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Standard return envelope from every tool function."""
    tool_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PolicyDecision:
    """Result of a policy_check() call."""
    decision: Decision
    tool_name: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class LogEntry:
    """One row in the execution log."""
    timestamp_iso: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    run_id: str = ""
    saw_id: str = ""
    node_id: str = ""
    tool_name: str = ""
    decision: str = ""  # "allow" | "deny"
    latency_ms: float = 0.0
    error: str | None = None
