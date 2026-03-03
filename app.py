import json
import re
import sqlite3
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from agents.production_config_agent import run_scenario as run_production_config_scenario


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / 'outputs'
API_BASE = 'http://127.0.0.1:8010'
PROD_CONFIG_PATH = PROJECT_ROOT / 'demo_artifacts' / 'prod_config.json'
PROD_CONFIG_BASELINE_PATH = PROJECT_ROOT / 'demo_artifacts' / 'prod_config.baseline.json'
PROD_AGENT_SCENARIOS = [
    'Unauthorized agent',
    'Path violation',
    'Policy mismatch',
    'Allowed execution',
]


def db_candidates() -> list[Path]:
    env_path = os.environ.get('SURFIT_DB_PATH')
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(PROJECT_ROOT / 'surfit_runs.db')
    candidates.append(Path('/tmp/surfit_runs.db'))
    return candidates

FINANCE_PAYLOAD = {
    'agent_id': 'openclaw_poc_agent_v1',
    'wave_template_id': 'sales_report_v1',
    'policy_version': 'sales_report_policy_v1',
    'intent': 'Scheduled demo trigger: generate weekly sales report with executive summary',
    'context_refs': {
        'input_csv_path': './data/sales.csv',
        'output_report_path': './outputs/report.md',
    },
}

MARKET_INTEL_PAYLOAD = {
    'agent_id': 'openclaw_market_intelligence_agent_v1',
    'wave_template_id': 'market_intelligence_digest_v1',
    'policy_version': 'market_intelligence_digest_policy_v1',
    'intent': 'Scheduled demo trigger: produce next-day market intelligence with top narratives, ranked content angles, and recommended focus for tomorrow',
    'context_refs': {
        'sources': [
            'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
            'https://feeds.hbr.org/harvardbusiness',
            'https://techcrunch.com/feed/',
        ],
        'snapshot_dir': './data/marketing_snapshots',
        'output_digest_path': './outputs/market_intelligence_digest.md',
    },
}

PROD_AGENT_WAVE_PAYLOAD = {
    'agent_id': 'production_config_agent',
    'wave_template_id': 'production_config_change_v1',
    'policy_version': 'prod_config_policy_v1',
    'intent': 'Scheduled demo trigger: provision production config mutation wave token',
    'context_refs': {
        'target_path': 'demo_artifacts/prod_config.json',
    },
}

UNAUTHORIZED_AGENT_PAYLOAD = {
    'agent_id': 'rogue_agent_v0',
    'wave_template_id': 'sales_report_v1',
    'policy_version': 'sales_report_policy_v1',
    'intent': 'Boundary break test: unauthorized agent',
    'context_refs': {
        'input_csv_path': './data/sales.csv',
        'output_report_path': './outputs/report.md',
    },
}

PATH_VIOLATION_PAYLOAD = {
    'agent_id': 'openclaw_poc_agent_v1',
    'wave_template_id': 'sales_report_v1',
    'policy_version': 'sales_report_policy_v1',
    'intent': 'Boundary break test: path violation',
    'context_refs': {
        'input_csv_path': '/tmp/outside.csv',
        'output_report_path': './outputs/report.md',
    },
}

POLICY_MISMATCH_PAYLOAD = {
    'agent_id': 'openclaw_poc_agent_v1',
    'wave_template_id': 'sales_report_v1',
    'policy_version': 'sales_report_policy_INVALID',
    'intent': 'Boundary break test: policy mismatch',
    'context_refs': {
        'input_csv_path': './data/sales.csv',
        'output_report_path': './outputs/report.md',
    },
}


