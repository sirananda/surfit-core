import sqlite3, uuid, os, shutil, copy, json, hashlib
from pathlib import Path
import streamlit as st
import logger as logger_mod
from engine import run_saw
from logger import get_run_logs, get_cycle_time_breakdown, init_db, DEFAULT_DB_PATH
from models import RunContext

def get_run_record(conn, run_id: str):
    fn = getattr(logger_mod, "get_run_record", None)
    if callable(fn):
        try:
            return fn(conn, run_id)
        except sqlite3.OperationalError:
            pass

    try:
        cur = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    except sqlite3.OperationalError:
        # Backward-compatible safety: ensure runs table exists, then return no record.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id           TEXT PRIMARY KEY,
                saw_id           TEXT NOT NULL,
                started_at       TEXT NOT NULL,
                status           TEXT NOT NULL,
                policy_hash      TEXT,
                policy_version   TEXT,
                policy_snapshot  TEXT,
                approved_by      TEXT,
                approved_at      TEXT,
                approval_note    TEXT
            )
        """)
        conn.commit()
        return None

    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

def get_llm_invocations(conn, run_id: str):
    fn = getattr(logger_mod, "get_llm_invocations", None)
    if callable(fn):
        try:
            return fn(conn, run_id)
        except Exception:
            pass
    return []


def verify_run_integrity(conn, run_id: str):
    fn = getattr(logger_mod, "verify_run_integrity", None)
    if callable(fn):
        try:
            return fn(conn, run_id)
        except Exception:
            pass
    return {
        "valid": None,
        "first_mismatch_index": None,
        "expected_hash": None,
        "found_hash": None,
    }

# Streamlit Cloud source tree is read-only — use /tmp for writable DB.
_CLOUD_DB = Path("/tmp/surfit_runs.db")
_src = Path(DEFAULT_DB_PATH)
if not _CLOUD_DB.exists() and _src.exists():
    shutil.copy2(str(_src), str(_CLOUD_DB))
DB_PATH = str(_CLOUD_DB)
# Always ensure schema exists at DB_PATH
_init_conn = sqlite3.connect(DB_PATH)
_init_conn.executescript("""
    CREATE TABLE IF NOT EXISTS execution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_iso TEXT NOT NULL,
        run_id TEXT NOT NULL,
        saw_id TEXT NOT NULL,
        node_id TEXT NOT NULL,
        tool_name TEXT DEFAULT '',
        decision TEXT NOT NULL,
        latency_ms REAL DEFAULT 0,
        error TEXT
    );
