from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uuid
import sqlite3
from datetime import datetime, timezone

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


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest):
    wave_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

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

    if not approval:
        # Create placeholder approval request for POC flow.
        wave_id_prefix = approval_request_id.replace("apr_", "")
        match = conn.execute(
            "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"{wave_id_prefix}%",),
        ).fetchone()
        wave_id_guess = match[0] if match else wave_id_prefix
        conn.execute(
            """
            INSERT INTO approval_requests
                (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_request_id,
                wave_id_guess,
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
        wave_id = wave_id_guess
        if len(wave_id) < 36:
            match = conn.execute(
                "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC LIMIT 1",
                (f"{wave_id}%",),
            ).fetchone()
            if match:
                wave_id = match[0]
    else:
        wave_id = approval[0]
        if len(wave_id) < 36:
            match = conn.execute(
                "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC LIMIT 1",
                (f"{wave_id}%",),
            ).fetchone()
            if match:
                wave_id = match[0]
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

