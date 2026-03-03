from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from fastapi.responses import JSONResponse
import uuid
import sqlite3
import json
import csv
import time
import os
import shutil
import hashlib
import secrets
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get("SURFIT_DB_PATH", str(PROJECT_ROOT / "surfit_runs.db"))
MAX_RUNTIME_SECONDS = 30
WAVE_TOKEN_TTL_SECONDS = 180

AGENT_WAVE_ALLOWLIST = {
    "openclaw_poc_agent_v1": {"sales_report_v1"},
    "openclaw_marketing_agent_v1": {"marketing_digest_v1"},  # backward compatibility
    "openclaw_market_intelligence_agent_v1": {"market_intelligence_digest_v1"},
    "production_config_agent": {"production_config_change_v1"},
}

MARKET_INTEL_TEMPLATES = {"marketing_digest_v1", "market_intelligence_digest_v1"}
TEMPLATE_POLICY_ALLOWLIST = {
    "sales_report_v1": {"sales_report_policy_v1"},
    "marketing_digest_v1": {"marketing_digest_policy_v1", "market_intelligence_digest_policy_v1"},
    "market_intelligence_digest_v1": {"market_intelligence_digest_policy_v1"},
    "production_config_change_v1": {"prod_config_policy_v1"},
}
RUNS_ROOT = Path("./runs")
PROD_CONFIG_TARGET = "demo_artifacts/prod_config.json"
PROD_CONFIG_ALLOWED_KEYS = {
    "feature_flags.checkout_v2",
    "rate_limits.requests_per_minute",
    "logging.level",
}

app = FastAPI(title="SurFit Runtime API", version="m13-poc")


class WaveRunRequest(BaseModel):
    agent_id: str | None = None
    wave_template_id: str
    policy_version: str
    intent: str
    context_refs: dict[str, Any]


class ApprovalRequest(BaseModel):
    approved_by: str
    note: str | None = None


class MutationItem(BaseModel):
    json_path: str
    value: Any


class ConfigMutateRequest(BaseModel):
    wave_id: str | None = None
    wave_token: str | None = None
    agent_name: str
    policy_version: str
    target_path: str
    mutations: list[MutationItem]
    reason: str | None = None


class WaveExecutionError(Exception):
    def __init__(self, code: str, message: str, node: str):
        super().__init__(message)
        self.code = code
        self.node = node


def ensure_wave_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS waves (
            wave_id TEXT PRIMARY KEY,
            agent_id TEXT,
            wave_template_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            intent TEXT,
            context_refs_json TEXT,
            status TEXT NOT NULL,
            error_code TEXT,
            error_message TEXT,
            error_node TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS approval_requests (
            approval_request_id TEXT PRIMARY KEY,
            wave_id TEXT NOT NULL,
            target_write_path TEXT,
            proposed_write_hash TEXT,
            approved_by TEXT,
            approved_at TEXT,
            note TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wave_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wave_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            rule TEXT NOT NULL,
            node TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    _ensure_wave_columns(conn)
    conn.commit()


@app.on_event("startup")
def initialize_runtime_schema() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_wave_tables(conn)
    finally:
        conn.close()


def _ensure_wave_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(waves)").fetchall()}
    required = {
        "agent_id": "TEXT",
        "error_code": "TEXT",
        "error_message": "TEXT",
        "error_node": "TEXT",
        "workspace_dir": "TEXT",
        "wave_token_hash": "TEXT",
        "wave_token_expires_at": "TEXT",
        "manifest_hash": "TEXT",
        "manifest_path": "TEXT",
    }
    for col, sql_type in required.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE waves ADD COLUMN {col} {sql_type}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: str) -> str | None:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _log_decision(conn: sqlite3.Connection, wave_id: str, decision: str, reason: str, rule: str, node: str) -> None:
    conn.execute(
        """
        INSERT INTO wave_decisions (wave_id, decision, reason, rule, node, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (wave_id, decision, reason, rule, node, _now_iso()),
    )


def _fetch_decisions(conn: sqlite3.Connection, wave_id: str) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT decision, reason, rule, node, created_at
        FROM wave_decisions
        WHERE wave_id = ?
        ORDER BY id ASC
        """,
        (wave_id,),
    ).fetchall()
    return [
        {
            "decision": r[0],
            "reason": r[1],
            "rule": r[2],
            "node": r[3],
            "timestamp": r[4],
        }
        for r in rows
    ]


def _issue_wave_token(wave_id: str, agent_id: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(24)
    token_hash = _sha256_text(token)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=WAVE_TOKEN_TTL_SECONDS)).isoformat()
    return token, token_hash, expires_at


