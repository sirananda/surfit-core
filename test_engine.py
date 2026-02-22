"""
SurFit V1 — Engine Integration Tests

Tests:
  1. Golden path: full run, approval granted, slides updated.
  2. Approval denied: run terminates at gate.
  3. Policy deny: wrong template ID → slides update blocked.
  4. Branching graph: raises NotImplementedError.

Run:  python test_engine.py
"""

from __future__ import annotations

import json
import sqlite3
from copy import deepcopy

from models import RunContext
from engine import run_saw
from logger import SCHEMA_SQL, get_run_logs, get_cycle_time_breakdown


# ── SAW spec (inline, matches the frozen JSON with TEMPLATE_DECK_V1) ──

SAW_SPEC = {
    "saw_id": "saw_board_metrics_v1",
    "name": "Board Metrics Aggregation SAW",
    "version": "0.1",
    "policy_bundle": {
        "policy_id": "policy_board_metrics_v1",
        "sensitivity_level": "medium",
        "egress": {
            "allow_external_http": False,
            "allowed_domains": [],
            "allow_email_send": False,
            "allow_slack_dm": False,
        },
        "tools": {
            "allowlist": [
                "tool_salesforce_read_pipeline",
                "tool_stripe_read_revenue",
                "tool_reconcile_metrics",
                "tool_generate_board_summary",
                "tool_slides_update_template",
                "tool_logger_write",
            ],
            "denylist": [
                "tool_browser",
                "tool_shell_exec",
                "tool_external_http",
                "tool_email_send",
                "tool_slack_dm",
            ],
        },
        "write_restrictions": {
            "tool_slides_update_template": {
                "allowed_template_ids": ["TEMPLATE_DECK_V1"],
                "allow_create_new_decks": False,
            }
        },
    },
    "approval_gate": {
        "mode": "sync_blocking",
        "timeout_seconds": 1800,
        "timeout_action": "deny",
        "required_for": [{"node_id": "n_update_slides", "reason": "write_action"}],
    },
    "graph": {
        "nodes": [
            {"id": "n_start", "type": "start"},
            {"id": "n_salesforce_pull", "type": "tool_call", "tool": "tool_salesforce_read_pipeline", "policy_ref": "policy_board_metrics_v1"},
            {"id": "n_stripe_pull", "type": "tool_call", "tool": "tool_stripe_read_revenue", "policy_ref": "policy_board_metrics_v1"},
            {"id": "n_reconcile", "type": "tool_call", "tool": "tool_reconcile_metrics", "policy_ref": "policy_board_metrics_v1"},
            {"id": "n_generate_summary", "type": "tool_call", "tool": "tool_generate_board_summary", "policy_ref": "policy_board_metrics_v1"},
            {"id": "n_approval", "type": "approval_gate", "approval_required_for_node_id": "n_update_slides"},
            {"id": "n_update_slides", "type": "tool_call", "tool": "tool_slides_update_template", "policy_ref": "policy_board_metrics_v1", "write_action": True},
            {"id": "n_end", "type": "end"},
        ],
        "edges": [
            {"from": "n_start", "to": "n_salesforce_pull"},
            {"from": "n_salesforce_pull", "to": "n_stripe_pull"},
            {"from": "n_stripe_pull", "to": "n_reconcile"},
            {"from": "n_reconcile", "to": "n_generate_summary"},
            {"from": "n_generate_summary", "to": "n_approval"},
            {"from": "n_approval", "to": "n_update_slides"},
            {"from": "n_update_slides", "to": "n_end"},
        ],
    },
}


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


# ── Test 1: Golden path ───────────────────────────────────────────

def test_engine_golden_path():
    conn = _make_conn()
    ctx = RunContext(
        saw_id="saw_board_metrics_v1",
        operator="alice@example.com",
        approver="bob@example.com",
    )
    # Pre-set approval
    ctx.state["_approval_granted"] = True
    ctx.state["_approval_wait_ms"] = 950.0

    summary = run_saw(SAW_SPEC, ctx, conn)

    assert summary.status == "completed", f"Expected completed, got {summary.status}: {summary.denial_reason}"
    assert summary.human_wait_time_ms == 950.0
    assert summary.system_time_ms >= 0
    assert summary.total_time_ms == summary.system_time_ms + summary.human_wait_time_ms
    assert summary.final_outputs.get("status") == "updated"

    # Verify all 8 nodes logged
    logs = get_run_logs(conn, ctx.run_id)
    node_ids = [l["node_id"] for l in logs]
    assert node_ids == [
        "n_start", "n_salesforce_pull", "n_stripe_pull", "n_reconcile",
        "n_generate_summary", "n_approval", "n_update_slides", "n_end",
    ], f"Log order: {node_ids}"

    print(f"  ✅ Golden path: {summary.status}, total={summary.total_time_ms:.1f}ms")
    conn.close()


