"""
SurFit V1 — SAW Engine (Graph Walker)

Takes a SAW spec dict + RunContext, walks the linear execution graph,
calls policy_check before each tool, handles approval gates, logs
everything, and returns a RunSummary.

V1 constraints:
  - Linear graph only (each node has 0 or 1 outgoing edge).
  - One start node, one end node.
  - Branching raises NotImplementedError.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any

from models import Decision, LogEntry, RunContext, ToolResult
from policy import policy_check, policy_from_spec, INFRA_TOOLS
from tools import TOOL_REGISTRY
from logger import write_log


# ── RunSummary ─────────────────────────────────────────────────────

@dataclass
class RunSummary:
    """Final output of a SAW engine run."""
    run_id: str
    saw_id: str
    status: str                          # "completed" | "denied" | "error"
    system_time_ms: float = 0.0
    human_wait_time_ms: float = 0.0
    total_time_ms: float = 0.0
    node_results: dict[str, Any] = field(default_factory=dict)
    final_outputs: dict[str, Any] = field(default_factory=dict)
    denial_reason: str | None = None


# ── Log helper ─────────────────────────────────────────────────────

def _log_event(
    conn: sqlite3.Connection,
    ctx: RunContext,
    node_id: str,
    decision: str,
    tool_name: str = "",
    latency_ms: float = 0.0,
    error: str | None = None,
) -> None:
    """Write a fully-populated LogEntry. Used for start/end/approval/errors."""
    write_log(conn, LogEntry(
        run_id=ctx.run_id,
        saw_id=ctx.saw_id,
        node_id=node_id,
        tool_name=tool_name,
        decision=decision,
        latency_ms=latency_ms,
        error=error,
    ))


# ── Graph helpers ──────────────────────────────────────────────────

def _build_graph(saw_spec: dict) -> tuple[dict[str, dict], dict[str, str]]:
    """
    Returns:
        node_map:  {node_id: node_dict}
        adjacency: {from_node_id: to_node_id}  (exactly one outgoing edge)

    Raises NotImplementedError if any node has >1 outgoing edge.
    """
    nodes = saw_spec["graph"]["nodes"]
    edges = saw_spec["graph"]["edges"]

    node_map: dict[str, dict] = {n["id"]: n for n in nodes}

    adjacency: dict[str, str] = {}
    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        if src in adjacency:
            raise NotImplementedError(
                f"Node '{src}' has >1 outgoing edge. "
                f"Branching graphs are not supported in V1."
            )
        adjacency[src] = dst

    return node_map, adjacency


def _find_start_node(node_map: dict[str, dict]) -> str:
    """Find the single start node. Raises ValueError if 0 or >1."""
    starts = [nid for nid, n in node_map.items() if n["type"] == "start"]
    if len(starts) != 1:
        raise ValueError(f"Expected exactly 1 start node, found {len(starts)}: {starts}")
    return starts[0]


# ── Default input resolver (Board Metrics golden path) ─────────────

def default_input_resolver(
    node_id: str,
    node: dict,
    ctx: RunContext,
) -> dict:
    """
    Wires upstream node outputs into downstream node inputs.
    Handles both Board Metrics Aggregation and Revenue Reconciliation SAWs.
    """
    # ── Board Metrics Aggregation ──────────────────────────────────
    if node_id == "n_salesforce_pull":
        return {"date_range": "2025-Q1", "segment": "enterprise"}

    if node_id == "n_stripe_pull" and "n_salesforce_pull" in ctx.state:
        return {"date_range": "2025-Q1", "currency": "usd"}

    if node_id == "n_reconcile" and "n_salesforce_pull" in ctx.state:
        return {
            "salesforce": ctx.state.get("n_salesforce_pull", {}),
            "stripe": ctx.state.get("n_stripe_pull", {}),
        }

    if node_id == "n_generate_summary":
        reconcile_data = ctx.state.get("n_reconcile", {})
        return {
            "reconciled_metrics": reconcile_data.get("reconciled_metrics", {}),
            "discrepancies": reconcile_data.get("discrepancies", []),
        }

    if node_id == "n_update_slides":
        summary_data = ctx.state.get("n_generate_summary", {})
        return {
            "template_id": "TEMPLATE_DECK_V1",
            "metrics_table_markdown": summary_data.get("metrics_table_markdown", ""),
            "commentary": summary_data.get("commentary", ""),
        }

    # ── Revenue Reconciliation ─────────────────────────────────────
    if node_id == "n_qb_pull":
        return {"period": "2025-Q1"}

    if node_id == "n_stripe_pull" and "n_qb_pull" in ctx.state:
        return {"period": "2025-Q1"}

    if node_id == "n_reconcile" and "n_qb_pull" in ctx.state:
        return {
            "expenses": ctx.state.get("n_qb_pull", {}),
            "payouts": ctx.state.get("n_stripe_pull", {}),
        }

    if node_id == "n_gen_report":
        return {"reconciled": ctx.state.get("n_reconcile", {})}

    if node_id == "n_write_report":
        return {"report": ctx.state.get("n_gen_report", {})}

    return {}


# ── Approval gate handler ─────────────────────────────────────────

def _handle_approval_gate(
    ctx: RunContext,
    node: dict,
    saw_spec: dict,
) -> tuple[bool, float, str | None]:
    """
    V1 approval gate: requires explicit ctx.state["_approval_granted"] == True.

    If not explicitly set to True, denies immediately with reason.
    No timeout simulation unless ctx.state["_approval_wait_ms"] is set.

    Returns (approved, wait_ms, error_or_none).
    """
    approved = ctx.state.get("_approval_granted") is True
    wait_ms = ctx.state.get("_approval_wait_ms", 0.0)

    if not approved:
        return False, wait_ms, "Approval not provided"

    return True, wait_ms, None


# ── Node executor ──────────────────────────────────────────────────

def _execute_tool_node(
    conn: sqlite3.Connection,
    ctx: RunContext,
    node: dict,
    policy: dict,
) -> tuple[ToolResult, float]:
    """
    Policy check → tool execution → log.

    Returns (ToolResult, latency_ms).
    On policy deny or missing tool, latency_ms is 0.0.
    """
    tool_name = node["tool"]
    node_id = node["id"]
    is_write = node.get("write_action", False)

    # Resolve tool inputs from accumulated state
    tool_inputs = ctx.state.get(f"_inputs_{node_id}", {})

    # ── Policy check (skip infra tools) ───────────────────────────
    if tool_name not in INFRA_TOOLS:
        pd = policy_check(
            tool_name, tool_inputs, ctx,
            is_write=is_write, policy=policy,
        )
        if pd.decision == Decision.DENY:
            error_msg = f"Policy denied: {'; '.join(pd.reasons)}"
            _log_event(
                conn, ctx, node_id,
                decision="deny",
                tool_name=tool_name,
                latency_ms=0.0,
                error=error_msg,
            )
            return (
                ToolResult(tool_name=tool_name, success=False, error=error_msg),
                0.0,
            )

    # ── Resolve tool function ─────────────────────────────────────
    if tool_name not in TOOL_REGISTRY:
        error_msg = f"Tool '{tool_name}' not found in TOOL_REGISTRY"
        _log_event(
            conn, ctx, node_id,
            decision="deny",
            tool_name=tool_name,
            latency_ms=0.0,
            error=error_msg,
        )
        return (
            ToolResult(tool_name=tool_name, success=False, error=error_msg),
            0.0,
        )

    # ── Execute tool ──────────────────────────────────────────────
    t0 = time.perf_counter()
    result = TOOL_REGISTRY[tool_name](tool_inputs, ctx)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # ── Log ───────────────────────────────────────────────────────
    _log_event(
        conn, ctx, node_id,
        decision="allow",
        tool_name=tool_name,
        latency_ms=latency_ms,
        error=result.error,
    )
    return result, latency_ms


# ── Engine ─────────────────────────────────────────────────────────

def run_saw(
    saw_spec: dict,
    ctx: RunContext,
    conn: sqlite3.Connection,
    input_resolver: callable | None = None,
) -> RunSummary:
    """
    Walk the SAW graph linearly, executing each node.

    Args:
        saw_spec:       Parsed SAW spec dict.
        ctx:            RunContext (mutable — accumulates state).
        conn:           SQLite connection for logging.
        input_resolver: Optional callable(node_id, node, ctx) -> dict
                        that returns tool inputs for a given node.
                        If None, uses default_input_resolver (Board Metrics
                        golden path wiring).

    Returns:
        RunSummary with timing, outputs, and status.
    """
    node_map, adjacency = _build_graph(saw_spec)
    policy = policy_from_spec(saw_spec)
    start_id = _find_start_node(node_map)
    resolver = input_resolver if input_resolver is not None else default_input_resolver

    summary = RunSummary(
        run_id=ctx.run_id,
        saw_id=ctx.saw_id,
        status="running",
    )

    current_id = start_id
    last_tool_result: ToolResult | None = None

    while True:
        node = node_map[current_id]
        node_type = node["type"]

        # ── START ─────────────────────────────────────────────────
        if node_type == "start":
            _log_event(conn, ctx, current_id, decision="allow")

        # ── END ───────────────────────────────────────────────────
        elif node_type == "end":
            _log_event(conn, ctx, current_id, decision="allow")
            summary.status = "completed"
            if last_tool_result and last_tool_result.success:
                summary.final_outputs = last_tool_result.data
            break

        # ── APPROVAL GATE ─────────────────────────────────────────
        elif node_type == "approval_gate":
            approved, wait_ms, error = _handle_approval_gate(ctx, node, saw_spec)
            summary.human_wait_time_ms += wait_ms

            _log_event(
                conn, ctx, current_id,
                decision="allow" if approved else "deny",
                latency_ms=wait_ms,
                error=error,
            )

            if not approved:
                summary.status = "denied"
                summary.denial_reason = error or "Approval denied"
                break

        # ── TOOL CALL ─────────────────────────────────────────────
        elif node_type == "tool_call":
            # Resolve inputs via resolver → stash for _execute_tool_node
            ctx.state[f"_inputs_{current_id}"] = resolver(current_id, node, ctx)

            result, latency_ms = _execute_tool_node(conn, ctx, node, policy)
            summary.node_results[current_id] = (
                result.data if result.success else result.error
            )

            if not result.success:
                summary.status = "denied"
                summary.denial_reason = result.error
                break

            # Accumulate outputs + system time
            ctx.state[current_id] = result.data
            last_tool_result = result
            summary.system_time_ms += latency_ms

        else:
            raise ValueError(
                f"Unknown node type '{node_type}' at node '{current_id}'"
            )

        # ── Advance to next node ──────────────────────────────────
        if current_id not in adjacency:
            if node_type != "end":
                summary.status = "error"
                summary.denial_reason = (
                    f"No outgoing edge from node '{current_id}'"
                )
            break
        current_id = adjacency[current_id]

    summary.system_time_ms = round(summary.system_time_ms, 2)
    summary.human_wait_time_ms = round(summary.human_wait_time_ms, 2)
    summary.total_time_ms = round(
        summary.system_time_ms + summary.human_wait_time_ms, 2
    )

    return summary
