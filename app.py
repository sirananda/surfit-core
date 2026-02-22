import sqlite3, uuid
import streamlit as st
from engine import run_saw
from logger import get_run_logs, get_cycle_time_breakdown, init_db
from models import RunContext

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Righteous&family=DM+Sans:wght@300;400;500&display=swap');

html, body { background-color: #0b1220 !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"],
section.main, section.main > div { background-color: #0b1220 !important; }
.main .block-container { background-color: #0b1220 !important; padding: 0 2rem 2rem !important; max-width: 100% !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
#MainMenu, footer { visibility: hidden; }

/* Global text — but NOT inside dataframes */
body, .stMarkdown, .stMarkdown p, .stSelectbox label p,
.stSlider label p, .stCheckbox label p,
[data-testid="stMetricLabel"] p { font-family: 'DM Sans', sans-serif !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1e3050 !important; gap: 0 !important; padding: 0 !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #7a9ab8 !important; font-size: 11px !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; padding: 12px 28px !important; border: none !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; }
.stTabs [aria-selected="true"] { color: #26c0ff !important; border-bottom: 2px solid #26c0ff !important; background: transparent !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 24px 0 0 0 !important; background: transparent !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* SELECT */
.stSelectbox label p { font-size: 10px !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; color: #7a9ab8 !important; }
.stSelectbox > div > div, [data-baseweb="select"] > div { background-color: #111d30 !important; border: 1px solid #1e3050 !important; border-radius: 8px !important; }
[data-baseweb="popover"] { background-color: #111d30 !important; border: 1px solid #1e3050 !important; }
[role="option"] { background-color: #111d30 !important; color: #e2eaf5 !important; }
[role="option"]:hover { background-color: #1e3050 !important; }

/* CHECKBOX */
.stCheckbox label { background: transparent !important; }
.stCheckbox label:hover { background: transparent !important; }
.stCheckbox label p { color: #e2eaf5 !important; font-size: 14px !important; }
[data-baseweb="checkbox"] span[role="checkbox"] { border: 2px solid #ff731e !important; border-radius: 4px !important; background: transparent !important; }
[data-baseweb="checkbox"] span[role="checkbox"][aria-checked="true"] { background-color: #ff731e !important; border-color: #ff731e !important; }

/* SLIDER */
.stSlider label p { font-size: 10px !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; color: #7a9ab8 !important; }
[data-testid="stSliderTrackFill"] { background: #ff731e !important; }
[data-testid="stSliderThumb"] { background: #ff731e !important; border: none !important; }

/* BUTTON */
.stButton > button { background: #26c0ff !important; color: #0b1220 !important; font-weight: 600 !important; font-size: 11px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important; border: none !important; border-radius: 8px !important; padding: 14px 24px !important; }
.stButton > button:hover { box-shadow: 0 4px 24px rgba(255,115,30,0.45) !important; }

/* METRICS */
[data-testid="metric-container"] { background: #111d30 !important; border: 1px solid #1e3050 !important; border-radius: 10px !important; padding: 20px 24px !important; }
[data-testid="stMetricLabel"] p { font-size: 10px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important; color: #7a9ab8 !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div { font-weight: 300 !important; font-size: 26px !important; color: #26c0ff !important; }

/* DATAFRAME — explicit dark background + light text so data is visible */
[data-testid="stDataFrame"] { border: 1px solid #1e3050 !important; border-radius: 10px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] * { color: #e2eaf5 !important; }
[data-testid="stDataFrame"] canvas { background: #111d30 !important; }
.dvn-scroller { background: #111d30 !important; }
[data-testid="stDataFrameResizable"] { background: #111d30 !important; }

/* INFO/WARNING */
[data-testid="stInfoBox"] { background: rgba(38,192,255,0.07) !important; border: 1px solid rgba(38,192,255,0.2) !important; border-radius: 8px !important; }
[data-testid="stWarningBox"] { background: rgba(255,115,30,0.08) !important; border: 1px solid rgba(255,115,30,0.25) !important; border-radius: 8px !important; }
[data-testid="stSpinner"] > div { border-top-color: #ff731e !important; }

.sf-label { font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: #7a9ab8; margin-bottom: 10px; font-family: 'DM Sans', sans-serif; }
.sf-hr { border: none; border-top: 1px solid #1e3050; margin: 20px 0; }
.sf-badge { display:inline-flex; align-items:center; gap:8px; padding:8px 18px; border-radius:6px; font-size:11px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:20px; font-family:'DM Sans',sans-serif; }
.sf-badge-ok  { background:rgba(38,192,255,0.1);  color:#26c0ff; border:1px solid rgba(38,192,255,0.3); }
.sf-badge-err { background:rgba(255,115,30,0.1);  color:#ff731e; border:1px solid rgba(255,115,30,0.3); }
.sf-empty { text-align:center; padding:80px 0; opacity:0.3; }
.sf-empty-text { font-size:11px; letter-spacing:0.18em; text-transform:uppercase; color:#7a9ab8; margin-top:12px; font-family:'DM Sans',sans-serif; }
</style>
"""

WAVE    = '<svg width="48" height="26" viewBox="0 0 120 68" fill="none"><path d="M0 16 C22 4,44 0,60 6 C76 12,98 22,120 10 L120 20 C98 32,76 22,60 16 C44 10,22 14,0 26 Z" fill="#26c0ff"/><path d="M0 32 C22 20,44 16,60 22 C76 28,98 38,120 26 L120 36 C98 48,76 38,60 32 C44 26,22 30,0 42 Z" fill="#26c0ff"/><path d="M0 48 C22 36,44 32,60 38 C76 44,98 54,120 42 L120 52 C98 64,76 54,60 48 C44 42,22 46,0 58 Z" fill="#26c0ff"/></svg>'
WAVE_LG = '<svg width="56" height="30" viewBox="0 0 120 68" fill="none"><path d="M0 16 C22 4,44 0,60 6 C76 12,98 22,120 10 L120 20 C98 32,76 22,60 16 C44 10,22 14,0 26 Z" fill="#26c0ff"/><path d="M0 32 C22 20,44 16,60 22 C76 28,98 38,120 26 L120 36 C98 48,76 38,60 32 C44 26,22 30,0 42 Z" fill="#26c0ff"/><path d="M0 48 C22 36,44 32,60 38 C76 44,98 54,120 42 L120 52 C98 64,76 54,60 48 C44 42,22 46,0 58 Z" fill="#26c0ff"/></svg>'

WORDMARK = (
    '<div style="display:flex;align-items:center;gap:14px;padding:20px 0 12px;">'
    + WAVE +
    '<div>'
    '<div style="font-family:Righteous,cursive;font-size:22px;line-height:1;display:flex;align-items:baseline;">'
    '<span style="color:#26c0ff;font-family:Righteous,cursive;">SURFIT</span>'
    '<span style="color:#7a9ab8;font-family:Righteous,cursive;font-size:15px;margin:0 2px;">.</span>'
    '<span style="color:#ff731e;font-family:Righteous,cursive;">AI</span>'
    '</div>'
    '<div style="font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:#7a9ab8;margin-top:3px;font-family:DM Sans,sans-serif;">SAW Platform</div>'
    '</div></div>'
)

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
        "policy_id": "board_metrics_policy_v1", "sensitivity_level": "medium",
        "tools": {"allowlist": ["tool_salesforce_read_pipeline","tool_stripe_read_revenue","tool_reconcile_metrics","tool_generate_board_summary","tool_slides_update_template","tool_logger_write"], "denylist": ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"]},
        "egress": {"allow_external_http": False, "allowed_domains": [], "allow_email_send": False, "allow_slack_dm": False},
        "write_restrictions": {"tool_slides_update_template": {"allowed_template_ids": ["TEMPLATE_DECK_V1"], "allow_create_new_decks": False}},
    },
}
REVENUE_RECON_SPEC = {
    "saw_id": "revenue_reconciliation_v1",
    "graph": {
        "nodes": [
            {"id": "n_start",          "type": "start"},
            {"id": "n_qb_pull",        "type": "tool_call",     "tool": "tool_quickbooks_read_expenses", "sensitivity": "medium"},
            {"id": "n_stripe_payouts", "type": "tool_call",     "tool": "tool_stripe_read_payouts",      "sensitivity": "medium"},
            {"id": "n_reconcile",      "type": "tool_call",     "tool": "tool_reconcile_revenue",        "sensitivity": "medium"},
            {"id": "n_gen_report",     "type": "tool_call",     "tool": "tool_generate_revenue_report",  "sensitivity": "medium"},
            {"id": "n_approval",       "type": "approval_gate", "tool": "human_approval",                "sensitivity": "high"},
            {"id": "n_write_report",   "type": "tool_call",     "tool": "tool_write_revenue_report",     "sensitivity": "medium", "write_action": True},
            {"id": "n_end",            "type": "end"},
        ],
        "edges": [
            {"from": "n_start",          "to": "n_qb_pull"},
            {"from": "n_qb_pull",        "to": "n_stripe_payouts"},
            {"from": "n_stripe_payouts", "to": "n_reconcile"},
            {"from": "n_reconcile",      "to": "n_gen_report"},
            {"from": "n_gen_report",     "to": "n_approval"},
            {"from": "n_approval",       "to": "n_write_report"},
            {"from": "n_write_report",   "to": "n_end"},
        ],
    },
    "policy_bundle": {
        "policy_id": "revenue_recon_policy_v1", "sensitivity_level": "medium",
        "tools": {"allowlist": ["tool_quickbooks_read_expenses","tool_stripe_read_payouts","tool_reconcile_revenue","tool_generate_revenue_report","tool_write_revenue_report","tool_logger_write"], "denylist": ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"]},
        "egress": {"allow_external_http": False, "allowed_domains": [], "allow_email_send": False, "allow_slack_dm": False},
        "write_restrictions": {},
    },
}
BUDGET_REFORECAST_SPEC = {
    "saw_id": "budget_reforecast_v1",
    "graph": {
        "nodes": [
            {"id": "n_start",          "type": "start"},
            {"id": "n_pull_actuals",   "type": "tool_call",     "tool": "tool_pull_actuals",      "sensitivity": "medium"},
            {"id": "n_pull_budget",    "type": "tool_call",     "tool": "tool_pull_budget",       "sensitivity": "medium"},
            {"id": "n_variance",       "type": "tool_call",     "tool": "tool_variance_analysis", "sensitivity": "medium"},
            {"id": "n_gen_reforecast", "type": "tool_call",     "tool": "tool_gen_reforecast",    "sensitivity": "medium"},
            {"id": "n_approval",       "type": "approval_gate", "tool": "human_approval",         "sensitivity": "high"},
            {"id": "n_update_plan",    "type": "tool_call",     "tool": "tool_update_plan",       "sensitivity": "medium", "write_action": True},
            {"id": "n_end",            "type": "end"},
        ],
        "edges": [
            {"from": "n_start",          "to": "n_pull_actuals"},
            {"from": "n_pull_actuals",   "to": "n_pull_budget"},
            {"from": "n_pull_budget",    "to": "n_variance"},
            {"from": "n_variance",       "to": "n_gen_reforecast"},
            {"from": "n_gen_reforecast", "to": "n_approval"},
            {"from": "n_approval",       "to": "n_update_plan"},
            {"from": "n_update_plan",    "to": "n_end"},
        ],
    },
    "policy_bundle": {
        "policy_id": "budget_reforecast_policy_v1", "sensitivity_level": "medium",
        "tools": {"allowlist": ["tool_pull_actuals","tool_pull_budget","tool_variance_analysis","tool_gen_reforecast","tool_update_plan","tool_logger_write"], "denylist": ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"]},
        "egress": {"allow_external_http": False, "allowed_domains": [], "allow_email_send": False, "allow_slack_dm": False},
        "write_restrictions": {},
    },
}

SAW_REGISTRY = {
    "Board Metrics Aggregation": BOARD_METRICS_SPEC,
    "Revenue Reconciliation":    REVENUE_RECON_SPEC,
    "Budget Reforecast":         BUDGET_REFORECAST_SPEC,
}
SUMMARY_NODE = {
    "Board Metrics Aggregation": "n_generate_summary",
    "Revenue Reconciliation":    "n_gen_report",
    "Budget Reforecast":         "n_gen_reforecast",
}

def load_run_history():
    import pandas as pd
    try:
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
        conn.close()
        df["status"] = df["status"].fillna("denied")
        return df
    except Exception as e:
        return None

# ── PAGE ───────────────────────────────────────────────────────
st.set_page_config(page_title="SurFit — SAW Platform", layout="wide", page_icon="〰")
st.markdown(CSS, unsafe_allow_html=True)

hc1, hc2 = st.columns([3, 1])
with hc1:
    st.markdown(WORDMARK, unsafe_allow_html=True)
with hc2:
    st.markdown('<div style="text-align:right;padding:20px 0 12px;font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:#7a9ab8;opacity:0.5;">Powered by SurFit.AI</div>', unsafe_allow_html=True)
st.markdown('<hr style="border:none;border-top:1px solid #1e3050;margin:0 0 4px;">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["▶  Run SAW", "  Run History"])

with tab1:
    col1, col2 = st.columns([1, 2], gap="large")
    with col1:
        st.markdown('<div class="sf-label">Controls</div>', unsafe_allow_html=True)
        saw_choice       = st.selectbox("Select SAW", list(SAW_REGISTRY.keys()))
        approval_granted = st.checkbox("Approve write step", value=True)
        wait_ms          = st.slider("Human approval wait (ms)", 0, 3000, 500, step=100)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        run_button       = st.button("▶  Run SAW", type="primary", use_container_width=True)

    with col2:
        if run_button:
            import pandas as pd
            spec = SAW_REGISTRY[saw_choice]
            conn = init_db("surfit_runs.db")
            ctx  = RunContext(
                run_id=str(uuid.uuid4()),
                saw_id=spec["saw_id"],
                state={"_approval_granted": approval_granted, "_approval_wait_ms": wait_ms},
            )
            with st.spinner("Running SAW..."):
                result = run_saw(spec, ctx, conn)

            badge_cls  = "sf-badge-ok" if result.status == "completed" else "sf-badge-err"
            badge_icon = "✦" if result.status == "completed" else "✕"
            st.markdown(f'<div class="sf-badge {badge_cls}">{badge_icon}&nbsp;&nbsp;{result.status.upper()}</div>', unsafe_allow_html=True)

            if result.denial_reason:
                st.warning(f"Denial reason: {result.denial_reason}")

            st.markdown('<div class="sf-label">Cycle-Time Breakdown</div>', unsafe_allow_html=True)
            breakdown = get_cycle_time_breakdown(conn, ctx.run_id)
            b1, b2, b3 = st.columns(3)
            b1.metric("System Time", f"{breakdown['system_time_ms']} ms")
            b2.metric("Human Wait",  f"{breakdown['human_wait_time_ms']} ms")
            b3.metric("Total Time",  f"{breakdown['total_ms']} ms")

            st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
            st.markdown('<div class="sf-label">Execution Log</div>', unsafe_allow_html=True)
            logs = get_run_logs(conn, ctx.run_id)
            if logs:
                df_logs = pd.DataFrame(logs)
                df_logs = df_logs[["timestamp_iso","node_id","tool_name","decision","latency_ms","error"]]
                df_logs.columns = ["Timestamp","Node","Tool","Decision","Latency (ms)","Error"]
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.markdown('<p style="color:#7a9ab8;font-size:13px;">No log entries found.</p>', unsafe_allow_html=True)

            if result.status == "completed":
                summary_node  = SUMMARY_NODE[saw_choice]
                summary_data  = result.node_results.get(summary_node, {})
                metrics_table = summary_data.get("metrics_table_markdown") if isinstance(summary_data, dict) else None
                commentary    = summary_data.get("commentary")             if isinstance(summary_data, dict) else None
                if metrics_table or commentary:
                    st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
                    st.markdown('<div class="sf-label">Output Summary</div>', unsafe_allow_html=True)
                    if metrics_table:
                        st.markdown(metrics_table)
                    if commentary:
                        st.info(commentary)
        else:
            st.markdown(f'<div class="sf-empty">{WAVE_LG}<div class="sf-empty-text">Select a SAW and click Run SAW</div></div>', unsafe_allow_html=True)

with tab2:
    import pandas as pd
    st.markdown('<div class="sf-label">All Past Runs</div>', unsafe_allow_html=True)
    history = load_run_history()
    if history is not None and not history.empty:
        display = history.copy()
        display["run_id"] = display["run_id"].str[:8]
        display.columns = ["Run ID","SAW","Status","System (ms)","Human Wait (ms)","Started At"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.markdown(f'<div class="sf-empty">{WAVE_LG}<div class="sf-empty-text">Run a SAW first — history will appear here</div></div>', unsafe_allow_html=True)
