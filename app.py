import sqlite3, uuid
import streamlit as st
from engine import run_saw
from logger import get_run_logs, get_cycle_time_breakdown, init_db
from models import RunContext

BOARD_METRICS_SPEC = {
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

REVENUE_RECON_SPEC = {
    "saw_id": "revenue_reconciliation_v1",
    "graph": {
        "nodes": [
            {"id": "n_start",        "type": "start"},
            {"id": "n_qb_pull",      "type": "tool_call",     "tool": "tool_quickbooks_read_expenses",  "sensitivity": "medium"},
            {"id": "n_stripe_pull",  "type": "tool_call",     "tool": "tool_stripe_read_payouts",       "sensitivity": "medium"},
            {"id": "n_reconcile",    "type": "tool_call",     "tool": "tool_reconcile_revenue",         "sensitivity": "medium"},
            {"id": "n_gen_report",   "type": "tool_call",     "tool": "tool_generate_revenue_report",   "sensitivity": "medium"},
            {"id": "n_approval",     "type": "approval_gate", "tool": "human_approval",                 "sensitivity": "high"},
            {"id": "n_write_report", "type": "tool_call",     "tool": "tool_write_revenue_report",      "sensitivity": "medium", "write_action": True},
            {"id": "n_end",          "type": "end"},
        ],
        "edges": [
            {"from": "n_start",        "to": "n_qb_pull"},
            {"from": "n_qb_pull",      "to": "n_stripe_pull"},
            {"from": "n_stripe_pull",  "to": "n_reconcile"},
            {"from": "n_reconcile",    "to": "n_gen_report"},
            {"from": "n_gen_report",   "to": "n_approval"},
            {"from": "n_approval",     "to": "n_write_report"},
            {"from": "n_write_report", "to": "n_end"},
        ],
    },
    "policy_bundle": {
        "policy_id": "revenue_recon_policy_v1",
        "sensitivity_level": "medium",
        "tools": {
            "allowlist": ["tool_quickbooks_read_expenses","tool_stripe_read_payouts","tool_reconcile_revenue","tool_generate_revenue_report","tool_write_revenue_report","tool_logger_write"],
            "denylist":  ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"],
        },
        "egress": {"allow_external_http": False, "allowed_domains": [], "allow_email_send": False, "allow_slack_dm": False},
        "write_restrictions": {},
    },
}

SAW_REGISTRY = {
    "Board Metrics Aggregation": BOARD_METRICS_SPEC,
    "Revenue Reconciliation":    REVENUE_RECON_SPEC,
}

SUMMARY_NODE = {
    "Board Metrics Aggregation": "n_generate_summary",
    "Revenue Reconciliation":    "n_gen_report",
}

def load_run_history():
    try:
        import pandas as pd
        conn = sqlite3.connect("surfit_runs.db")
        df = pd.read_sql_query("""
            SELECT run_id, saw_id,
                MAX(CASE WHEN node_id = 'n_end' THEN 'completed' ELSE NULL END) as status,
                ROUND(SUM(CASE WHEN node_id != 'n_approval' THEN latency_ms ELSE 0 END), 2) as system_ms,
                ROUND(MAX(CASE WHEN node_id = 'n_approval' THEN latency_ms ELSE 0 END), 2) as human_wait_ms,
                MIN(timestamp_iso) as started_at
            FROM execution_log
            GROUP BY run_id, saw_id
            ORDER BY started_at DESC
        """, conn)
        df["status"] = df["status"].fillna("denied")
        return df
    except:
        return None

st.set_page_config(page_title="SurFit — SAW Platform", layout="wide")
st.title("SurFit AI — SAW Platform")
st.caption("Semi-Autonomous Workflow demo. No LLM. Fully deterministic.")

tab1, tab2 = st.tabs(["▶ Run SAW", "📋 Run History"])

with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Controls")
        saw_choice = st.selectbox("Select SAW", list(SAW_REGISTRY.keys()))
        approval_granted = st.checkbox("Approve write step", value=True)
        wait_ms = st.slider("Human approval wait (ms)", 0, 3000, 500, step=100)
        run_button = st.button("▶ Run SAW", type="primary", use_container_width=True)

    with col2:
        if run_button:
            spec = SAW_REGISTRY[saw_choice]
            conn = init_db("surfit_runs.db")
            ctx = RunContext(
                run_id=str(uuid.uuid4()),
                saw_id=spec["saw_id"],
                state={"_approval_granted": approval_granted, "_approval_wait_ms": wait_ms},
            )
            with st.spinner("Running SAW..."):
                result = run_saw(spec, ctx, conn)
            status_colour = "green" if result.status == "completed" else "red"
            st.markdown(f"### Status: :{status_colour}[{result.status.upper()}]")
            if result.denial_reason:
                st.warning(f"Denial reason: {result.denial_reason}")
            st.subheader("Cycle-Time Breakdown")
            breakdown = get_cycle_time_breakdown(conn, ctx.run_id)
            b_col1, b_col2, b_col3 = st.columns(3)
            b_col1.metric("System Time", f"{breakdown['system_time_ms']} ms")
            b_col2.metric("Human Wait", f"{breakdown['human_wait_time_ms']} ms")
            b_col3.metric("Total Time", f"{breakdown['total_ms']} ms")
            st.subheader("Execution Log")
            logs = get_run_logs(conn, ctx.run_id)
            if logs:
                import pandas as pd
                df = pd.DataFrame(logs)
                df = df[["timestamp_iso", "node_id", "tool_name", "decision", "latency_ms", "error"]]
                df.columns = ["Timestamp", "Node", "Tool", "Decision", "Latency (ms)", "Error"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            if result.status == "completed":
                summary_node = SUMMARY_NODE[saw_choice]
                summary_data = result.node_results.get(summary_node, {})
                metrics_table = summary_data.get("metrics_table_markdown") if isinstance(summary_data, dict) else None
                commentary = summary_data.get("commentary") if isinstance(summary_data, dict) else None
                if metrics_table or commentary:
                    st.subheader("Output Summary")
                    if metrics_table:
                        st.markdown(metrics_table)
                    if commentary:
                        st.info(commentary)
        else:
            st.info("Select a SAW, set controls, and click Run SAW.")

with tab2:
    st.subheader("All Past Runs")
    history = load_run_history()
    if history is not None and not history.empty:
        import pandas as pd
        history["run_id"] = history["run_id"].str[:8]
        history.columns = ["Run ID", "SAW", "Status", "System (ms)", "Human Wait (ms)", "Started At"]
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("No runs yet. Go to Run SAW tab and click Run SAW.")