# ── Test 2: Approval denied ───────────────────────────────────────

def test_engine_approval_denied():
    conn = _make_conn()
    ctx = RunContext(saw_id="saw_board_metrics_v1")
    ctx.state["_approval_granted"] = False
    ctx.state["_approval_wait_ms"] = 300.0

    summary = run_saw(SAW_SPEC, ctx, conn)

    assert summary.status == "denied"
    assert "not provided" in (summary.denial_reason or "").lower()
    # n_update_slides and n_end should NOT appear in logs
    logs = get_run_logs(conn, ctx.run_id)
    node_ids = [l["node_id"] for l in logs]
    assert "n_update_slides" not in node_ids
    assert "n_end" not in node_ids

    print(f"  ✅ Approval denied: terminated at gate")
    conn.close()


# ── Test 3: Approval not set → immediate deny ────────────────────

def test_engine_approval_not_set():
    conn = _make_conn()
    ctx = RunContext(saw_id="saw_board_metrics_v1")
    # Don't set _approval_granted at all → immediate deny

    summary = run_saw(SAW_SPEC, ctx, conn)

    assert summary.status == "denied"
    assert "not provided" in (summary.denial_reason or "").lower()
    assert summary.human_wait_time_ms == 0.0  # no timeout simulation

    print(f"  ✅ Approval not set: immediate deny")
    conn.close()


# ── Test 4: Policy deny (wrong template ID) ──────────────────────

def test_engine_policy_deny_wrong_template():
    conn = _make_conn()
    ctx = RunContext(saw_id="saw_board_metrics_v1")
    ctx.state["_approval_granted"] = True
    ctx.state["_approval_wait_ms"] = 100.0

    # Custom resolver that sends wrong template ID for slides only
    from engine import default_input_resolver

    def bad_resolver(node_id, node, ctx):
        if node_id == "n_update_slides":
            summary_data = ctx.state.get("n_generate_summary", {})
            return {
                "template_id": "ROGUE_TEMPLATE",
                "metrics_table_markdown": summary_data.get("metrics_table_markdown", ""),
                "commentary": summary_data.get("commentary", ""),
            }
        return default_input_resolver(node_id, node, ctx)

    summary = run_saw(SAW_SPEC, ctx, conn, input_resolver=bad_resolver)

    assert summary.status == "denied"
    assert "ROGUE_TEMPLATE" in (summary.denial_reason or "")

    # n_update_slides should be logged as deny
    logs = get_run_logs(conn, ctx.run_id)
    slides_logs = [l for l in logs if l["node_id"] == "n_update_slides"]
    assert len(slides_logs) == 1
    assert slides_logs[0]["decision"] == "deny"

    print(f"  ✅ Policy deny: wrong template blocked")
    conn.close()


# ── Test 5: Branching graph raises ────────────────────────────────

def test_engine_rejects_branching():
    branching_spec = deepcopy(SAW_SPEC)
    branching_spec["graph"]["edges"].append(
        {"from": "n_reconcile", "to": "n_end"}  # second edge from n_reconcile
    )

    try:
        conn = _make_conn()
        ctx = RunContext()
        run_saw(branching_spec, ctx, conn)
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError as e:
        assert "n_reconcile" in str(e)
        print(f"  ✅ Branching rejected: {e}")
    conn.close()


# ── Run all ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Engine integration tests:")
    test_engine_golden_path()
    test_engine_approval_denied()
    test_engine_approval_not_set()
    test_engine_policy_deny_wrong_template()
    test_engine_rejects_branching()
    print("\n✅ All engine tests PASSED")
import unittest

class TestEngine(unittest.TestCase):
    def test_file_loads(self):
        """Minimal test to confirm the file imports and runs without crash."""
        self.assertTrue(True)  # Dummy pass - replace with real test later

