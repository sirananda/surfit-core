"""
SurFit V1 — Golden-Path Test
Exercises the full SAW: start → SF pull → Stripe pull → reconcile →
generate summary → approval → slides update → end.

Run:  python -m pytest test_golden_path.py -v
  or: python test_golden_path.py
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from models import Decision, LogEntry, RunContext, ToolResult
from policy import policy_check, INFRA_TOOLS
from tools import TOOL_REGISTRY
from logger import init_db, write_log, get_run_logs, get_cycle_time_breakdown

# Use in-memory DB for tests
DB_PATH = Path(":memory:")


# ── Helpers ────────────────────────────────────────────────────────

def execute_node(
    conn,
    ctx: RunContext,
    node_id: str,
    tool_name: str,
    tool_inputs: dict,
    is_write: bool = False,
) -> ToolResult:
    """Run policy check → execute tool → log result. Returns ToolResult."""

    # Policy check (skip for infra tools)
    if tool_name not in INFRA_TOOLS:
        pd = policy_check(tool_name, tool_inputs, ctx, is_write=is_write)
        if pd.decision == Decision.DENY:
            entry = LogEntry(
                run_id=ctx.run_id,
                saw_id=ctx.saw_id,
                node_id=node_id,
                tool_name=tool_name,
                decision="deny",
                latency_ms=0.0,
                error="; ".join(pd.reasons),
            )
            write_log(conn, entry)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Policy denied: {'; '.join(pd.reasons)}",
            )

    # Execute
    t0 = time.perf_counter()
    tool_fn = TOOL_REGISTRY[tool_name]
    result = tool_fn(tool_inputs, ctx)
    latency = (time.perf_counter() - t0) * 1000

    # Log
    entry = LogEntry(
        run_id=ctx.run_id,
        saw_id=ctx.saw_id,
        node_id=node_id,
        tool_name=tool_name,
        decision="allow",
        latency_ms=round(latency, 2),
        error=result.error,
    )
    write_log(conn, entry)
    return result


def simulate_approval_gate(
    conn, ctx: RunContext, node_id: str, approved: bool, wait_ms: float = 500.0
) -> bool:
    """Simulate sync-blocking approval. In production this blocks on human input."""
    decision = "allow" if approved else "deny"
    entry = LogEntry(
        run_id=ctx.run_id,
        saw_id=ctx.saw_id,
        node_id=node_id,
        tool_name="",
        decision=decision,
        latency_ms=wait_ms,
        error=None if approved else "Approver rejected",
    )
    write_log(conn, entry)
    return approved


# ── Golden-Path Test ──────────────────────────────────────────────

def test_golden_path():
    """Full happy-path execution of Board Metrics Aggregation SAW."""

    # Setup
    import sqlite3
    conn = sqlite3.connect(":memory:")
    from logger import SCHEMA_SQL
    conn.executescript(SCHEMA_SQL)
    conn.commit()

    ctx = RunContext(
        saw_id="saw_board_metrics_v1",
        policy_id="policy_board_metrics_v1",
        operator="alice@example.com",
        approver="bob@example.com",
    )

    # ── n_start (log only) ────────────────────────────────────────
    write_log(conn, LogEntry(
        run_id=ctx.run_id, saw_id=ctx.saw_id,
        node_id="n_start", decision="allow",
    ))

    # ── n_salesforce_pull ─────────────────────────────────────────
    sf_result = execute_node(
        conn, ctx, "n_salesforce_pull",
        "tool_salesforce_read_pipeline",
        {"date_range": "2025-Q1", "segment": "enterprise"},
    )
    assert sf_result.success, f"Salesforce pull failed: {sf_result.error}"
    assert sf_result.data["pipeline_usd"] == 4_250_000.00
    assert sf_result.data["bookings_usd"] == 1_875_000.00
    ctx.state["n_salesforce_pull"] = sf_result.data

    # ── n_stripe_pull ─────────────────────────────────────────────
    stripe_result = execute_node(
        conn, ctx, "n_stripe_pull",
        "tool_stripe_read_revenue",
        {"date_range": "2025-Q1", "currency": "usd"},
    )
    assert stripe_result.success, f"Stripe pull failed: {stripe_result.error}"
    assert stripe_result.data["net_revenue_usd"] == 2_055_000.00
    ctx.state["n_stripe_pull"] = stripe_result.data

    # ── n_reconcile ───────────────────────────────────────────────
    reconcile_result = execute_node(
        conn, ctx, "n_reconcile",
        "tool_reconcile_metrics",
        {
            "salesforce": ctx.state["n_salesforce_pull"],
            "stripe": ctx.state["n_stripe_pull"],
        },
    )
    assert reconcile_result.success
    rec = reconcile_result.data["reconciled_metrics"]
    assert rec["bookings_revenue_delta_usd"] == 1_875_000.00 - 2_055_000.00
    ctx.state["n_reconcile"] = reconcile_result.data

    # ── n_generate_summary ────────────────────────────────────────
    summary_result = execute_node(
        conn, ctx, "n_generate_summary",
        "tool_generate_board_summary",
        {
            "reconciled_metrics": ctx.state["n_reconcile"]["reconciled_metrics"],
            "discrepancies": ctx.state["n_reconcile"]["discrepancies"],
        },
    )
    assert summary_result.success
    assert "Pipeline" in summary_result.data["metrics_table_markdown"]
    ctx.state["n_generate_summary"] = summary_result.data

    # ── n_approval (simulate human approves) ──────────────────────
    approved = simulate_approval_gate(
        conn, ctx, "n_approval", approved=True, wait_ms=1200.0
    )
    assert approved

    # ── n_update_slides ───────────────────────────────────────────
    slides_result = execute_node(
        conn, ctx, "n_update_slides",
        "tool_slides_update_template",
        {
            "template_id": "TEMPLATE_DECK_V1",
            "metrics_table_markdown": ctx.state["n_generate_summary"]["metrics_table_markdown"],
            "commentary": ctx.state["n_generate_summary"]["commentary"],
        },
        is_write=True,
    )
    assert slides_result.success, f"Slides update failed: {slides_result.error}"
    assert slides_result.data["status"] == "updated"

    # ── n_end (log only) ──────────────────────────────────────────
    write_log(conn, LogEntry(
        run_id=ctx.run_id, saw_id=ctx.saw_id,
        node_id="n_end", decision="allow",
    ))

    # ── Verify logs ───────────────────────────────────────────────
    logs = get_run_logs(conn, ctx.run_id)
    node_ids_logged = [row["node_id"] for row in logs]
    expected_nodes = [
        "n_start",
        "n_salesforce_pull",
        "n_stripe_pull",
        "n_reconcile",
        "n_generate_summary",
        "n_approval",
        "n_update_slides",
        "n_end",
    ]
    assert node_ids_logged == expected_nodes, f"Log order: {node_ids_logged}"

    # All decisions should be 'allow'
    for row in logs:
        assert row["decision"] == "allow", f"Unexpected deny at {row['node_id']}"

    # ── Verify cycle-time breakdown ───────────────────────────────
    ct = get_cycle_time_breakdown(conn, ctx.run_id)
    assert ct["human_wait_time_ms"] == 1200.0  # our simulated approval time
    assert ct["system_time_ms"] > 0
    assert ct["total_ms"] == ct["system_time_ms"] + ct["human_wait_time_ms"]

    print("\n✅ Golden-path test PASSED")
    print(f"   Run ID:           {ctx.run_id}")
    print(f"   Nodes executed:   {len(logs)}")
    print(f"   System time:      {ct['system_time_ms']:.1f} ms")
    print(f"   Human wait time:  {ct['human_wait_time_ms']:.1f} ms")
    print(f"   Total time:       {ct['total_ms']:.1f} ms")

    conn.close()


# ── Policy-Deny Tests ─────────────────────────────────────────────

def test_policy_denies_unlisted_tool():
    """A tool not on the allowlist must be denied."""
    ctx = RunContext()
    pd = policy_check("tool_browser", {}, ctx)
    assert pd.decision == Decision.DENY
    assert "denylist" in pd.reasons[0].lower()


def test_policy_denies_wrong_template_id():
    """Write to a non-allowed template ID must be denied."""
    ctx = RunContext()
    pd = policy_check(
        "tool_slides_update_template",
        {"template_id": "ROGUE_TEMPLATE"},
        ctx,
        is_write=True,
    )
    assert pd.decision == Decision.DENY
    assert "ROGUE_TEMPLATE" in pd.reasons[0]


def test_policy_denies_unknown_tool():
    """A completely unknown tool must be denied (not on allowlist)."""
    ctx = RunContext()
    pd = policy_check("tool_something_random", {}, ctx)
    assert pd.decision == Decision.DENY
    assert "allowlist" in pd.reasons[0].lower()


def test_policy_allows_valid_write():
    """A write with the correct template ID must be allowed."""
    ctx = RunContext()
    pd = policy_check(
        "tool_slides_update_template",
        {"template_id": "TEMPLATE_DECK_V1"},
        ctx,
        is_write=True,
    )
    assert pd.decision == Decision.ALLOW


# ── Run directly ──────────────────────────────────────────────────

if __name__ == "__main__":
    test_golden_path()
    test_policy_denies_unlisted_tool()
    test_policy_denies_wrong_template_id()
    test_policy_denies_unknown_tool()
    test_policy_allows_valid_write()
    print("✅ All tests PASSED")
import unittest

class TestGoldenPath(unittest.TestCase):
    def test_golden_path_loads(self):
        """Minimal test to confirm the file imports and basic structure."""
        self.assertTrue(True)  # Dummy pass - replace with real test later

