from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "/tmp/surfit_runs.db"


app = FastAPI(title="SurFit Runtime API", version="m13-poc")


class WaveRunRequest(BaseModel):
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
            wave_template_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            intent TEXT,
            context_refs_json TEXT,
            status TEXT NOT NULL,
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
    conn.commit()

def _is_under(base: str, target: str) -> bool:
    base_path = Path(base).resolve()
    target_path = Path(target).resolve()
    try:
        target_path.relative_to(base_path)
        return True
    except ValueError:
        return False


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest):
    wave_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    input_path = str(req.context_refs.get("input_csv_path", ""))
    output_path = str(req.context_refs.get("output_report_path", ""))

    if not input_path or not output_path:
        return {"wave_id": None, "status": "failed", "error": {"code": "BAD_CONTEXT", "message": "Missing required context paths", "node": "run_wave"}}

    if not _is_under("./data", input_path):
        return {"wave_id": None, "status": "failed", "error": {"code": "INPUT_PATH_VIOLATION", "message": "input_csv_path must be under ./data/", "node": "run_wave"}}

    if not _is_under("./outputs", output_path):
        return {"wave_id": None, "status": "failed", "error": {"code": "OUTPUT_PATH_VIOLATION", "message": "output_report_path must be under ./outputs/", "node": "run_wave"}}


    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    conn.execute(
        """
        INSERT INTO waves
            (wave_id, wave_template_id, policy_version, intent, context_refs_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            wave_id,
            req.wave_template_id,
            req.policy_version,
            req.intent,
            str(req.context_refs),
            "running",
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "wave_id": wave_id,
        "status": "running",
    }

@app.get("/api/waves/{wave_id}/status")
def wave_status(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    wave = conn.execute(
        "SELECT wave_id, status FROM waves WHERE wave_id = ?",
        (wave_id,),
    ).fetchone()

    if not wave:
        conn.close()
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

    approval = conn.execute(
        """
        SELECT approval_request_id
        FROM approval_requests
        WHERE wave_id = ? AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (wave_id,),
    ).fetchone()

    conn.close()

    return {
        "wave_id": wave_id,
        "status": wave[1],
        "approval_request_id": approval[0] if approval else None,
        "summary": {"output_path": "./outputs/report.md"},
    }

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

    def resolve_wave_id(prefix_or_id: str):
        if len(prefix_or_id) >= 36:
            return prefix_or_id, None

        matches = conn.execute(
            "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC",
            (f"{prefix_or_id}%",),
        ).fetchall()

        if len(matches) == 1:
            return matches[0][0], None
        if len(matches) > 1:
            return None, {
                "wave_id": None,
                "status": "failed",
                "approval_request_id": approval_request_id,
                "error": {
                    "code": "AMBIGUOUS_WAVE_PREFIX",
                    "message": "approval_request_id prefix maps to multiple waves",
                    "node": "approve_wave",
                },
            }
        return prefix_or_id, None

    if not approval:
        wave_id_prefix = approval_request_id.replace("apr_", "")
        wave_id, err = resolve_wave_id(wave_id_prefix)
        if err:
            conn.close()
            return err

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
        wave_id, err = resolve_wave_id(approval[0])
        if err:
            conn.close()
            return err

        conn.execute(
            """
            UPDATE approval_requests
            SET approved_by = ?, approved_at = ?, note = ?, status = 'approved', updated_at = ?
            WHERE approval_request_id = ?
            """,
            (req.approved_by, now, req.note, now, approval_request_id),
        )

    conn.execute(
        "UPDATE waves SET status = 'complete', updated_at = ? WHERE wave_id = ?",
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
        SELECT wave_id, policy_version, status
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()

    approval = conn.execute(
        """
        SELECT approved_by, approved_at, note, proposed_write_hash
        FROM approval_requests
        WHERE wave_id = ? OR wave_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (wave_id, wave_id[:8]),
    ).fetchone()

    conn.close()

    if not wave:
        return {
            "wave_id": wave_id,
            "integrity_status": "INVALID",
            "policy_hash": None,
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "note": None,
                "proposed_write_hash": None,
            },
            "events": [],
            "llm_invocations": [],
        }

    integrity_status = "VALID" if wave[2] in ("complete", "running", "needs_approval") else "INVALID"

    return {
        "wave_id": wave[0],
        "integrity_status": integrity_status,
        "policy_hash": wave[1],  # placeholder mapping for POC; replace with real hash column in full runtime API
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
            {"node": "approval_gate", "status": "approved" if approval else "pending"},
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

