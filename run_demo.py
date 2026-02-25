import sqlite3, uuid
from engine import run_saw
from logger import get_run_logs, get_cycle_time_breakdown
from models import RunContext

SAW_SPEC = {
    "saw_id": "board_metrics_v1",
    "graph": {
        "nodes": [
            {"id": "n_start",           "type": "start"},
            {"id": "n_salesforce_pull",  "type": "tool_call",     "tool": "tool_salesforce_read_pipeline", "sensitivity": "medium"},
            {"id": "n_stripe_pull",      "type": "tool_call",     "tool": "tool_stripe_read_revenue",      "sensitivity": "medium"},
            {"id": "n_reconcile",        "type": "tool_call",     "tool": "tool_reconcile_metrics",        "sensitivity": "medium"},
            {"id": "n_generate_summary", "type": "tool_call",     "tool": "tool_generate_board_summary",   "sensitivity": "medium"},
            {"id": "n_approval",         "type": "approval_gate", "tool": "human_approval",                "sensitivity": "high"},
            {"id": "n_update_slides",    "type": "tool_call",     "tool": "tool_slides_update_template",   "sensitivity": "medium", "write_action": True},
            {"id": "n_end",              "type": "end"},
        ],
        "edges": [
            {"from": "n_start",           "to": "n_salesforce_pull"},
            {"from": "n_salesforce_pull",  "to": "n_stripe_pull"},
            {"from": "n_stripe_pull",      "to": "n_reconcile"},
            {"from": "n_reconcile",        "to": "n_generate_summary"},
            {"from": "n_generate_summary", "to": "n_approval"},
            {"from": "n_approval",         "to": "n_update_slides"},
            {"from": "n_update_slides",    "to": "n_end"},
        ],
    },
    "policy_bundle": {
        "policy_id": "board_metrics_policy_v1",
        "sensitivity_level": "medium",
        "tools": {
            "allowlist": ["tool_salesforce_read_pipeline","tool_stripe_read_revenue","tool_reconcile_metrics","tool_generate_board_summary","tool_slides_update_template","tool_logger_write"],
            "denylist":  ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"],
        },
        "egress": {"allow_external_http": False, "allowed_domains": [], "allow_email_send": False, "allow_slack_dm": False},
        "write_restrictions": {"tool_slides_update_template": {"allowed_template_ids": ["TEMPLATE_DECK_V1"], "allow_create_new_decks": False}},
    },
}

def demo_run(approval_granted=True, wait_ms=500):
    from logger import init_db; conn = init_db(":memory:")
    ctx = RunContext(
        run_id=str(uuid.uuid4()),
        saw_id=SAW_SPEC["saw_id"],
        state={"_approval_granted": approval_granted, "_approval_wait_ms": wait_ms},
    )
    result = run_saw(SAW_SPEC, ctx, conn)
    print(f"  Status:          {result.status}")
    print(f"  System time:     {result.system_time_ms} ms")
    print(f"  Human wait time: {result.human_wait_time_ms} ms")
    print(f"  Total time:      {result.total_time_ms} ms")
    if result.denial_reason:
        print(f"  Denial reason:   {result.denial_reason}")
    breakdown = get_cycle_time_breakdown(conn, ctx.run_id)
    print("  Cycle breakdown:", breakdown)
    logs = get_run_logs(conn, ctx.run_id)
    print("  Last 5 logs:")
    for e in logs[-5:]:
        print("   ", e)

print("=== Run 1: Approval Granted ===")
demo_run(True, 500)
print("\n=== Run 2: Approval Denied ===")
demo_run(False, 0)
