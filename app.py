import sqlite3, uuid
import streamlit as st
from engine import run_saw
from logger import get_run_logs, get_cycle_time_breakdown, init_db
from models import RunContext

# ── WAVE SVG ICON ──────────────────────────────────────────────
WAVE_ICON_SVG = """
<svg width="48" height="26" viewBox="0 0 120 68" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M0 16 C22 4, 44 0, 60 6 C76 12, 98 22, 120 10 L120 20 C98 32, 76 22, 60 16 C44 10, 22 14, 0 26 Z" fill="#26c0ff"/>
  <path d="M0 32 C22 20, 44 16, 60 22 C76 28, 98 38, 120 26 L120 36 C98 48, 76 38, 60 32 C44 26, 22 30, 0 42 Z" fill="#26c0ff"/>
  <path d="M0 48 C22 36, 44 32, 60 38 C76 44, 98 54, 120 42 L120 52 C98 64, 76 54, 60 48 C44 42, 22 46, 0 58 Z" fill="#26c0ff"/>
</svg>
"""

WAVE_ICON_SM = """
<svg width="32" height="18" viewBox="0 0 120 68" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M0 16 C22 4, 44 0, 60 6 C76 12, 98 22, 120 10 L120 20 C98 32, 76 22, 60 16 C44 10, 22 14, 0 26 Z" fill="#26c0ff"/>
  <path d="M0 32 C22 20, 44 16, 60 22 C76 28, 98 38, 120 26 L120 36 C98 48, 76 38, 60 32 C44 26, 22 30, 0 42 Z" fill="#26c0ff"/>
  <path d="M0 48 C22 36, 44 32, 60 38 C76 44, 98 54, 120 42 L120 52 C98 64, 76 54, 60 48 C44 42, 22 46, 0 58 Z" fill="#26c0ff"/>
</svg>
"""

# ── CSS ────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Righteous&family=DM+Sans:wght@300;400;500&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0b1220 !important;
    color: #e2eaf5 !important;
}

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── BRANDED HEADER ── */
.sf-header {
    background: #111d30;
    border-bottom: 1px solid #1e3050;
    padding: 16px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
}
.sf-header-left { display: flex; align-items: center; gap: 14px; }
.sf-wordmark {
    font-family: 'Righteous', cursive !important;
    font-size: 22px;
    line-height: 1;
    display: flex;
    align-items: baseline;
    gap: 0;
}
.sf-wordmark .blue   { color: #26c0ff; }
.sf-wordmark .dot    { color: #7a9ab8; font-size: 16px; margin: 0 2px; }
.sf-wordmark .orange { color: #ff731e; }
.sf-platform-tag {
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #7a9ab8;
    margin-top: 3px;
}
.sf-header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 3px;
}
.sf-client-slot {
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7a9ab8;
    opacity: 0.5;
}

/* ── MAIN CONTENT WRAPPER ── */
.sf-main { padding: 0 40px 40px; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e3050 !important;
    gap: 0 !important;
    margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7a9ab8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 12px 24px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #26c0ff !important;
    border-bottom: 2px solid #26c0ff !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── SECTION LABELS ── */
.sf-section-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #7a9ab8;
    margin-bottom: 12px;
}

/* ── CONTROLS PANEL ── */
.sf-controls-panel {
    background: #111d30;
    border: 1px solid #1e3050;
    border-radius: 12px;
    padding: 24px;
}

/* ── SELECT BOX ── */
.stSelectbox label {
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #7a9ab8 !important;
    margin-bottom: 6px !important;
}
.stSelectbox > div > div {
    background: #0b1220 !important;
    border: 1px solid #1e3050 !important;
    border-radius: 8px !important;
    color: #e2eaf5 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #26c0ff !important;
    box-shadow: 0 0 0 2px rgba(38,192,255,0.15) !important;
}

/* ── CHECKBOX ── */
.stCheckbox label {
    color: #e2eaf5 !important;
    font-size: 13px !important;
}
.stCheckbox [data-testid="stCheckbox"] > div {
    border-color: #1e3050 !important;
}

/* ── SLIDER ── */
.stSlider label {
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #7a9ab8 !important;
}
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #26c0ff !important;
}
.stSlider [data-baseweb="slider"] div[data-testid="stSliderTrackFill"] {
    background: #26c0ff !important;
}

/* ── BUTTON ── */
.stButton > button {
    background: #26c0ff !important;
    color: #0b1220 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #4dcdff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(38,192,255,0.3) !important;
}

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
    background: #111d30 !important;
    border: 1px solid #1e3050 !important;
    border-radius: 10px !important;
    padding: 20px !important;
}
[data-testid="metric-container"] label {
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #7a9ab8 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 300 !important;
    font-size: 28px !important;
    color: #26c0ff !important;
}