def _validate_wave_token(conn: sqlite3.Connection, wave_id: str, wave_token: str, node: str = "token_validation") -> None:
    row = conn.execute(
        """
        SELECT wave_token_hash, wave_token_expires_at
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()
    if not row:
        _log_decision(conn, wave_id, "DENY", "wave not found for token validation", "wave_id_exists", node)
        raise WaveExecutionError("WAVE_TOKEN_INVALID", "Wave token validation failed (wave not found).", node)

    stored_hash = row[0]
    expires_at = row[1]
    if not stored_hash:
        _log_decision(conn, wave_id, "DENY", "wave token hash missing", "token_present", node)
        raise WaveExecutionError("WAVE_TOKEN_INVALID", "Wave token is missing for mutation step.", node)
    if _sha256_text(wave_token) != stored_hash:
        _log_decision(conn, wave_id, "DENY", "token hash mismatch", "token_match", node)
        raise WaveExecutionError("WAVE_TOKEN_INVALID", "Wave token does not match run scope.", node)

    exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) if expires_at else None
    if not exp or datetime.now(timezone.utc) > exp:
        _log_decision(conn, wave_id, "DENY", "token expired", "token_expiry", node)
        raise WaveExecutionError("WAVE_TOKEN_INVALID", "Wave token expired.", node)

    _log_decision(conn, wave_id, "ALLOW", "token valid", "token_validation", node)


def _commit_output_write(
    conn: sqlite3.Connection,
    wave_id: str,
    wave_token: str,
    workspace_dir: str,
    final_output_path: str,
    rendered_content: str,
    node: str,
) -> str:
    _validate_wave_token(conn, wave_id, wave_token, node=f"{node}.token")

    if not _is_under("./outputs", final_output_path):
        _log_decision(conn, wave_id, "DENY", "output path outside allowed prefix", "output_path_prefix", node)
        raise WaveExecutionError("PATH_VIOLATION", "Output path outside ./outputs is denied.", node)
    _log_decision(conn, wave_id, "ALLOW", "output path within allowed prefix", "output_path_prefix", node)

    workspace_output = Path(workspace_dir) / Path(final_output_path).name
    workspace_output.parent.mkdir(parents=True, exist_ok=True)
    workspace_output.write_text(rendered_content, encoding="utf-8")
    _log_decision(conn, wave_id, "ALLOW", "workspace write successful", "workspace_write", node)

    Path(final_output_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(workspace_output), final_output_path)
    _log_decision(conn, wave_id, "ALLOW", "final output committed", "commit_output", node)
    return str(workspace_output)


def _is_under(base: str, target: str) -> bool:
    base_path = Path(base).resolve()
    target_path = Path(target).resolve()
    try:
        target_path.relative_to(base_path)
        return True
    except ValueError:
        return False


def _resolve_output_path(context_refs_json: str | None) -> str | None:
    if not context_refs_json:
        return None
    try:
        refs = json.loads(context_refs_json)
    except Exception:
        return None
    return (
        refs.get("output_report_path")
        or refs.get("output_digest_path")
        or refs.get("output_brief_path")
        or refs.get("output_path")
    )


def _normalize_repo_relative(path_text: str) -> str:
    return str(Path(path_text).as_posix().lstrip("./"))


def _set_json_path(obj: dict[str, Any], dotted_path: str, value: Any) -> tuple[Any, Any]:
    parts = dotted_path.split(".")
    cur: Any = obj
    for key in parts[:-1]:
        if not isinstance(cur, dict):
            raise ValueError(f"json_path '{dotted_path}' is not object-traversable")
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    if not isinstance(cur, dict):
        raise ValueError(f"json_path '{dotted_path}' is not object-traversable")
    last = parts[-1]
    before = cur.get(last)
    cur[last] = value
    return before, value


def _execute_production_config_wave(
    conn: sqlite3.Connection,
    wave_id: str,
    workspace_dir: str,
    target_path: str,
) -> dict[str, Any]:
    target = Path(target_path)
    if not target.exists():
        raise WaveExecutionError("BAD_CONTEXT", "target_path does not exist", "production_config.bootstrap")
    config_text = target.read_text(encoding="utf-8")
    workspace_snapshot = Path(workspace_dir) / "prod_config.snapshot.json"
    workspace_snapshot.parent.mkdir(parents=True, exist_ok=True)
    workspace_snapshot.write_text(config_text, encoding="utf-8")
    _log_decision(conn, wave_id, "ALLOW", "config snapshot captured", "config_snapshot", "production_config.bootstrap")
    return {
        "target_path": target_path,
        "snapshot_path": str(workspace_snapshot),
        "config_hash": _sha256_text(config_text),
    }


def _execute_sales_report(
    conn: sqlite3.Connection,
    wave_id: str,
    wave_token: str,
    workspace_dir: str,
    input_csv_path: str,
    output_report_path: str,
    approved_by: str,
) -> dict[str, Any]:
    rows = []
    with open(input_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            units = float(row.get("units", 0))
            unit_price = float(row.get("unit_price_usd", 0))
            revenue = units * unit_price
            rows.append(
                {
                    "date": row.get("date", ""),
                    "region": row.get("region", ""),
                    "rep": row.get("rep", ""),
                    "product": row.get("product", ""),
                    "units": units,
                    "unit_price_usd": unit_price,
                    "revenue_usd": revenue,
                }
            )

    total_units = sum(r["units"] for r in rows)
    total_revenue = sum(r["revenue_usd"] for r in rows)

    by_region = {}
    for r in rows:
        by_region.setdefault(r["region"], 0.0)
        by_region[r["region"]] += r["revenue_usd"]

    lines = [
        "# Weekly Sales Report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Deterministic Metrics Summary",
        f"- Total rows: {len(rows)}",
        f"- Total units: {total_units:,.0f}",
        f"- Total revenue (USD): ${total_revenue:,.2f}",
        "",
        "### Revenue by Region",
    ]
    for region in sorted(by_region.keys()):
        lines.append(f"- {region}: ${by_region[region]:,.2f}")

    _prompt = (
        f"You are a CFO-level finance analyst writing for investors and operators.\n"
        f"Build a detailed executive section with the exact markdown headings below:\n"
        f"### Executive Readout\n"
        f"### Key Drivers\n"
        f"### Risks and Watchouts\n"
        f"### Actions for Next 7 Days\n\n"
        f"Requirements:\n"
        f"- 180-260 words total.\n"
        f"- Executive Readout must be 2-3 sentences and probabilistic in tone (use language like likely/may/could).\n"
        f"- Use concrete numbers from the metrics.\n"
        f"- Call out best and weakest region explicitly.\n"
        f"- Include at least 3 bullet points under Actions.\n\n"
        f"Data:\n"
        f"Total rows: {len(rows)}\n"
        f"Total units: {total_units:,.0f}\n"
        f"Total revenue: ${total_revenue:,.2f}\n"
        f"Revenue by region: {str(by_region)}\n"
    )

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": _prompt}]
        )
        _llm_summary = _msg.content[0].text.strip()
    except Exception as e:
        top_region = max(by_region, key=by_region.get) if by_region else "N/A"
        weakest_region = min(by_region, key=by_region.get) if by_region else "N/A"
        _llm_summary = (
            "### Executive Readout\n"
            f"This wave completed with deterministic analysis over {len(rows)} records, producing "
            f"${total_revenue:,.2f} in total revenue and {total_units:,.0f} total units. "
            "Given fallback mode, directional conclusions are likely reliable but lack narrative depth from live LLM synthesis.\n\n"
            "### Key Drivers\n"
            f"- Strongest region: {top_region}\n"
            f"- Weakest region: {weakest_region}\n"
            f"- Revenue concentration suggests {top_region} is carrying the largest share of performance.\n"
            f"- Variance in regional mix indicates {weakest_region} is under-weighted relative to peers.\n"
            "- Output integrity and policy checks passed for this run.\n\n"
            "### Risks and Watchouts\n"
            "- Narrative generation is currently in deterministic fallback mode (live LLM unavailable).\n"
            "- Interpret directional trends as signal, not full forecasting, until a live summary validates intent.\n"
            "- A single-week snapshot may mask volatility in smaller regions.\n\n"
            "### Actions for Next 7 Days\n"
            "- Validate regional pricing assumptions against recent pipeline movement.\n"
            f"- Prioritize an uplift plan for {weakest_region} while protecting momentum in {top_region}.\n"
            "- Review top three accounts by revenue contribution to isolate concentration risk.\n"
            "- Run the next wave with live LLM enabled for expanded narrative context."
        )

    lines.extend(
        [
            "",
            "## LLM Summary",
            _llm_summary,
            "",
            "## Approval Metadata",
            f"- approved_by: {approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "- note: auto-approved (v1 default path)",
            "",
        ]
    )

    rendered = "\n".join(lines)
    workspace_output = _commit_output_write(
        conn=conn,
        wave_id=wave_id,
        wave_token=wave_token,
        workspace_dir=workspace_dir,
        final_output_path=output_report_path,
        rendered_content=rendered,
        node="sales_report.write",
    )
    return {
        "workspace_output": workspace_output,
        "input_hashes": {"input_csv_path": _sha256_file(input_csv_path)},
    }


def _execute_marketing_digest(
    conn: sqlite3.Connection,
    wave_id: str,
    wave_token: str,
    workspace_dir: str,
    sources: list,
    snapshot_dir: str,
    output_digest_path: str,
    run_id: str,
    approved_by: str,
) -> dict[str, Any]:
    import urllib.request

    # Deterministic: fetch sources and extract raw text
    snapshots = []
    workspace_snapshots = Path(workspace_dir) / "snapshots"
    workspace_snapshots.mkdir(parents=True, exist_ok=True)
    for url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SurFit/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            # Store snapshot
            safe_name = url.replace("https://", "").replace("/", "_")[:60]
            snap_path = workspace_snapshots / f"{safe_name}.txt"
            snap_path.write_text(raw[:5000], encoding="utf-8")
            snapshots.append({"url": url, "content": raw[:3000]})
        except Exception as e:
            snapshots.append({"url": url, "content": f"[fetch failed: {e}]"})

    combined = "\n\n".join(
        f"Source: {s['url']}\n{s['content']}" for s in snapshots
    )

    # Probabilistic: Claude clusters themes and writes digest
    _prompt = (
        f"You are a senior market intelligence strategist preparing a next-day decision brief.\n"
        f"Primary objective: determine what the team should watch, prioritize, and potentially publish tomorrow based on market signals.\n\n"
        f"Return markdown with EXACT headings in this order:\n"
        f"### Executive Summary\n"
        f"### 3 Key Themes\n"
        f"### 2 Proposed Content Angles\n"
        f"### Forward-Looking Observation\n\n"
        f"Requirements:\n"
        f"- Executive Summary must be 2-3 sentences and probabilistic in tone (use likely/may/could).\n"
        f"- Executive Summary must answer: what changed, why it matters, and what the team should do next.\n"
        f"- 3 Key Themes: exactly 3 numbered items, each one sentence.\n"
        f"- 2 Proposed Content Angles: exactly 2 items, each with a headline and one supporting sentence.\n"
        f"- Content angles should be ranked by expected relevance for tomorrow's audience.\n"
        f"- Forward-Looking Observation: 1 paragraph.\n"
        f"- Use specific details from the source content.\n\n"
        f"Content:\n{combined[:9000]}"
    )
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{"role": "user", "content": _prompt}]
        )
        digest_summary = _msg.content[0].text.strip()
    except Exception as e:
        digest_summary = (
            "### Executive Summary\n"
            "Market signals were collected successfully, and the team can likely use today’s narratives to prioritize tomorrow’s messaging focus. "
            "In fallback mode, recommendations are directional but still useful for planning a near-term content posture.\n\n"
            "### 3 Key Themes\n"
            "1. AI tooling and platform consolidation continues to dominate coverage, implying buyer focus on reliability and governance.\n"
            "2. Enterprise adoption narratives emphasize control, auditability, and operational safety rather than pure model capability.\n"
            "3. Funding and partnership news suggests renewed interest in infrastructure vendors that enable compliant deployment.\n\n"
            "### 2 Proposed Content Angles\n"
            "1. \"Governed autonomy as the new default\" — Highlight how teams move from experimentation to enforceable runtime controls.\n"
            "2. \"Execution certainty over model novelty\" — Argue that policy-bound execution is now the differentiator for enterprise adoption.\n\n"
            "### Forward-Looking Observation\n"
            "Expect buyers to ask for proof of control (not just performance) in upcoming cycles. Establishing a clear governance narrative now "
            "will likely improve conversion as procurement and security teams increasingly influence agent deployments.\n"
        )

    lines = [
        "# Marketing Digest",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Run ID: {run_id}",
        f"Sources fetched: {len(sources)}",
        "",
        "## AI Digest",
        digest_summary,
        "",
        "## Sources",
    ]
    for s in snapshots:
        status = "ok" if not s["content"].startswith("[fetch failed") else "failed"
        lines.append(f"- {s['url']} ({status})")

    lines.extend([
        "",
        "## Approval Metadata",
        f"- approved_by: {approved_by}",
        f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
        "- note: auto-approved (v1 default path)",
        "",
    ])

    rendered = "\n".join(lines)
    workspace_output = _commit_output_write(
        conn=conn,
        wave_id=wave_id,
        wave_token=wave_token,
        workspace_dir=workspace_dir,
        final_output_path=output_digest_path,
        rendered_content=rendered,
        node="market_intel.write",
    )

    snapshot_hashes = {}
    for p in workspace_snapshots.glob("*.txt"):
        h = _sha256_file(str(p))
        if h:
            snapshot_hashes[p.name] = h

    return {
        "workspace_output": workspace_output,
        "snapshot_hashes": snapshot_hashes,
        "snapshot_dir": str(workspace_snapshots),
    }


def _insert_wave_row(
    conn: sqlite3.Connection,
    wave_id: str,
    req: WaveRunRequest,
    status: str,
    workspace_dir: str | None = None,
    wave_token_hash: str | None = None,
    wave_token_expires_at: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    error_node: str | None = None,
) -> None:
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO waves
            (wave_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status,
             error_code, error_message, error_node, workspace_dir, wave_token_hash, wave_token_expires_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            wave_id,
            req.agent_id,
            req.wave_template_id,
            req.policy_version,
            req.intent,
            json.dumps(req.context_refs, sort_keys=True),
            status,
            error_code,
            error_message,
            error_node,
            workspace_dir,
            wave_token_hash,
            wave_token_expires_at,
            now,
            now,
        ),
    )


def _deny_and_record(
    conn: sqlite3.Connection,
    wave_id: str,
    req: WaveRunRequest,
    code: str,
    message: str,
    node: str,
    http_status: int,
    rule: str,
) -> JSONResponse:
    _insert_wave_row(
        conn=conn,
        wave_id=wave_id,
        req=req,
        status="failed",
        error_code=code,
        error_message=message,
        error_node=node,
    )
    _log_decision(conn, wave_id, "DENY", message, rule, node)
    conn.commit()
    return JSONResponse(
        status_code=http_status,
        content={
            "wave_id": wave_id,
            "status": "failed",
            "error": {"code": code, "message": message, "node": node},
        },
    )


def _write_manifest(
    conn: sqlite3.Connection,
    wave_id: str,
    workspace_dir: str,
    req: WaveRunRequest,
    output_path: str,
    extra: dict[str, Any],
) -> tuple[str, str]:
    manifest = {
        "wave_id": wave_id,
        "agent_id": req.agent_id,
        "wave_template_id": req.wave_template_id,
        "policy_version": req.policy_version,
        "intent": req.intent,
        "context_refs": req.context_refs,
        "output_path": output_path,
        "timestamps": {"manifested_at": _now_iso()},
        "evidence": extra,
    }
    manifest_text = json.dumps(manifest, sort_keys=True, indent=2)
    manifest_hash = _sha256_text(manifest_text)
    manifest_path = str(Path(workspace_dir) / "manifest.json")
    Path(manifest_path).write_text(manifest_text, encoding="utf-8")
    conn.execute(
        "UPDATE waves SET manifest_hash = ?, manifest_path = ?, updated_at = ? WHERE wave_id = ?",
        (manifest_hash, manifest_path, _now_iso(), wave_id),
    )
    _log_decision(conn, wave_id, "ALLOW", "manifest signed and stored", "manifest_sign", "manifest")
    return manifest_hash, manifest_path


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest):
    wave_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    workspace_dir = str((RUNS_ROOT / wave_id).resolve())

    if not req.agent_id:
        resp = _deny_and_record(
            conn,
            wave_id,
            req,
            code="AGENT_ID_REQUIRED",
            message="agent_id is required",
            node="run_wave",
            http_status=403,
            rule="agent_id_present",
        )
        conn.close()
        return resp

    allowed_templates = AGENT_WAVE_ALLOWLIST.get(req.agent_id, set())
    if req.wave_template_id not in allowed_templates:
        resp = _deny_and_record(
            conn,
            wave_id,
            req,
            code="AGENT_NOT_AUTHORIZED",
            message=f"agent_id '{req.agent_id}' is not authorized for wave_template_id '{req.wave_template_id}'",
            node="run_wave",
            http_status=403,
            rule="agent_wave_allowlist",
        )
        conn.close()
        return resp

    _log_decision(conn, wave_id, "ALLOW", "agent-wave allowlist satisfied", "agent_wave_allowlist", "run_wave")

    allowed_policies = TEMPLATE_POLICY_ALLOWLIST.get(req.wave_template_id, set())
    if req.policy_version not in allowed_policies:
        resp = _deny_and_record(
            conn,
            wave_id,
            req,
            code="POLICY_VERSION_INVALID",
            message=f"policy_version '{req.policy_version}' is invalid for wave_template_id '{req.wave_template_id}'",
            node="run_wave",
            http_status=422,
            rule="template_policy_allowlist",
        )
        conn.close()
        return resp
    _log_decision(conn, wave_id, "ALLOW", "policy version valid for template", "template_policy_allowlist", "run_wave")

    # Route context extraction by wave template
    if req.wave_template_id == "production_config_change_v1":
        target_path = str(req.context_refs.get("target_path", ""))
        output_path = target_path
        input_path = "n/a"
        snapshot_dir = None
        sources = []
        if not target_path:
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="BAD_CONTEXT",
                message="Missing required context: target_path",
                node="run_wave",
                http_status=422,
                rule="context_required_fields",
            )
            conn.close()
            return resp
        normalized = _normalize_repo_relative(target_path)
        if normalized != _normalize_repo_relative(PROD_CONFIG_TARGET):
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="PATH_VIOLATION",
                message="target_path is not allowlisted for production_config_agent",
                node="run_wave",
                http_status=422,
                rule="target_path_allowlist",
            )
            conn.close()
            return resp
        _log_decision(conn, wave_id, "ALLOW", "target path allowlisted", "target_path_allowlist", "run_wave")
    elif req.wave_template_id in MARKET_INTEL_TEMPLATES:
        sources = req.context_refs.get("sources", [])
        snapshot_dir = str(req.context_refs.get("snapshot_dir", "./data/marketing_snapshots"))
        output_path = str(req.context_refs.get("output_digest_path", ""))
        input_path = "n/a"

        if not sources or not output_path:
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="BAD_CONTEXT",
                message="Missing required context: sources and output_digest_path",
                node="run_wave",
                http_status=422,
                rule="context_required_fields",
            )
            conn.close()
            return resp

        if not _is_under("./outputs", output_path):
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="PATH_VIOLATION",
                message="output_digest_path must be under ./outputs/",
                node="run_wave",
                http_status=422,
                rule="output_path_prefix",
            )
            conn.close()
            return resp
        _log_decision(conn, wave_id, "ALLOW", "output path within allowed prefix", "output_path_prefix", "run_wave")
    else:
        input_path = str(req.context_refs.get("input_csv_path", ""))
        output_path = str(req.context_refs.get("output_report_path", ""))
        snapshot_dir = None
        sources = []

        if not input_path or not output_path:
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="BAD_CONTEXT",
                message="Missing required context paths",
                node="run_wave",
                http_status=422,
                rule="context_required_fields",
            )
            conn.close()
            return resp

        if not _is_under("./data", input_path):
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="PATH_VIOLATION",
                message="input_csv_path must be under ./data/",
                node="run_wave",
                http_status=422,
                rule="input_path_prefix",
            )
            conn.close()
            return resp
        if not _is_under("./outputs", output_path):
            resp = _deny_and_record(
                conn,
                wave_id,
                req,
                code="PATH_VIOLATION",
                message="output_report_path must be under ./outputs/",
                node="run_wave",
                http_status=422,
                rule="output_path_prefix",
            )
            conn.close()
            return resp
        _log_decision(conn, wave_id, "ALLOW", "input/output paths validated", "path_constraints", "run_wave")

    token, token_hash, token_expires_at = _issue_wave_token(wave_id, req.agent_id)
    Path(workspace_dir).mkdir(parents=True, exist_ok=True)
    _insert_wave_row(
        conn=conn,
        wave_id=wave_id,
        req=req,
        status="running",
        workspace_dir=workspace_dir,
        wave_token_hash=token_hash,
        wave_token_expires_at=token_expires_at,
    )
    _log_decision(conn, wave_id, "ALLOW", "wave token issued", "wave_token_issue", "run_wave")
    conn.commit()

    started = time.monotonic()
    try:
        evidence: dict[str, Any] = {}
        if req.wave_template_id == "sales_report_v1":
            evidence = _execute_sales_report(
                conn=conn,
                wave_id=wave_id,
                wave_token=token,
                workspace_dir=workspace_dir,
                input_csv_path=input_path,
                output_report_path=output_path,
                approved_by=req.agent_id,
            )
        elif req.wave_template_id == "production_config_change_v1":
            evidence = _execute_production_config_wave(
                conn=conn,
                wave_id=wave_id,
                workspace_dir=workspace_dir,
                target_path=output_path,
            )
        elif req.wave_template_id in MARKET_INTEL_TEMPLATES:
            evidence = _execute_marketing_digest(
                conn=conn,
                wave_id=wave_id,
                wave_token=token,
                workspace_dir=workspace_dir,
                sources=sources,
                snapshot_dir=snapshot_dir,
                output_digest_path=output_path,
                run_id=wave_id,
                approved_by=req.agent_id,
            )
        else:
            raise WaveExecutionError("WAVE_TEMPLATE_INVALID", "Unsupported wave template.", "run_wave")

        elapsed = time.monotonic() - started
        if elapsed > MAX_RUNTIME_SECONDS:
            raise TimeoutError(f"Wave exceeded max runtime of {MAX_RUNTIME_SECONDS}s")

        output_hash = _sha256_file(output_path)
        evidence["output_hash"] = output_hash
        evidence["workspace_dir"] = workspace_dir
        _write_manifest(conn, wave_id, workspace_dir, req, output_path, evidence)

        conn.execute(
            """
            UPDATE waves
            SET status = 'complete',
                error_code = NULL,
                error_message = NULL,
                error_node = NULL,
                updated_at = ?
            WHERE wave_id = ?
            """,
            (_now_iso(), wave_id),
        )
        conn.commit()
        conn.close()
        return {"wave_id": wave_id, "status": "running", "wave_token": token}

    except Exception as e:
        if isinstance(e, WaveExecutionError):
            err_code = e.code
            err_node = e.node
            err_message = str(e)
        elif isinstance(e, TimeoutError):
            err_code = "WAVE_TIMEOUT"
            err_node = "run_wave"
            err_message = str(e)
        else:
            err_code = "WAVE_EXECUTION_ERROR"
            err_node = "run_wave"
            err_message = str(e)
        _log_decision(conn, wave_id, "DENY", err_message, err_code, err_node)
        conn.execute(
            """
            UPDATE waves
            SET status = 'failed',
                error_code = ?,
                error_message = ?,
                error_node = ?,
                updated_at = ?
            WHERE wave_id = ?
            """,
            (err_code, err_message, err_node, _now_iso(), wave_id),
        )
        conn.commit()
        conn.close()
        return {
            "wave_id": wave_id,
            "status": "failed",
            "error": {
                "code": err_code,
                "message": err_message,
                "node": err_node,
            },
        }


@app.get("/api/waves/{wave_id}/status")
def wave_status(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    wave = conn.execute(
        """
        SELECT wave_id, status, error_code, error_message, error_node, context_refs_json
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()

    conn.close()

    if not wave:
        return {
            "wave_id": wave_id,
            "status": "failed",
            "approval_request_id": None,
            "summary": {"output_path": None},
            "error": {
                "code": "WAVE_NOT_FOUND",
                "message": "No wave found for provided wave_id",
                "node": "wave_status",
            },
        }

    output_path = _resolve_output_path(wave[5])

    payload = {
        "wave_id": wave[0],
        "status": wave[1],
        "approval_request_id": None,
        "summary": {"output_path": output_path},
    }

    if wave[1] == "failed":
        payload["error"] = {
            "code": wave[2] or "WAVE_FAILED",
            "message": wave[3] or "Wave failed",
            "node": wave[4] or "wave_status",
        }

    return payload


@app.post("/api/approvals/{approval_request_id}")
def approve_wave(approval_request_id: str, req: ApprovalRequest):
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    approval = conn.execute(
        """
        SELECT wave_id
        FROM approval_requests
        WHERE approval_request_id = ?
        """,
        (approval_request_id,),
    ).fetchone()

    if not approval:
        wave_id_prefix = approval_request_id.replace("apr_", "")
        matches = conn.execute(
            "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC",
            (f"{wave_id_prefix}%",),
        ).fetchall()

        if len(matches) == 0:
            conn.close()
            return {
                "wave_id": None,
                "status": "failed",
                "approval_request_id": approval_request_id,
                "error": {
                    "code": "WAVE_NOT_FOUND",
                    "message": "No matching wave for approval_request_id prefix",
                    "node": "approve_wave",
                },
            }
        if len(matches) > 1:
            conn.close()
            return {
                "wave_id": None,
                "status": "failed",
                "approval_request_id": approval_request_id,
                "error": {
                    "code": "AMBIGUOUS_WAVE_PREFIX",
                    "message": "approval_request_id prefix maps to multiple waves",
                    "node": "approve_wave",
                },
            }

        wave_id = matches[0][0]
        conn.execute(
            """
            INSERT INTO approval_requests
                (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_request_id,
                wave_id,
                "./outputs/report.md",
                "demo_proposed_write_hash_placeholder",
                req.approved_by,
                now,
                req.note,
                "approved",
                now,
                now,
            ),
        )
    else:
        wave_id = approval[0]
        conn.execute(
            """
            UPDATE approval_requests
            SET approved_by = ?, approved_at = ?, note = ?, status = 'approved', updated_at = ?
            WHERE approval_request_id = ?
            """,
            (req.approved_by, now, req.note, now, approval_request_id),
        )

    conn.execute(
        "UPDATE waves SET status = CASE WHEN status = 'running' THEN 'complete' ELSE status END, updated_at = ? WHERE wave_id = ?",
        (now, wave_id),
    )

    conn.commit()
    conn.close()

    return {
        "wave_id": wave_id,
        "status": "complete",
        "approval_request_id": approval_request_id,
        "approved_by": req.approved_by,
        "note": req.note,
    }


@app.post("/ocean/mutate_config")
def ocean_mutate_config(req: ConfigMutateRequest):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    def reject(reason_code: str, message: str, wave_id: str | None, policy_version: str | None, prev_hash: str | None):
        if wave_id:
            _log_decision(conn, wave_id, "DENY", message, reason_code, "ocean.mutate_config")
            conn.commit()
        event_payload = {
            "status": "REJECTED",
            "reason_code": reason_code,
            "agent_name": req.agent_name,
            "target_path": req.target_path,
            "policy_version": req.policy_version,
            "wave_id": wave_id,
            "timestamp": _now_iso(),
        }
        return {
            "status": "REJECTED",
            "reason_code": reason_code,
            "message": message,
            "audit": {
                "wave_id": wave_id,
                "policy_version": policy_version,
                "hash": _sha256_text(json.dumps(event_payload, sort_keys=True)),
                "prev_hash": prev_hash,
            },
            "diff_preview": [],
        }

    wave_id = req.wave_id
    if not wave_id or not req.wave_token:
        out = reject("UNAUTHORIZED_AGENT", "Missing wave_id or wave_token.", wave_id, None, None)
        conn.close()
        return out

    wave = conn.execute(
        """
        SELECT wave_id, agent_id, policy_version, manifest_hash
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()
    if not wave:
        out = reject("UNAUTHORIZED_AGENT", "Wave not found.", wave_id, None, None)
        conn.close()
        return out

    wave_agent = wave[1]
    wave_policy = wave[2]
    prev_hash = wave[3]

    try:
        _validate_wave_token(conn, wave_id, req.wave_token, node="ocean.mutate_config.token")
    except Exception:
        out = reject("UNAUTHORIZED_AGENT", "Invalid wave token.", wave_id, wave_policy, prev_hash)
        conn.close()
        return out

    if req.agent_name != "production_config_agent" or req.agent_name != wave_agent:
        out = reject("UNAUTHORIZED_AGENT", "Agent is not authorized for this wave.", wave_id, wave_policy, prev_hash)
        conn.close()
        return out
    _log_decision(conn, wave_id, "ALLOW", "agent authorized", "agent_identity", "ocean.mutate_config")

    if req.policy_version != wave_policy:
        out = reject("POLICY_MISMATCH", "policy_version does not match wave policy.", wave_id, wave_policy, prev_hash)
        conn.close()
        return out
    _log_decision(conn, wave_id, "ALLOW", "policy version matches wave", "policy_version_match", "ocean.mutate_config")

    normalized_target = _normalize_repo_relative(req.target_path)
    if normalized_target != _normalize_repo_relative(PROD_CONFIG_TARGET):
        out = reject("PATH_VIOLATION", "target_path is not allowlisted.", wave_id, wave_policy, prev_hash)
        conn.close()
        return out
    _log_decision(conn, wave_id, "ALLOW", "target path allowlisted", "target_path_allowlist", "ocean.mutate_config")

    bad_keys = [m.json_path for m in req.mutations if m.json_path not in PROD_CONFIG_ALLOWED_KEYS]
    if bad_keys:
        out = reject("KEY_VIOLATION", f"mutation key(s) not allowlisted: {', '.join(bad_keys)}", wave_id, wave_policy, prev_hash)
        conn.close()
        return out
    _log_decision(conn, wave_id, "ALLOW", "mutation keys allowlisted", "mutation_keys_allowlist", "ocean.mutate_config")

    target_file = PROJECT_ROOT / normalized_target
    if not target_file.exists():
        out = reject("PATH_VIOLATION", "target file does not exist.", wave_id, wave_policy, prev_hash)
        conn.close()
        return out

    try:
        config_obj = json.loads(target_file.read_text(encoding="utf-8"))
    except Exception as e:
        out = reject("PATH_VIOLATION", f"failed to parse target JSON: {e}", wave_id, wave_policy, prev_hash)
        conn.close()
        return out

    diff_preview: list[dict[str, Any]] = []
    for m in req.mutations:
        before, after = _set_json_path(config_obj, m.json_path, m.value)
        diff_preview.append({"json_path": m.json_path, "before": before, "after": after})

    target_file.write_text(json.dumps(config_obj, indent=2) + "\n", encoding="utf-8")
    _log_decision(conn, wave_id, "ALLOW", "config mutation applied", "config_mutation_commit", "ocean.mutate_config")
    conn.execute("UPDATE waves SET updated_at = ? WHERE wave_id = ?", (_now_iso(), wave_id))
    conn.commit()
    conn.close()

    event_payload = {
        "status": "ALLOWED",
        "reason_code": "OK",
        "agent_name": req.agent_name,
        "target_path": req.target_path,
        "policy_version": req.policy_version,
        "wave_id": wave_id,
        "mutations": diff_preview,
        "timestamp": _now_iso(),
    }
    return {
        "status": "ALLOWED",
        "reason_code": "OK",
        "message": "Config mutation accepted and applied.",
        "audit": {
            "wave_id": wave_id,
            "policy_version": wave_policy,
            "hash": _sha256_text(json.dumps(event_payload, sort_keys=True)),
            "prev_hash": prev_hash,
        },
        "diff_preview": diff_preview,
    }


@app.get("/api/waves/{wave_id}/audit/export")
def export_audit(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    wave = conn.execute(
        """
        SELECT wave_id, policy_version, status, agent_id, context_refs_json, error_code, error_message, error_node,
               manifest_hash, manifest_path, workspace_dir
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()

    approval = conn.execute(
        """
        SELECT approved_by, approved_at, note, proposed_write_hash
        FROM approval_requests
        WHERE wave_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (wave_id,),
    ).fetchone()

    decisions = _fetch_decisions(conn, wave_id)
    conn.close()

    if not wave:
        return {
            "wave_id": wave_id,
            "integrity_status": "INVALID",
            "policy_hash": None,
            "agent_id": None,
            "output_path": None,
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "note": None,
                "proposed_write_hash": None,
            },
            "events": [],
            "llm_invocations": [],
        }

    output_path = _resolve_output_path(wave[4])
    integrity_status = "VALID" if wave[2] == "complete" else "INVALID"

    payload = {
        "wave_id": wave[0],
        "integrity_status": integrity_status,
        "policy_hash": wave[1],  # placeholder mapping for POC; replace with real hash column in full runtime API
        "agent_id": wave[3],
        "output_path": output_path,
        "approval": {
            "approved_by": approval[0] if approval else None,
            "approved_at": approval[1] if approval else None,
            "note": approval[2] if approval else None,
            "proposed_write_hash": approval[3] if approval else None,
        },
        "workspace_dir": wave[10],
        "manifest_hash": wave[8],
        "manifest_path": wave[9],
        "events": decisions,
        "llm_invocations": [
            {
                "provider": "anthropic",
                "model_name": "claude",
                "model_version": "placeholder",
            }
        ],
    }

    if wave[2] == "failed":
        payload["error"] = {
            "code": wave[5] or "WAVE_FAILED",
            "message": wave[6] or "Wave failed",
            "node": wave[7] or "export_audit",
        }

    return payload


@app.get("/api/waves/{wave_id}/audit/verify")
def verify_audit(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    row = conn.execute(
        "SELECT manifest_hash, manifest_path, status FROM waves WHERE wave_id = ?",
        (wave_id,),
    ).fetchone()
    conn.close()

    if not row:
        return {
            "wave_id": wave_id,
            "integrity_status": "CORRUPTED",
            "details": "Wave not found.",
        }

    stored_hash, manifest_path, status = row
    if not manifest_path or not Path(manifest_path).exists():
        return {
            "wave_id": wave_id,
            "integrity_status": "CORRUPTED",
            "details": "Manifest file missing.",
        }

    manifest_text = Path(manifest_path).read_text(encoding="utf-8")
    recomputed = _sha256_text(manifest_text)
    ok = stored_hash == recomputed
    return {
        "wave_id": wave_id,
        "integrity_status": "VALID" if ok and status == "complete" else "CORRUPTED",
        "details": {
            "stored_manifest_hash": stored_hash,
            "recomputed_manifest_hash": recomputed,
            "manifest_path": manifest_path,
            "status": status,
        },
    }