""")
_init_conn.commit()
_init_conn.close()

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
.stSelectbox > div > div, [data-baseweb="select"] > div { background-color: #111d30 !important; border: 1px solid #1e3050 !important; border-radius: 8px !important; color: #e2eaf5 !important; }
.stSelectbox > div > div *, [data-baseweb="select"] > div * { color: #e2eaf5 !important; }
[data-baseweb="popover"] { background-color: #111d30 !important; border: 1px solid #1e3050 !important; }
[role="option"] { background-color: #111d30 !important; color: #e2eaf5 !important; }
[role="option"]:hover { background-color: #1e3050 !important; color: #e2eaf5 !important; }
[role="option"] * { color: #e2eaf5 !important; }

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
.stButton > button { background: #26c0ff !important; color: #0b1220 !important; font-weight: 600 !important; font-size: 11px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important; border: none !important; border-radius: 8px !important; padding: 14px 24px !important; outline: none !important; box-shadow: none !important; }
.stButton > button:hover { box-shadow: 0 4px 24px rgba(38,192,255,0.35) !important; outline: none !important; }
.stButton > button:focus { outline: none !important; box-shadow: none !important; border: none !important; }
.stButton > button:active { outline: none !important; box-shadow: none !important; border: none !important; }
.stButton > button:focus-visible { outline: none !important; box-shadow: none !important; }

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

/* MARKDOWN TABLES */
.stMarkdown table { color: #e2eaf5 !important; width: 100%; }
.stMarkdown table th { color: #e2eaf5 !important; font-weight: 600; border-bottom: 1px solid #1e3050; }
.stMarkdown table td { color: #e2eaf5 !important; border-bottom: 1px solid #1e3050; padding: 8px 12px; }
.stMarkdown table tr:last-child td { border-bottom: none; }

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
            {"id": "n_generate_summary", "type": "tool_call",     "tool": "tool_generate_summary_llm",   "sensitivity": "medium"},
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
        "tools": {"allowlist": ["tool_salesforce_read_pipeline","tool_stripe_read_revenue","tool_reconcile_metrics","tool_generate_summary_llm","tool_slides_update_template","tool_logger_write"], "denylist": ["tool_browser","tool_shell_exec","tool_external_http","tool_email_send","tool_slack_dm"]},
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
SAW_SPEC_BY_ID = {spec["saw_id"]: spec for spec in SAW_REGISTRY.values()}

SUMMARY_NODE = {
    "Board Metrics Aggregation": "n_generate_summary",
    "Revenue Reconciliation":    "n_gen_report",
    "Budget Reforecast":         "n_gen_reforecast",
}
def policy_fingerprint(spec: dict) -> str:
    pb = spec.get("policy_bundle", {})
    canonical = json.dumps(pb, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
def render_policy_snapshot(spec: dict) -> None:
    pb = spec.get("policy_bundle", {})
    tools = pb.get("tools", {})
    allowlist = tools.get("allowlist", [])
    denylist = tools.get("denylist", [])

    def _rows(items):
        if not items:
            return '<tr><td style="padding:10px 14px;color:#7a9ab8;">—</td></tr>'
        return "".join(
            f'<tr><td style="padding:10px 14px;color:#e2eaf5;border-bottom:1px solid #1a2a40;">{item}</td></tr>'
            for item in items
        )

    allow_table = (
        '<div style="border:1px solid #1e3050;border-radius:10px;overflow:hidden;">'
        '<div style="padding:10px 14px;border-bottom:1px solid #1e3050;color:#26c0ff;font-size:10px;letter-spacing:0.12em;text-transform:uppercase;">Allowlist</div>'
        '<table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:12px;">'
        f'<tbody>{_rows(allowlist)}</tbody>'
        '</table>'
        '</div>'
    )

    deny_table = (
        '<div style="border:1px solid #1e3050;border-radius:10px;overflow:hidden;">'
        '<div style="padding:10px 14px;border-bottom:1px solid #1e3050;color:#ff731e;font-size:10px;letter-spacing:0.12em;text-transform:uppercase;">Denylist</div>'
        '<table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:12px;">'
        f'<tbody>{_rows(denylist)}</tbody>'
        '</table>'
        '</div>'
    )

    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">{allow_table}{deny_table}</div>',
        unsafe_allow_html=True
    )


def _node_status_map(spec: dict, logs: list[dict]) -> dict[str, str]:
    statuses = {n["id"]: "pending" for n in spec["graph"]["nodes"]}
    statuses["n_start"] = "executed"

    for row in logs or []:
        node_id = row.get("node_id", "")
        decision = row.get("decision", "")
        if not node_id:
            continue
        if decision == "deny":
            statuses[node_id] = "blocked"
        elif decision == "allow":
            statuses[node_id] = "executed"

    return statuses


def render_execution_graph(spec: dict, logs: list[dict]) -> None:
    statuses = _node_status_map(spec, logs)
    color_for = {
        "executed": ("#26c0ff", "rgba(38,192,255,0.10)"),
        "blocked": ("#ff731e", "rgba(255,115,30,0.10)"),
        "pending": ("#7a9ab8", "rgba(122,154,184,0.10)"),
    }

    chips = []
    for node in spec["graph"]["nodes"]:
        node_id = node["id"]
        node_type = node.get("type", "")
        state = statuses.get(node_id, "pending")
        fg, bg = color_for[state]
        label = node_id.replace("n_", "").replace("_", " ").title()
        chips.append(
            f'<div style="border:1px solid {fg};background:{bg};border-radius:10px;padding:10px 12px;min-height:72px;">'
            f'<div style="font-size:10px;letter-spacing:0.10em;text-transform:uppercase;color:#7a9ab8;">{node_type}</div>'
            f'<div style="font-size:13px;color:#e2eaf5;margin:4px 0 6px;">{label}</div>'
            f'<div style="font-size:10px;letter-spacing:0.10em;text-transform:uppercase;color:{fg};">{state}</div>'
            f'</div>'
        )

    legend = (
        '<div style="display:flex;gap:14px;align-items:center;margin-bottom:10px;">'
        '<span style="color:#26c0ff;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;">Executed</span>'
        '<span style="color:#ff731e;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;">Blocked</span>'
        '<span style="color:#7a9ab8;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;">Pending</span>'
        '</div>'
    )

    st.markdown(
        f'{legend}<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )

def build_audit_card_text(conn, run_record: dict | None, ctx: RunContext, result, breakdown: dict, logs: list[dict]) -> str:
    snapshot = (run_record or {}).get("policy_snapshot") or "{}"
    pb = json.loads(snapshot)
    tools = pb.get("tools", {})
    allowlist = ", ".join(tools.get("allowlist", []))
    denylist = ", ".join(tools.get("denylist", []))

    db_policy_hash = (run_record or {}).get("policy_hash", "unknown")
    db_policy_version = (run_record or {}).get("policy_version", "unknown")
    db_approved_by = (run_record or {}).get("approved_by") or "unknown"
    db_approved_at = (run_record or {}).get("approved_at") or "unknown"
    db_approval_note = (run_record or {}).get("approval_note") or "none"

    lines = [
        "SURFIT AI - RUN AUDIT CARD",
        "=" * 40,
        f"Run ID: {ctx.run_id}",
        f"SAW ID: {ctx.saw_id}",
        f"Policy Version: {db_policy_version}",
        f"Policy Fingerprint: {db_policy_hash}",
        f"Approved By: {db_approved_by}",
        f"Approved At: {db_approved_at}",
        f"Approval Note: {db_approval_note}",
        f"Status: {result.status}",
        f"Denial reason: {result.denial_reason or 'none'}",
        f"System Time (ms): {breakdown.get('system_time_ms', 0)}",
        f"Human Wait (ms): {breakdown.get('human_wait_time_ms', 0)}",
        f"Total Time (ms): {breakdown.get('total_ms', 0)}",
        "",
        "ALLOWLIST:",
        allowlist or "none",
        "",
        "DENYLIST:",
        denylist or "none",
        "",
        "EXECUTION LOG:",
    ]

    for row in logs or []:
        lines.append(
            f"- {row.get('timestamp_iso','')} | node={row.get('node_id','')} | tool={row.get('tool_name','')} | decision={row.get('decision','')} | latency_ms={row.get('latency_ms',0)} | error={row.get('error','') or '-'}"
        )

    llm_payload = None
    if isinstance(getattr(result, "node_results", None), dict):
        llm_payload = result.node_results.get("n_generate_summary")

    if isinstance(llm_payload, dict):
        llm_meta = llm_payload.get("llm_meta", {})
        raw_tool_input = llm_payload.get("raw_tool_input", {})
        sanitized_prompt_input = llm_payload.get("sanitized_prompt_input", {})
        llm_output_text = llm_payload.get("llm_output_text", "")

        lines.extend([
            "",
            "LLM INVOCATION:",
            f"Provider: {llm_meta.get('provider', 'unknown')}",
            f"Model Name: {llm_meta.get('model_name', 'unknown')}",
            f"Model Version: {llm_meta.get('model_version', 'unknown')}",
            f"Temperature: {llm_meta.get('temperature', 'unknown')}",
            f"Max Tokens: {llm_meta.get('max_tokens', 'unknown')}",
            f"Raw Tool Input: {json.dumps(raw_tool_input, sort_keys=True)}",
            f"Sanitized Prompt Input: {json.dumps(sanitized_prompt_input, sort_keys=True)}",
            f"LLM Output: {llm_output_text}",
        ])
    integrity = verify_run_integrity(conn, ctx.run_id)
    lines.extend([
        "",
        "INTEGRITY CHECK:",
        f"Valid: {integrity.get('valid')}",
        f"First Mismatch Index: {integrity.get('first_mismatch_index')}",
        f"Expected Hash: {integrity.get('expected_hash')}",
        f"Found Hash: {integrity.get('found_hash')}",
    ])

    llm_rows = get_llm_invocations(conn, ctx.run_id)
    if llm_rows:
        lines.append("")
        lines.append("LLM INVOCATION HASHES:")
        for i, r in enumerate(llm_rows, start=1):
            lines.extend([
                f"[{i}] node={r.get('node_id')} invoked_at={r.get('invoked_at')}",
                f"provider={r.get('provider')} model={r.get('model_name')} version={r.get('model_version')}",
                f"raw_tool_input_hash={r.get('raw_tool_input_hash')}",
                f"sanitized_prompt_input_hash={r.get('sanitized_prompt_input_hash')}",
                f"llm_output_text_hash={r.get('llm_output_text_hash')}",
            ])

    return "\n".join(lines)

def load_run_history():
    import pandas as pd
    try:
        conn = sqlite3.connect(DB_PATH)
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
        force_policy_deny = st.checkbox("Force policy deny demo", value=False)

        wait_ms          = st.slider("Human approval wait (ms)", 0, 3000, 500, step=100)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        run_button       = st.button("▶  Run SAW", use_container_width=True)

    with col2:
        if run_button:
            import pandas as pd
            spec = copy.deepcopy(SAW_REGISTRY[saw_choice])

            if force_policy_deny:
                first_tool = next(
                    (n.get("tool") for n in spec["graph"]["nodes"] if n.get("type") == "tool_call" and n.get("tool")),
                    None
                )
                if first_tool:
                    deny = spec["policy_bundle"]["tools"]["denylist"]
                    if first_tool not in deny:
                        deny.append(first_tool)

            conn = init_db(DB_PATH)
            ctx = RunContext(
                run_id=str(uuid.uuid4()),
                saw_id=spec["saw_id"],
                state={
                    "_approval_granted": approval_granted,
                    "_approval_wait_ms": wait_ms,
                    "_approved_by": "demo.manager@surfit.ai",
                    "_approval_note": "Approved in investor demo",
                },
            )
            with st.spinner("Running SAW..."):
                result = run_saw(spec, ctx, conn)

            conn.commit()

            badge_cls  = "sf-badge-ok" if result.status == "completed" else "sf-badge-err"
            badge_icon = "✦" if result.status == "completed" else "✕"
            st.markdown(f'<div class="sf-badge {badge_cls}">{badge_icon}&nbsp;&nbsp;{result.status.upper()}</div>', unsafe_allow_html=True)

            if result.denial_reason:
                st.warning(f"Denial reason: {result.denial_reason}")
            st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
           
            fp = policy_fingerprint(spec)
            st.markdown(f'<div style="font-size:11px;color:#7a9ab8;margin-bottom:10px;">Policy Fingerprint: <span style="color:#26c0ff;">{fp}</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="sf-label">Policy Snapshot</div>', unsafe_allow_html=True)
            render_policy_snapshot(spec)

            st.markdown('<div class="sf-label">Cycle-Time Breakdown</div>', unsafe_allow_html=True)
            breakdown = get_cycle_time_breakdown(conn, ctx.run_id)
            b1, b2, b3 = st.columns(3)
            b1.metric("System Time", f"{breakdown['system_time_ms']} ms")
            b2.metric("Human Wait",  f"{breakdown['human_wait_time_ms']} ms")
            b3.metric("Total Time",  f"{breakdown['total_ms']} ms")
            run_record = get_run_record(conn, ctx.run_id)
            audit_text = build_audit_card_text(conn, run_record, ctx, result, breakdown, get_run_logs(conn, ctx.run_id))
            st.download_button(
                "⬇ Export Audit Card (.txt)",
                data=audit_text,
                file_name=f"audit_{ctx.run_id[:8]}.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
            st.markdown('<div class="sf-label">Execution Log</div>', unsafe_allow_html=True)
            logs = get_run_logs(conn, ctx.run_id)
            st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
            st.markdown('<div class="sf-label">Execution Graph</div>', unsafe_allow_html=True)
            render_execution_graph(spec, logs)

            if logs:
                rows_html = ""
                for row in logs:
                    ts = str(row.get("timestamp_iso",""))[:19].replace("T"," ")
                    node = row.get("node_id","")
                    tool = row.get("tool_name","") or "—"
                    dec = row.get("decision","")
                    lat = f"{row.get('latency_ms',0):.2f}"
                    err = row.get("error","") or "—"
                    dec_color = "#26c0ff" if dec == "allow" else "#ff731e"
                    rows_html += f'<tr><td>{ts}</td><td>{node}</td><td>{tool}</td><td style="color:{dec_color}">{dec}</td><td>{lat}</td><td>{err}</td></tr>'
                st.markdown(f'''<div style="overflow-x:auto;border:1px solid #1e3050;border-radius:10px;">
<table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:12px;">
<thead><tr style="border-bottom:1px solid #1e3050;">
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Timestamp</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Node</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Tool</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Decision</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Latency (ms)</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Error</th>
</tr></thead>
<tbody style="color:#e2eaf5;">{rows_html}</tbody>
</table></div>''', unsafe_allow_html=True)
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
                        # Convert markdown table to styled HTML
                        lines = [l.strip() for l in metrics_table.strip().split("\n") if l.strip() and not l.strip().startswith("|---")]
                        if len(lines) >= 2:
                            headers = [c.strip() for c in lines[0].split("|") if c.strip()]
                            th = "".join(f'<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;border-bottom:1px solid #1e3050;">{h}</th>' for h in headers)
                            body = ""
                            for line in lines[1:]:
                                cells = [c.strip() for c in line.split("|") if c.strip()]
                                body += "<tr>" + "".join(f'<td style="padding:10px 14px;color:#e2eaf5;border-bottom:1px solid #1a2a40;">{c}</td>' for c in cells) + "</tr>"
                            st.markdown(f'<div style="overflow-x:auto;border:1px solid #1e3050;border-radius:10px;margin-bottom:16px;"><table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:13px;"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="color:#e2eaf5;">{metrics_table}</div>', unsafe_allow_html=True)
                    if commentary:
                        st.info(commentary)
        else:
            st.markdown(f'<div class="sf-empty">{WAVE_LG}<div class="sf-empty-text">Select a SAW and click Run SAW</div></div>', unsafe_allow_html=True)

with tab2:
    import pandas as pd
    st.markdown('<div class="sf-label">All Past Runs</div>', unsafe_allow_html=True)
    history = load_run_history()
    drill_run_id = st.text_input("Run ID drill-down", placeholder="Paste full run_id from DB")

    if history is not None and not history.empty:
        history = history.copy()

        # Drill-down FIRST (shows right under input)
        if drill_run_id:
            conn = init_db(DB_PATH)
            run_id_value = drill_run_id.strip()
            selected_logs = get_run_logs(conn, run_id_value)

            # Allow short 8-char prefix from table.
            if not selected_logs and len(run_id_value) == 8:
                row = conn.execute(
                    "SELECT run_id FROM execution_log WHERE run_id LIKE ? ORDER BY timestamp_iso DESC LIMIT 1",
                    (f"{run_id_value}%",)
                ).fetchone()
                if row:
                    run_id_value = row[0]
                    selected_logs = get_run_logs(conn, run_id_value)

            if not selected_logs:
                st.warning("No logs found for that run ID.")
            else:
                saw_id = selected_logs[0].get("saw_id", "")
                spec = SAW_SPEC_BY_ID.get(saw_id)

                st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
                st.markdown(f'<div class="sf-label">Run Drill-Down · {run_id_value[:8]} ({saw_id})</div>', unsafe_allow_html=True)

                if not spec:
                    st.warning(f"SAW spec not found for saw_id: {saw_id}")
                else:
                    st.markdown('<div class="sf-label">Policy Snapshot</div>', unsafe_allow_html=True)
                    render_policy_snapshot(spec)

                    st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
                    st.markdown('<div class="sf-label">Execution Graph</div>', unsafe_allow_html=True)
                    render_execution_graph(spec, selected_logs)

                st.markdown('<hr class="sf-hr">', unsafe_allow_html=True)
                st.markdown('<div class="sf-label">Execution Log (Drill-Down)</div>', unsafe_allow_html=True)

                rows_html_drill = ""
                for row in selected_logs:
                    ts = str(row.get("timestamp_iso", ""))[:19].replace("T", " ")
                    node = row.get("node_id", "")
                    tool = row.get("tool_name", "") or "—"
                    dec = row.get("decision", "")
                    lat = f"{row.get('latency_ms', 0):.2f}"
                    err = row.get("error", "") or "—"
                    dec_color = "#26c0ff" if dec == "allow" else "#ff731e"
                    rows_html_drill += f'<tr><td>{ts}</td><td>{node}</td><td>{tool}</td><td style="color:{dec_color}">{dec}</td><td>{lat}</td><td>{err}</td></tr>'

                st.markdown(
                    '<div style="overflow-x:auto;border:1px solid #1e3050;border-radius:10px;">'
                    '<table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:12px;">'
                    '<thead><tr style="border-bottom:1px solid #1e3050;">'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Timestamp</th>'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Node</th>'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Tool</th>'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Decision</th>'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Latency (ms)</th>'
                    '<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Error</th>'
                    f'</tr></thead><tbody style="color:#e2eaf5;">{rows_html_drill}</tbody></table></div>',
                    unsafe_allow_html=True
                )

        # History table SECOND
        history["run_id"] = history["run_id"].str[:8]
        rows_html_hist = ""
        for _, row in history.iterrows():
            status_color = "#26c0ff" if row["status"] == "completed" else "#ff731e"
            rows_html_hist += f'<tr><td>{row["run_id"]}</td><td>{row["saw_id"]}</td><td style="color:{status_color}">{row["status"]}</td><td>{row["system_ms"]}</td><td>{row["human_wait_ms"]}</td><td>{str(row["started_at"])[:19].replace("T"," ")}</td></tr>'

        st.markdown(f'''<div style="overflow-x:auto;border:1px solid #1e3050;border-radius:10px;">
<table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif;font-size:12px;">
<thead><tr style="border-bottom:1px solid #1e3050;">
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Run ID</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">SAW</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Status</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">System (ms)</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Human Wait (ms)</th>
<th style="padding:10px 14px;text-align:left;color:#7a9ab8;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-size:10px;">Started At</th>
</tr></thead>
<tbody style="color:#e2eaf5;">{rows_html_hist}</tbody>
</table></div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sf-empty">{WAVE_LG}<div class="sf-empty-text">Run a SAW first — history will appear here</div></div>', unsafe_allow_html=True)