/* ── STATUS BADGE ── */
.sf-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 20px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 24px;
}
.sf-status-completed {
    background: rgba(38,192,255,0.1);
    color: #26c0ff;
    border: 1px solid rgba(38,192,255,0.3);
}
.sf-status-denied {
    background: rgba(255,115,30,0.1);
    color: #ff731e;
    border: 1px solid rgba(255,115,30,0.3);
}

/* ── DATAFRAME ── */
.stDataFrame {
    border: 1px solid #1e3050 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
.stDataFrame [data-testid="stDataFrameResizable"] {
    background: #111d30 !important;
}

/* ── INFO / WARNING BOXES ── */
.stInfo {
    background: rgba(38,192,255,0.06) !important;
    border: 1px solid rgba(38,192,255,0.2) !important;
    border-radius: 8px !important;
    color: #e2eaf5 !important;
}
.stWarning {
    background: rgba(255,115,30,0.08) !important;
    border: 1px solid rgba(255,115,30,0.25) !important;
    border-radius: 8px !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #26c0ff !important; }

/* ── SUBHEADERS ── */
h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 400 !important;
    color: #e2eaf5 !important;
    letter-spacing: 0.02em !important;
}

/* ── DIVIDER ── */
.sf-divider {
    height: 1px;
    background: #1e3050;
    margin: 24px 0;
}

/* ── RESULTS PANEL ── */
.sf-results-panel {
    background: #111d30;
    border: 1px solid #1e3050;
    border-radius: 12px;
    padding: 24px;
}

/* ── OUTPUT SUMMARY ── */
.sf-output-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #7a9ab8;
    margin-bottom: 16px;
}

/* ── EMPTY STATE ── */
.sf-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 64px 0;
    gap: 12px;
}
.sf-empty-label {
    font-size: 12px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #7a9ab8;
    opacity: 0.5;
}
</style>
"""

# ── SAW SPECS ──────────────────────────────────────────────────
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
        "policy_id": "budget_reforecast_policy_v1",
        "sensitivity_level": "medium",
        "tools": {
            "allowlist": ["tool_pull_actuals","tool_pull_budget","tool_variance_analysis","tool_gen_reforecast","tool_update_plan","tool_logger_write"],
            "denylist":  ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"],
        },
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

# ── HELPERS ────────────────────────────────────────────────────
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

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(page_title="SurFit — SAW Platform", layout="wide", page_icon="〰")

# ── INJECT CSS ─────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

# ── BRANDED HEADER ─────────────────────────────────────────────
st.markdown(f"""
<div class="sf-header">
  <div class="sf-header-left">
    {WAVE_ICON_SVG}
    <div>
      <div class="sf-wordmark">
        <span class="blue">SURFIT</span><span class="dot">.</span><span class="orange">AI</span>
      </div>
      <div class="sf-platform-tag">SAW Platform</div>
    </div>
  </div>
  <div class="sf-header-right">
    <div class="sf-client-slot">Powered by SurFit.AI</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["▶  Run SAW", "  Run History"])