ATLAS_ENTRIES = {
    'production_config_change_v1': {
        'title': 'Production config mutation wave',
        'agent_script': PROJECT_ROOT / 'agents' / 'production_config_agent.py',
        'wave_script': {
            'agent_id': 'production_config_agent',
            'wave_template_id': 'production_config_change_v1',
            'policy_version': 'prod_config_policy_v1',
            'intent': 'Demo trigger: production config mutation governance proof',
            'context_refs': {'target_path': 'demo_artifacts/prod_config.json'},
        },
    },
    'sales_report_v1': {
        'title': 'Finance reporting wave',
        'agent_script': PROJECT_ROOT / 'agents' / 'finance-agent.js',
        'wave_script': FINANCE_PAYLOAD,
    },
    'market_intelligence_digest_v1': {
        'title': 'Market intelligence wave',
        'agent_script': PROJECT_ROOT / 'agents' / 'marketing-agent.js',
        'wave_script': MARKET_INTEL_PAYLOAD,
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Righteous&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --blue: #26c0ff;
  --orange: #ff731e;
  --dark: #0b1220;
  --surface: #111d30;
  --border: #1e3050;
  --text: #e2eaf5;
  --muted: #7a9ab8;
}

html, body { background: var(--dark) !important; color: var(--text) !important; }
.stApp { background: radial-gradient(ellipse at top, rgba(38,192,255,0.07) 0%, transparent 45%), var(--dark) !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
#MainMenu, footer { visibility: hidden; }
.main .block-container { max-width: 1180px !important; padding-top: 18px !important; padding-bottom: 36px !important; }

.sf-wordmark { display:flex; align-items:center; gap:14px; margin-top:8px; }
.sf-title { font-family:'Righteous', cursive; font-size:40px; line-height:1; letter-spacing:0.01em; }
.sf-title .s { color:var(--blue); }
.sf-title .d { color:var(--muted); font-size:26px; margin:0 3px; }
.sf-title .a { color:var(--orange); }
.sf-sub { font-size:11px; letter-spacing:0.18em; text-transform:uppercase; color:var(--muted); margin-top:4px; }

.sf-glass {
  background: linear-gradient(180deg, rgba(17,29,48,0.92), rgba(11,18,32,0.95));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 20px;
}

.sf-kicker { font-size:11px; color:var(--muted); letter-spacing:.16em; text-transform:uppercase; }
.sf-chip { display:inline-block; padding:5px 10px; border-radius:999px; font-size:11px; letter-spacing:0.08em; text-transform:uppercase; }
.sf-chip-ok { color:var(--blue); background:rgba(38,192,255,0.12); border:1px solid rgba(38,192,255,0.28); }
.sf-chip-warn { color:var(--orange); background:rgba(255,115,30,0.12); border:1px solid rgba(255,115,30,0.28); }

.sf-metrics { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 12px 0 18px; }
.sf-metric { background: var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 16px; }
.sf-metric .k { font-size:10px; color:var(--muted); letter-spacing:0.16em; text-transform:uppercase; }
.sf-metric .v { font-size:26px; color:var(--blue); font-weight:300; margin-top:6px; }
.sf-metric .d { font-size:12px; color:var(--muted); margin-top:4px; }

.stTabs [data-baseweb="tab-list"] { border-bottom:1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-size: 11px !important; letter-spacing: 0.13em !important; text-transform: uppercase !important; }
.stTabs [aria-selected="true"] { color: var(--blue) !important; }

[data-testid="stTextInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}
[data-testid="stTextInput"] label p {
  color: #c7ddf2 !important;
  opacity: 1 !important;
  font-size: 12px !important;
}
[data-testid="stTextInput"] input::placeholder {
  color: #9fc0de !important;
  opacity: 1 !important;
}

[data-testid="stDataFrame"] { border:1px solid var(--border) !important; border-radius:10px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] canvas { background: var(--surface) !important; }
[data-testid="stDataFrame"] * { color: var(--text) !important; }
.stMarkdown a, .stMarkdown a:visited { color: var(--blue) !important; text-decoration: underline !important; }

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown p, .stMarkdown li { color: var(--text) !important; }
.stMarkdown code { background: var(--surface) !important; color: var(--blue) !important; }

@media (max-width: 960px) {
  .sf-metrics { grid-template-columns: 1fr 1fr; }
  .sf-title { font-size:32px; }
}
@media (max-width: 640px) {
  .sf-metrics { grid-template-columns: 1fr; }
}
</style>
"""

WAVE_ICON = '<svg width="38" height="22" viewBox="0 0 120 68" fill="none"><path d="M0 16 C22 4,44 0,60 6 C76 12,98 22,120 10 L120 20 C98 32,76 22,60 16 C44 10,22 14,0 26 Z" fill="#26c0ff"/><path d="M0 32 C22 20,44 16,60 22 C76 28,98 38,120 26 L120 36 C98 48,76 38,60 32 C44 26,22 30,0 42 Z" fill="#26c0ff"/><path d="M0 48 C22 36,44 32,60 38 C76 44,98 54,120 42 L120 52 C98 64,76 54,60 48 C44 42,22 46,0 58 Z" fill="#26c0ff"/></svg>'


def find_db_path() -> Path | None:
    # Prefer a DB that already has a `waves` table so the UI never binds to a thin/partial file.
    for p in db_candidates():
        if not p.exists():
            continue
        try:
            conn = sqlite3.connect(str(p))
            try:
                row = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='waves'"
                ).fetchone()
                if row is not None:
                    return p
            finally:
                conn.close()
        except Exception:
            continue

    # Fallback: first existing DB path if no `waves` table found.
    for p in db_candidates():
        if p.exists():
            return p
    return None


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [r[0] for r in rows]


def has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return row is not None


def wave_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute('PRAGMA table_info(waves)').fetchall()
    return {r[1] for r in rows}


def pick_order_column(cols: set[str]) -> str:
    for col in ('completed_at', 'updated_at', 'started_at', 'created_at'):
        if col in cols:
            return col
    return 'rowid'


def fetch_waves(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    order_col = pick_order_column(wave_columns(conn))
    return conn.execute(f'SELECT * FROM waves ORDER BY {order_col} DESC').fetchall()


def safe_json_loads(value: str | None) -> dict:
    if not value:
        return {}
    try:
        out = json.loads(value)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return None


def resolve_output_path(row: sqlite3.Row) -> str | None:
    d = dict(row)
    if d.get('output_path'):
        return str(d['output_path'])
    refs = safe_json_loads(d.get('context_refs_json'))
    for key in ('output_report_path', 'output_digest_path', 'output_brief_path', 'output_path'):
        if refs.get(key):
            return str(refs[key])
    return None


def resolve_policy_hash(row: sqlite3.Row) -> str:
    d = dict(row)
    return str(d.get('policy_hash') or d.get('policy_version') or 'N/A')


def resolve_integrity(row: sqlite3.Row) -> str:
    d = dict(row)
    if d.get('integrity_status'):
        return str(d['integrity_status'])
    status = str(d.get('status') or '').lower()
    if status == 'complete':
        return 'VALID'
    if status == 'failed':
        return 'FLAGGED'
    return 'UNKNOWN'


def load_output_text(output_path: str | None) -> tuple[str | None, str | None]:
    if not output_path:
        return None, None
    p = Path(output_path)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    if not p.exists():
        alt = (OUTPUT_DIR / p.name).resolve()
        if alt.exists():
            p = alt
        else:
            return None, None
    return str(p), p.read_text(encoding='utf-8', errors='replace')


def display_path(output_path: str | None, resolved_output_path: str | None) -> str:
    if output_path:
        return output_path
    if not resolved_output_path:
        return 'N/A'
    p = Path(resolved_output_path)
    try:
        rel = p.resolve().relative_to(PROJECT_ROOT.resolve())
        return f'./{rel.as_posix()}'
    except Exception:
        return p.name


def extract_section(markdown_text: str, heading: str) -> str | None:
    esc = re.escape(heading)
    pattern = rf'^## {esc}\s*\n(.*?)(?=^##\s+|\Z)'
    match = re.search(pattern, markdown_text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def remove_section(markdown_text: str, heading: str) -> str:
    esc = re.escape(heading)
    pattern = rf'^## {esc}\s*\n.*?(?=^##\s+|\Z)'
    return re.sub(pattern, '', markdown_text, flags=re.MULTILINE | re.DOTALL)


def de_duplicate_rendered_output(markdown_text: str) -> str:
    text = markdown_text
    text = remove_section(text, 'LLM Summary')
    text = remove_section(text, 'AI Digest')
    text = remove_section(text, 'Deterministic Metrics Summary')
    text = remove_section(text, 'Revenue by Region')
    text = remove_section(text, 'Sources')
    # Top title + generated/run metadata already shown in Wave Output Snapshot.
    text = re.sub(r'(?m)^#\s+.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Generated at:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Run ID:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Sources fetched:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Topic:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Scope:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Top N:\s*.+\n?', '', text, count=1)
    text = re.sub(r'(?m)^Generated at:\s*.+\s+Run ID:\s*.+\s+Sources fetched:\s*.+\n?', '', text, count=1)
    # Normalize extra blank lines after section removal.
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def parse_total_revenue(markdown_text: str) -> float | None:
    m = re.search(r'Total revenue \(USD\): \$([0-9,]+(?:\.[0-9]{2})?)', markdown_text)
    if not m:
        return None
    return float(m.group(1).replace(',', ''))


def extract_report_header(markdown_text: str) -> tuple[str | None, str | None]:
    title_match = re.search(r'(?m)^#\s+(.+)$', markdown_text)
    generated_match = re.search(r'(?m)^Generated at:\s*(.+)$', markdown_text)
    title = title_match.group(1).strip() if title_match else None
    generated = generated_match.group(1).strip() if generated_match else None
    return title, generated


def render_output_snapshot(output_text: str | None) -> None:
    if not output_text:
        return

    title, generated = extract_report_header(output_text)
    deterministic = extract_section(output_text, 'Deterministic Metrics Summary')
    sources = extract_section(output_text, 'Sources')
    revenue_by_region = extract_section(output_text, 'Revenue by Region')

    st.markdown('### Wave Output Snapshot')
    if title:
        st.markdown(f'**{title}**')
    if generated:
        st.markdown(f'Generated at: `{generated}`')

    if deterministic:
        st.markdown('**Deterministic Metrics Summary**')
        st.markdown(deterministic)

    if revenue_by_region:
        st.markdown('**Revenue by Region**')
        st.markdown(revenue_by_region)

    if sources:
        st.markdown('**Sources**')
        st.markdown(sources)


def call_wave_run_result(payload: dict) -> dict:
    req = urllib.request.Request(
        f'{API_BASE}/api/waves/run',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode('utf-8'))
        return {
            'ok': str(body.get('status', '')).lower() != 'failed',
            'wave_id': body.get('wave_id'),
            'status': body.get('status'),
            'error': body.get('error'),
            'body': body,
            'http_code': 200,
        }
    except urllib.error.HTTPError as e:
        try:
            err_json = json.loads(e.read().decode('utf-8', errors='replace'))
        except Exception:
            err_json = {"error": {"code": "HTTP_ERROR", "message": f"HTTP {e.code}", "node": "call_wave_run_result"}}
        return {
            'ok': False,
            'wave_id': err_json.get('wave_id'),
            'status': err_json.get('status', 'failed'),
            'error': err_json.get('error'),
            'body': err_json,
            'http_code': e.code,
        }
    except Exception:
        return {
            'ok': False,
            'wave_id': None,
            'status': 'failed',
            'error': {'code': 'REQUEST_FAILED', 'message': 'API unavailable or request timed out.', 'node': 'call_wave_run_result'},
            'body': {},
            'http_code': None,
        }


def call_wave_run(payload: dict) -> tuple[bool, str]:
    result = call_wave_run_result(payload)
    wave_id = result.get('wave_id')
    status = result.get('status')
    if result.get('ok') and wave_id:
        return True, f'Wave started: {wave_id} (status: {status})'
    err = result.get('error') or {}
    code = err.get('code', 'UNKNOWN')
    msg = err.get('message', 'Wave trigger failed.')
    if wave_id:
        return False, f'Wave denied: {wave_id} ({code}) {msg}'
    return False, f'Wave trigger failed ({code}): {msg}'


def apply_run_result(
    result: dict,
    label: str,
    show_success_message: bool = True,
    track_proof: bool = True,
    replace_proof: bool = False,
) -> None:
    wave_id = result.get('wave_id')
    status = result.get('status')
    ok = bool(result.get('ok'))
    err = result.get('error') or {}

    if ok and wave_id:
        st.session_state['focus_wave_id'] = wave_id
        st.session_state['show_latest_output'] = True
        if show_success_message:
            st.success(f"{label}: {wave_id} ({status})")
    else:
        code = err.get('code', 'UNKNOWN')
        msg = err.get('message', 'Denied')
        st.error(f"{label}: {wave_id or 'n/a'} ({code}) {msg}")

    if track_proof:
        st.session_state.setdefault('proof_runs', [])
        entry = {
            'label': label,
            'wave_id': wave_id,
            'status': status,
            'ok': ok,
            'error': err,
            'http_code': result.get('http_code'),
        }
        if replace_proof:
            st.session_state['proof_runs'] = [entry]
        else:
            st.session_state['proof_runs'].insert(0, entry)
            st.session_state['proof_runs'] = st.session_state['proof_runs'][:12]


def fetch_audit_export(wave_id: str) -> dict:
    req = urllib.request.Request(f'{API_BASE}/api/waves/{wave_id}/audit/export', method='GET')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_audit_verify(wave_id: str) -> dict:
    req = urllib.request.Request(f'{API_BASE}/api/waves/{wave_id}/audit/verify', method='GET')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def reset_prod_config() -> tuple[bool, str]:
    try:
        PROD_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROD_CONFIG_PATH.write_text(PROD_CONFIG_BASELINE_PATH.read_text(encoding='utf-8'), encoding='utf-8')
        return True, 'Reset config to baseline.'
    except Exception as e:
        return False, f'Reset failed: {e}'


def render_prod_agent_panel() -> bool:
    action_triggered = False
    st.markdown('<div class="sf-glass" style="margin-top:10px;">'
                '<div class="sf-kicker">Production Config Change Agent (Agent 3)</div>'
                '<div style="margin-top:6px;font-size:14px;color:#d6e8f5;">Run config mutation governance scenarios with allowlisted path and policy constraints.</div>'
                '</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown('#### Current Config')
        try:
            st.code(json.dumps(load_json_file(PROD_CONFIG_PATH), indent=2), language='json')
        except Exception as e:
            st.warning(f'Could not load config: {e}')
    with c2:
        scenario = st.selectbox('Scenario', PROD_AGENT_SCENARIOS, key='prod_agent_scenario')
        if st.button('Run Agent', key='prod_agent_run', width='stretch'):
            before_cfg = load_json_file(PROD_CONFIG_PATH) if PROD_CONFIG_PATH.exists() else {}
            run_result = run_production_config_scenario(scenario, api_base=API_BASE)
            after_cfg = load_json_file(PROD_CONFIG_PATH) if PROD_CONFIG_PATH.exists() else {}
            mutate = (run_result or {}).get('mutate') or {}
            body = mutate.get('body') or {}
            st.session_state['prod_agent_result'] = {
                'scenario': scenario,
                'wave': (run_result or {}).get('wave'),
                'status': body.get('status', 'REJECTED'),
                'reason_code': body.get('reason_code', 'REQUEST_FAILED'),
                'message': body.get('message', 'Mutation request failed'),
                'audit': body.get('audit', {}),
                'diff_preview': body.get('diff_preview', []),
                'before': before_cfg,
                'after': after_cfg,
            }
            action_triggered = True
        if st.button('Reset config', key='prod_agent_reset', width='stretch'):
            ok, msg = reset_prod_config()
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            action_triggered = True

    result = st.session_state.get('prod_agent_result')
    if result:
        st.markdown('#### Agent 3 Result')
        state = result.get('status', 'REJECTED')
        if state == 'ALLOWED':
            st.success(f"status={state} | reason_code={result.get('reason_code')}")
        else:
            st.error(f"status={state} | reason_code={result.get('reason_code')} | {result.get('message')}")
        st.markdown(f"Message: `{result.get('message')}`")
        st.markdown('**Diff Preview**')
        st.code(json.dumps(result.get('diff_preview', []), indent=2), language='json')
        st.markdown('**Audit**')
        st.code(json.dumps(result.get('audit', {}), indent=2), language='json')
        wave = result.get('wave') or {}
        wave_id = wave.get('wave_id')
        if wave_id:
            try:
                verify = fetch_audit_verify(wave_id)
                st.caption(f"wave_id={wave_id} | audit_verify={verify.get('integrity_status')}")
            except Exception as e:
                st.caption(f"audit verify unavailable: {e}")
    return action_triggered


def clean_summary(summary: str | None) -> str:
    if not summary:
        return 'No LLM summary found yet for this wave.'
    lower = summary.lower()
    if 'llm summary unavailable' in lower or 'llm digest unavailable' in lower:
        return 'Live LLM is unavailable for this run. Showing deterministic executive brief generated from verified wave outputs.'
    return summary


def summary_to_html(summary: str) -> str:
    safe = summary.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    safe = re.sub(r'(?m)^###\s+(.+)$', r'<strong>\1</strong>', safe)
    safe = re.sub(r'(?m)^##\s+(.+)$', r'<strong>\1</strong>', safe)
    safe = re.sub(r'(?m)^#\s+(.+)$', r'<strong>\1</strong>', safe)
    return safe.replace('\n', '<br>')


def compute_ocean_metrics(current_wave: sqlite3.Row, all_waves: list[sqlite3.Row], output_text: str | None, output_file_exists: bool) -> dict[str, str]:
    d = dict(current_wave)

    created = parse_iso(d.get('created_at') or d.get('started_at'))
    started = parse_iso(d.get('started_at') or d.get('created_at'))
    completed = parse_iso(d.get('completed_at') or d.get('updated_at'))

    wave_length = None
    if started and completed and completed >= started:
        wave_length = (completed - started).total_seconds()

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    starts_24h = 0
    for w in all_waves:
        wd = dict(w)
        ts = parse_iso(wd.get('started_at') or wd.get('created_at'))
        if ts and ts.astimezone(timezone.utc) >= cutoff:
            starts_24h += 1

    wave_frequency = starts_24h / 24.0

    words = len((output_text or '').split())
    sections = len(re.findall(r'^##\s+', output_text or '', flags=re.MULTILINE))
    wave_depth_proxy = max(words // 40 + sections * 2, sections)

    checks = 0
    if resolve_policy_hash(current_wave) != 'N/A':
        checks += 1
    if resolve_integrity(current_wave) in {'VALID', 'FLAGGED'}:
        checks += 1
    if str(d.get('status', '')).lower() in {'complete', 'failed'}:
        checks += 1
    if d.get('error_code'):
        checks += 1
    wave_height = f'{checks}/5'

    write_count = 1 if output_file_exists else 0

    return {
        'Wave Length': f'{wave_length:.2f}s' if wave_length is not None else 'N/A',
        'Wave Frequency': f'{wave_frequency:.2f}/hr',
        'Wave Depth': f'{wave_depth_proxy} (proxy)',
        'Wave Height': f'{wave_height} (beta)',
        'Write Count': str(write_count),
        'Integrity Status': resolve_integrity(current_wave),
    }


def render_brand_header(db_path: Path) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="sf-wordmark">
  {WAVE_ICON}
  <div>
    <div class="sf-title"><span class="s">SURFIT</span><span class="d">.</span><span class="a">AI</span></div>
    <div class="sf-sub">Local Wave Control Deck</div>
  </div>
</div>
<div style="height:10px"></div>
<div style="font-size:12px;color:#7a9ab8;letter-spacing:.08em;text-transform:uppercase;">Connected DB: {db_path}</div>
<div style="height:8px"></div>
""",
        unsafe_allow_html=True,
    )


def render_trigger_panel() -> bool:
    action_triggered = False
    st.markdown('<div class="sf-glass">', unsafe_allow_html=True)
    st.markdown('<div class="sf-kicker">Wave Atlas</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="margin-top:6px;font-size:14px;color:#d6e8f5;">Customer Atlas (Wave Library) available to agent scheduling.</div>',
        unsafe_allow_html=True,
    )
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            '<div style="background:#111d30;border:1px solid #1e3050;border-radius:10px;padding:10px 12px;">'
            '<div style="font-size:11px;color:#7a9ab8;letter-spacing:.12em;text-transform:uppercase;">production_config_change_v1</div>'
            '<div style="margin-top:6px;font-size:13px;color:#e2eaf5;">Production config mutation wave</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button('View Prod Config Wave + Agent Script', key='atlas_prod', width='stretch'):
            current = st.session_state.get('atlas_selected')
            st.session_state['atlas_selected'] = None if current == 'production_config_change_v1' else 'production_config_change_v1'
    with a2:
        st.markdown(
            '<div style="background:#111d30;border:1px solid #1e3050;border-radius:10px;padding:10px 12px;">'
            '<div style="font-size:11px;color:#7a9ab8;letter-spacing:.12em;text-transform:uppercase;">market_intelligence_digest_v1</div>'
            '<div style="margin-top:6px;font-size:13px;color:#e2eaf5;">Market intelligence wave</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button('View Market Wave + Agent Script', key='atlas_market', width='stretch'):
            current = st.session_state.get('atlas_selected')
            st.session_state['atlas_selected'] = None if current == 'market_intelligence_digest_v1' else 'market_intelligence_digest_v1'
    with a3:
        st.markdown(
            '<div style="background:#111d30;border:1px solid #1e3050;border-radius:10px;padding:10px 12px;">'
            '<div style="font-size:11px;color:#7a9ab8;letter-spacing:.12em;text-transform:uppercase;">sales_report_v1</div>'
            '<div style="margin-top:6px;font-size:13px;color:#e2eaf5;">Finance reporting wave</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button('View Sales Wave + Agent Script', key='atlas_sales', width='stretch'):
            current = st.session_state.get('atlas_selected')
            st.session_state['atlas_selected'] = None if current == 'sales_report_v1' else 'sales_report_v1'

    selected = st.session_state.get('atlas_selected')
    if selected in ATLAS_ENTRIES:
        entry = ATLAS_ENTRIES[selected]
        st.markdown(f'#### Atlas Entry: `{selected}`')
        st.markdown('**Wave Script**')
        st.code(json.dumps(entry['wave_script'], indent=2), language='json')
        st.markdown('**Agent Script**')
        try:
            st.code(entry['agent_script'].read_text(encoding='utf-8'), language='javascript')
        except Exception as e:
            st.warning(f'Could not load agent script: {e}')
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-glass" style="margin-top:10px;"><div class="sf-kicker">Demo Trigger</div><div style="margin-top:6px;font-size:14px;color:#d6e8f5;">Run Scheduled Wave to simulate cron-triggered agent execution.</div></div>', unsafe_allow_html=True)
    t0, t1, t2, t3, t4 = st.columns([0.45, 1, 1, 1, 0.45])
    with t1:
        if st.button('Run Scheduled Wave (Prod Config)', width='stretch'):
            apply_run_result(call_wave_run_result(PROD_AGENT_WAVE_PAYLOAD), 'Run Scheduled Wave (Prod Config)', track_proof=False)
            action_triggered = True
    with t2:
        if st.button('Run Scheduled Wave (Market Intelligence)', width='stretch'):
            apply_run_result(call_wave_run_result(MARKET_INTEL_PAYLOAD), 'Run Scheduled Wave (Market Intelligence)', track_proof=False)
            action_triggered = True
    with t3:
        if st.button('Run Scheduled Wave (Finance)', width='stretch'):
            apply_run_result(call_wave_run_result(FINANCE_PAYLOAD), 'Run Scheduled Wave (Finance)', track_proof=False)
            action_triggered = True

    b1, b2, b3 = st.columns([1.45, 1, 1.45])
    with b2:
        if st.button('Clear Output', width='stretch'):
            st.session_state['show_latest_output'] = False
            st.session_state['focus_wave_id'] = None
            st.session_state['proof_runs'] = []
            action_triggered = True
            st.rerun()

    st.markdown('<div class="sf-glass" style="margin-top:10px;">'
                '<div class="sf-kicker">Enforcement Proof</div>'
                '<div style="margin-top:6px;font-size:14px;color:#d6e8f5;">Run allowed and denied boundary cases with auditable evidence.</div>'
                '</div>', unsafe_allow_html=True)

    p0, p1, p2, p3, p4 = st.columns([0.45, 1, 1, 1, 0.45])
    proof_actions = [
        ('proof_deny_agent', 'Run Unauthorized Agent', UNAUTHORIZED_AGENT_PAYLOAD),
        ('proof_deny_path', 'Run Path Violation', PATH_VIOLATION_PAYLOAD),
        ('proof_deny_policy', 'Run Policy Mismatch', POLICY_MISMATCH_PAYLOAD),
    ]
    for col, (key, label, payload) in zip([p1, p2, p3], proof_actions):
        with col:
            if st.button(label, key=key, width='stretch'):
                apply_run_result(
                    call_wave_run_result(payload),
                    label,
                    show_success_message=False,
                    replace_proof=True,
                )
                action_triggered = True

    proof_runs = st.session_state.get('proof_runs', [])
    if proof_runs:
        st.markdown('#### Proof Results')
        for rec in proof_runs:
            wave_id = rec.get('wave_id')
            err = rec.get('error') or {}
            head = f"- `{rec.get('label')}` | wave `{wave_id}` | status `{rec.get('status')}`"
            if rec.get('ok'):
                st.markdown(head + " | result `ALLOW`")
            else:
                st.markdown(head + f" | result `DENY` ({err.get('code','UNKNOWN')})")
            if wave_id:
                try:
                    audit = fetch_audit_export(wave_id)
                    verify = fetch_audit_verify(wave_id)
                    decision_events = audit.get('events', [])
                    highlights = []
                    for e in decision_events[-4:]:
                        highlights.append(f"{e.get('decision')}:{e.get('rule')}")
                    st.caption(
                        f"verify={verify.get('integrity_status')} | decisions={', '.join(highlights) if highlights else 'none'}"
                    )
                except Exception as e:
                    st.caption(f"audit unavailable: {e}")

    if render_prod_agent_panel():
        action_triggered = True
    return action_triggered


def render_metric_grid(metrics: dict[str, str]) -> None:
    labels = [
        ('Wave Length', 'Autonomous execution duration'),
        ('Wave Frequency', 'Trigger cadence (24h)'),
        ('Wave Depth', 'Governed execution depth'),
        ('Wave Height', 'Governance intensity score'),
        ('Write Count', 'Mutation attempts'),
        ('Integrity Status', 'Tamper-evident result'),
    ]
    cards = []
    for key, desc in labels:
        cards.append(
            f'<div class="sf-metric"><div class="k">{key}</div><div class="v">{metrics.get(key, "N/A")}</div><div class="d">{desc}</div></div>'
        )
    st.markdown(f'<div class="sf-metrics">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_latest_output(latest_wave: sqlite3.Row, all_waves: list[sqlite3.Row]) -> None:
    d = dict(latest_wave)
    output_path = resolve_output_path(latest_wave)
    resolved_output_path, output_text = load_output_text(output_path)

    raw_summary = None
    if output_text:
        raw_summary = (
            extract_section(output_text, 'LLM Summary')
            or extract_section(output_text, 'AI Digest')
            or extract_section(output_text, 'Executive Summary')
        )
    summary = clean_summary(raw_summary)

    chip = '<span class="sf-chip sf-chip-ok">LLM Live</span>'
    if raw_summary:
        lowered = raw_summary.lower()
        if 'fallback' in lowered or 'deterministic' in lowered or 'unavailable' in lowered:
            chip = '<span class="sf-chip sf-chip-warn">LLM Fallback</span>'

    st.markdown('### Full Rendered Output')
    if output_text and resolved_output_path:
        st.caption(f'Output file: {display_path(output_path, resolved_output_path)}')
        st.markdown(de_duplicate_rendered_output(output_text))
    else:
        st.warning('Output file not found for this wave.')

    metrics = compute_ocean_metrics(latest_wave, all_waves, output_text, resolved_output_path is not None)
    render_metric_grid(metrics)

    summary_html = summary_to_html(summary)
    st.markdown(
        f"""
<div class="sf-glass">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
    <div class="sf-kicker">Latest Completed Wave</div>
    {chip}
  </div>
  <div style="margin-top:8px;font-size:20px;font-weight:600;color:#e2eaf5;">LLM Executive Summary</div>
  <div style="margin-top:10px;font-size:15px;line-height:1.7;color:#d8e8f5;">{summary_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    render_output_snapshot(output_text)


def find_by_wave_id(rows: list[sqlite3.Row], value: str) -> sqlite3.Row | None:
    target = value.strip()
    if not target:
        return None
    exact = [r for r in rows if str(dict(r).get('wave_id', '')) == target]
    if exact:
        return exact[0]
    pref = [r for r in rows if str(dict(r).get('wave_id', '')).startswith(target)]
    if len(pref) == 1:
        return pref[0]
    return None


def render_wave_history(waves: list[sqlite3.Row]) -> None:
    rows = []
    for r in waves:
        d = dict(r)
        status = str(d.get('status') or '')
        status_flag = 'green' if status.lower() == 'complete' else 'red'
        rows.append(
            {
                'wave_id': str(d.get('wave_id') or '')[:8],
                'wave_template_id': d.get('wave_template_id'),
                'agent_id': d.get('agent_id'),
                'status': f'{status} ({status_flag})',
                'integrity_status': resolve_integrity(r),
                'policy_hash': resolve_policy_hash(r),
                'started_at': d.get('started_at') or d.get('created_at'),
            }
        )

    st.dataframe(rows, width='stretch', hide_index=True)

    wave_lookup = st.text_input('Enter full wave_id or unique prefix for drill-down')
    picked = find_by_wave_id(waves, wave_lookup)
    if wave_lookup and picked is None:
        st.warning('No unique match for that wave_id.')

    if picked is not None:
        d = dict(picked)
        output_path = resolve_output_path(picked)
        resolved_output_path, output_text = load_output_text(output_path)

        st.markdown('### Wave Drill-Down')
        st.code(
            json.dumps(
                {
                    'wave_id': d.get('wave_id'),
                    'agent_id': d.get('agent_id'),
                    'wave_template_id': d.get('wave_template_id'),
                    'status': d.get('status'),
                    'integrity': resolve_integrity(picked),
                    'policy_hash': resolve_policy_hash(picked),
                    'started_at': d.get('started_at') or d.get('created_at'),
                    'completed_at': d.get('completed_at') or d.get('updated_at'),
                    'output_path': output_path,
                },
                indent=2,
            ),
            language='json',
        )
        if output_text and resolved_output_path:
            st.caption(f'Output file: {display_path(output_path, resolved_output_path)}')
            st.markdown(de_duplicate_rendered_output(output_text))


def main() -> None:
    st.set_page_config(page_title='Surfit AI Local Demo', layout='wide')
    if 'show_latest_output' not in st.session_state:
        st.session_state['show_latest_output'] = False
    if 'focus_wave_id' not in st.session_state:
        st.session_state['focus_wave_id'] = None

    db_path = find_db_path()
    if not db_path:
        st.error('No SQLite DB found. Checked SURFIT_DB_PATH, project surfit_runs.db, and /tmp/surfit_runs.db.')
        return

    render_brand_header(db_path)

    conn = connect_db(db_path)
    try:
        if not has_table(conn, 'waves'):
            st.error('Table `waves` does not exist in this DB.')
            st.code('\n'.join(list_tables(conn)))
            return

        waves = fetch_waves(conn)
        if not waves:
            st.warning('No waves found in `waves` table yet. Run a scheduled wave to populate the demo.')

        latest_complete = None
        if waves:
            latest_complete = next(
                (r for r in waves if str(dict(r).get('status', '')).lower() == 'complete'),
                waves[0],
            )
        focus_wave_id = st.session_state.get('focus_wave_id')
        focus_wave = next((r for r in waves if str(dict(r).get('wave_id', '')) == focus_wave_id), None)

        tab_latest, tab_history = st.tabs(['Latest Output', 'Wave History'])
        with tab_latest:
            action_triggered = render_trigger_panel()
            if action_triggered:
                # Refresh waves after button actions so this render uses current run state.
                waves = fetch_waves(conn)
                latest_complete = None
                if waves:
                    latest_complete = next(
                        (r for r in waves if str(dict(r).get('status', '')).lower() == 'complete'),
                        waves[0],
                    )
                focus_wave_id = st.session_state.get('focus_wave_id')
                focus_wave = next((r for r in waves if str(dict(r).get('wave_id', '')) == focus_wave_id), None)
            if st.session_state.get('show_latest_output'):
                if focus_wave_id:
                    if not focus_wave:
                        st.info(
                            f"Selected wave `{focus_wave_id}` is registering. "
                            "Refresh in a few seconds to view this wave output."
                        )
                    else:
                        focus_status = str(dict(focus_wave).get('status', '')).lower()
                        if focus_status != 'complete':
                            st.info(
                                f"Selected wave `{dict(focus_wave).get('wave_id')}` is `{focus_status}`. "
                                "Refresh in a few seconds to view its completed output."
                            )
                        else:
                            render_latest_output(focus_wave, waves)
                else:
                    if latest_complete is None:
                        st.info('No completed waves yet. Run a scheduled wave, then view results here.')
                    else:
                        render_latest_output(latest_complete, waves)
            else:
                st.info('No wave output loaded yet. Run a scheduled wave, then review results here.')
        with tab_history:
            render_wave_history(waves)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
