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
import anthropic
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "/tmp/surfit_runs.db"
MAX_RUNTIME_SECONDS = 30

AGENT_WAVE_ALLOWLIST = {
    "openclaw_poc_agent_v1": {"sales_report_v1"},
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
    _ensure_wave_columns(conn)
    conn.commit()


def _ensure_wave_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(waves)").fetchall()}
    required = {
        "agent_id": "TEXT",
        "error_code": "TEXT",
        "error_message": "TEXT",
        "error_node": "TEXT",
    }
    for col, sql_type in required.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE waves ADD COLUMN {col} {sql_type}")


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
    return refs.get("output_report_path")


def _execute_sales_report(input_csv_path: str, output_report_path: str, approved_by: str) -> None:
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

    _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    _prompt = (
        f"You are a finance analyst. Write a concise 3-sentence sales summary for an executive.\n"
        f"Total rows: {len(rows)}, Total units: {total_units:,.0f}, Total revenue: ${total_revenue:,.2f}\n"
        f"Revenue by region: {str(by_region)}\n"
        f"Highlight the top region, note any underperforming region, end with one forward-looking sentence."
    )
    _msg = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": _prompt}]
    )
    _llm_summary = _msg.content[0].text.strip()

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

    Path(output_report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest):
    wave_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    if not req.agent_id:
        return JSONResponse(
            status_code=403,
            content={
                "code": "AGENT_ID_REQUIRED",
                "message": "agent_id is required",
                "node": "run_wave",
            },
        )

    allowed_templates = AGENT_WAVE_ALLOWLIST.get(req.agent_id, set())
    if req.wave_template_id not in allowed_templates:
        return JSONResponse(
            status_code=403,
            content={
                "code": "AGENT_NOT_AUTHORIZED",
                "message": f"agent_id '{req.agent_id}' is not authorized for wave_template_id '{req.wave_template_id}'",
                "node": "run_wave",
            },
        )

    input_path = str(req.context_refs.get("input_csv_path", ""))
    output_path = str(req.context_refs.get("output_report_path", ""))

    if not input_path or not output_path:
        return {
            "wave_id": None,
            "status": "failed",
            "error": {
                "code": "BAD_CONTEXT",
                "message": "Missing required context paths",
                "node": "run_wave",
            },
        }

    if not _is_under("./data", input_path):
        return {
            "wave_id": None,
            "status": "failed",
            "error": {
                "code": "INPUT_PATH_VIOLATION",
                "message": "input_csv_path must be under ./data/",
                "node": "run_wave",
            },
        }

    if not _is_under("./outputs", output_path):
        return {
            "wave_id": None,
            "status": "failed",
            "error": {
                "code": "OUTPUT_PATH_VIOLATION",
                "message": "output_report_path must be under ./outputs/",
                "node": "run_wave",
            },
        }

    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    conn.execute(
        """
        INSERT INTO waves
            (wave_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            wave_id,
            req.agent_id,
            req.wave_template_id,
            req.policy_version,
            req.intent,
            json.dumps(req.context_refs, sort_keys=True),
            "running",
            now,
            now,
        ),
    )
    conn.commit()

    started = time.monotonic()
    try:
        if req.wave_template_id != "sales_report_v1":
            raise ValueError(f"Unsupported wave_template_id '{req.wave_template_id}'")

        _execute_sales_report(
            input_csv_path=input_path,
            output_report_path=output_path,
            approved_by=req.agent_id,
        )

        elapsed = time.monotonic() - started
        if elapsed > MAX_RUNTIME_SECONDS:
            raise TimeoutError(f"Wave exceeded max runtime of {MAX_RUNTIME_SECONDS}s")

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
            (datetime.now(timezone.utc).isoformat(), wave_id),
        )
        conn.commit()
        conn.close()
        return {"wave_id": wave_id, "status": "running"}

    except Exception as e:
        err_code = "WAVE_TIMEOUT" if isinstance(e, TimeoutError) else "WAVE_EXECUTION_ERROR"
        conn.execute(
            """
            UPDATE waves
            SET status = 'failed',
                error_code = ?,
                error_message = ?,
                error_node = 'run_wave',
                updated_at = ?
            WHERE wave_id = ?
            """,
            (err_code, str(e), datetime.now(timezone.utc).isoformat(), wave_id),
        )
        conn.commit()
        conn.close()
        return {
            "wave_id": wave_id,
            "status": "failed",
            "error": {
                "code": err_code,
                "message": str(e),
                "node": "run_wave",
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


@app.get("/api/waves/{wave_id}/audit/export")
def export_audit(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    wave = conn.execute(
        """
        SELECT wave_id, policy_version, status, agent_id, context_refs_json, error_code, error_message, error_node
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
        "events": [
            {"node": "load_csv", "status": "ok"},
            {"node": "compute_metrics", "status": "ok"},
            {"node": "llm_summary", "status": "ok"},
            {"node": "propose_write_report", "status": "ok"},
            {"node": "approval_gate", "status": "auto_approved"},
            {"node": "commit_write_report", "status": "ok" if wave[2] == "complete" else "pending"},
        ],
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