with tab1:
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.markdown('<div class="sf-section-label">Controls</div>', unsafe_allow_html=True)
        with st.container():
            saw_choice = st.selectbox("Select SAW", list(SAW_REGISTRY.keys()))
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            approval_granted = st.checkbox("Approve write step", value=True)
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            wait_ms = st.slider("Human approval wait (ms)", 0, 3000, 500, step=100)
            st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
            run_button = st.button("▶  Run SAW", type="primary", use_container_width=True)

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

            # Status badge
            status_class = "sf-status-completed" if result.status == "completed" else "sf-status-denied"
            status_icon  = "✦" if result.status == "completed" else "✕"
            st.markdown(f"""
                <div class="sf-status {status_class}">
                    {status_icon} &nbsp; {result.status.upper()}
                </div>
            """, unsafe_allow_html=True)

            if result.denial_reason:
                st.warning(f"Denial reason: {result.denial_reason}")

            # Cycle-time metrics
            st.markdown('<div class="sf-section-label">Cycle-Time Breakdown</div>', unsafe_allow_html=True)
            breakdown = get_cycle_time_breakdown(conn, ctx.run_id)
            b1, b2, b3 = st.columns(3)
            b1.metric("System Time",  f"{breakdown['system_time_ms']} ms")
            b2.metric("Human Wait",   f"{breakdown['human_wait_time_ms']} ms")
            b3.metric("Total Time",   f"{breakdown['total_ms']} ms")

            st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

            # Execution log
            st.markdown('<div class="sf-section-label">Execution Log</div>', unsafe_allow_html=True)
            logs = get_run_logs(conn, ctx.run_id)
            if logs:
                import pandas as pd
                df = pd.DataFrame(logs)
                df = df[["timestamp_iso","node_id","tool_name","decision","latency_ms","error"]]
                df.columns = ["Timestamp","Node","Tool","Decision","Latency (ms)","Error"]
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Output summary
            if result.status == "completed":
                summary_node = SUMMARY_NODE[saw_choice]
                summary_data = result.node_results.get(summary_node, {})
                metrics_table = summary_data.get("metrics_table_markdown") if isinstance(summary_data, dict) else None
                commentary    = summary_data.get("commentary") if isinstance(summary_data, dict) else None
                if metrics_table or commentary:
                    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="sf-section-label">Output Summary</div>', unsafe_allow_html=True)
                    if metrics_table:
                        st.markdown(metrics_table)
                    if commentary:
                        st.info(commentary)
        else:
            st.markdown("""
                <div class="sf-empty">
                    <svg width="48" height="26" viewBox="0 0 120 68" fill="none" xmlns="http://www.w3.org/2000/svg" style="opacity:0.15">
                      <path d="M0 16 C22 4, 44 0, 60 6 C76 12, 98 22, 120 10 L120 20 C98 32, 76 22, 60 16 C44 10, 22 14, 0 26 Z" fill="#26c0ff"/>
                      <path d="M0 32 C22 20, 44 16, 60 22 C76 28, 98 38, 120 26 L120 36 C98 48, 76 38, 60 32 C44 26, 22 30, 0 42 Z" fill="#26c0ff"/>
                      <path d="M0 48 C22 36, 44 32, 60 38 C76 44, 98 54, 120 42 L120 52 C98 64, 76 54, 60 48 C44 42, 22 46, 0 58 Z" fill="#26c0ff"/>
                    </svg>
                    <div class="sf-empty-label">Select a SAW and click Run SAW</div>
                </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="sf-section-label">All Past Runs</div>', unsafe_allow_html=True)
    history = load_run_history()
    if history is not None and not history.empty:
        import pandas as pd
        history["run_id"] = history["run_id"].str[:8]
        history.columns = ["Run ID","SAW","Status","System (ms)","Human Wait (ms)","Started At"]
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
            <div class="sf-empty">
                <div class="sf-empty-label">No runs yet — go to Run SAW and fire one off</div>
            </div>
        """, unsafe_allow_html=True)
