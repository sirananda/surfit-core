"""
SurFit V1 — Execution Logger (SQLite)
One table, one writer function. No ORM.
"""

from __future__ import annotations

import sqlite3
import json
import hashlib
from pathlib import Path

from models import LogEntry

DEFAULT_DB_PATH = Path("surfit_runs.db")

def canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip()


def normalized_payload_hash(value: str) -> str:
    return sha256_hex(_normalize_text(value))


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS execution_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_iso   TEXT    NOT NULL,
    run_id          TEXT    NOT NULL,
    saw_id          TEXT    NOT NULL,
    node_id         TEXT    NOT NULL,
    tool_name       TEXT    NOT NULL DEFAULT '',
    decision        TEXT    NOT NULL CHECK(decision IN ('allow', 'deny', '')),
    latency_ms      REAL    NOT NULL DEFAULT 0.0,
    prev_hash       TEXT    NOT NULL DEFAULT 'GENESIS',
    event_hash      TEXT    NOT NULL DEFAULT '',
    error           TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_id ON execution_log(run_id);
CREATE INDEX IF NOT EXISTS idx_saw_id ON execution_log(saw_id);

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
);

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_saw_id ON runs(saw_id);
CREATE TABLE IF NOT EXISTS llm_invocations (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                       TEXT    NOT NULL,
    node_id                      TEXT    NOT NULL,
    invoked_at                   TEXT    NOT NULL,
    provider                     TEXT,
    model_name                   TEXT,
    model_version                TEXT,
    temperature                  REAL,
    max_tokens                   INTEGER,
    raw_tool_input_hash          TEXT,
    sanitized_prompt_input_hash  TEXT,
    llm_output_text_hash         TEXT,
    raw_tool_input_preview       TEXT,
    llm_output_preview           TEXT
);

CREATE INDEX IF NOT EXISTS idx_llm_run_id ON llm_invocations(run_id);
CREATE INDEX IF NOT EXISTS idx_llm_node_id ON llm_invocations(node_id);
CREATE INDEX IF NOT EXISTS idx_llm_invoked_at ON llm_invocations(invoked_at);

"""

def _ensure_runs_columns(conn: sqlite3.Connection) -> None:
    """Backfill columns on legacy DBs that already have runs table."""
    cols = {
        row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()
    }
    required = {
        "policy_hash": "TEXT",
        "policy_version": "TEXT",
        "policy_snapshot": "TEXT",
        "approved_by": "TEXT",
        "approved_at": "TEXT",
        "approval_note": "TEXT",
    }
    for col, sql_type in required.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE runs ADD COLUMN {col} {sql_type}")
def _ensure_execution_log_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(execution_log)").fetchall()}
    required = {
        "prev_hash": "TEXT NOT NULL DEFAULT 'GENESIS'",
        "event_hash": "TEXT NOT NULL DEFAULT ''",
    }
    for col, sql_type in required.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE execution_log ADD COLUMN {col} {sql_type}")

def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create DB + table if needed. Returns connection."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    _ensure_runs_columns(conn)
    _ensure_execution_log_columns(conn)
    conn.commit()
    return conn


def write_log(conn: sqlite3.Connection, entry: LogEntry) -> None:
    """Insert one log row with per-run hash chain."""
    prev_row = conn.execute(
        """
        SELECT event_hash
        FROM execution_log
        WHERE run_id = ?
        ORDER BY timestamp_iso DESC, id DESC
        LIMIT 1
        """,
        (entry.run_id,),
    ).fetchone()

    prev_hash = prev_row[0] if prev_row and prev_row[0] else "GENESIS"

    canonical_event = canonical_json(
        {
            "run_id": entry.run_id,
            "node_id": entry.node_id,
            "tool_name": entry.tool_name,
            "decision": entry.decision,
	    "latency_ms": float(entry.latency_ms),
            "error": entry.error or "",
            "timestamp": entry.timestamp_iso,
        }
    )
    event_hash = sha256_hex(prev_hash + canonical_event)

    conn.execute(
        """
        INSERT INTO execution_log
            (timestamp_iso, run_id, saw_id, node_id, tool_name, decision, latency_ms, prev_hash, event_hash, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.timestamp_iso,
            entry.run_id,
            entry.saw_id,
            entry.node_id,
            entry.tool_name,
            entry.decision,
            entry.latency_ms,
            prev_hash,
            event_hash,
            entry.error,
        ),
    )
    conn.commit()

def upsert_run_start(
    conn: sqlite3.Connection,
    run_id: str,
    saw_id: str,
    started_at: str,
    status: str,
    policy_hash: str,
    policy_version: str,
    policy_snapshot: str,
) -> None:
    conn.execute(
        """
        INSERT INTO runs
            (run_id, saw_id, started_at, status, policy_hash, policy_version, policy_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            saw_id = excluded.saw_id,
            started_at = excluded.started_at,
            status = excluded.status,
            policy_hash = excluded.policy_hash,
            policy_version = excluded.policy_version,
            policy_snapshot = excluded.policy_snapshot
        """,
        (run_id, saw_id, started_at, status, policy_hash, policy_version, policy_snapshot),
    )
    conn.commit()


def update_run_approval(
    conn: sqlite3.Connection,
    run_id: str,
    approved_by: str | None,
    approved_at: str | None,
    approval_note: str | None,
) -> None:
    conn.execute(
        """
        UPDATE runs
        SET approved_by = ?, approved_at = ?, approval_note = ?
        WHERE run_id = ?
        """,
        (approved_by, approved_at, approval_note, run_id),
    )
    conn.commit()


def update_run_status(conn: sqlite3.Connection, run_id: str, status: str) -> None:
    conn.execute(
        "UPDATE runs SET status = ? WHERE run_id = ?",
        (status, run_id),
    )
    conn.commit()


def get_run_record(conn: sqlite3.Connection, run_id: str) -> dict | None:
    cur = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

def write_llm_invocation(
    conn: sqlite3.Connection,
    run_id: str,
    node_id: str,
    invoked_at: str,
    provider: str | None,
    model_name: str | None,
    model_version: str | None,
    temperature: float | None,
    max_tokens: int | None,
    raw_tool_input: dict,
    sanitized_prompt_input: dict,
    llm_output_text: str,
) -> None:
    raw_json = canonical_json(raw_tool_input or {})
    sanitized_json = canonical_json(sanitized_prompt_input or {})
    output_text = llm_output_text or ""

    raw_hash = normalized_payload_hash(raw_json)
    sanitized_hash = normalized_payload_hash(sanitized_json)
    output_hash = normalized_payload_hash(output_text)

    conn.execute(
        """
        INSERT INTO llm_invocations
            (run_id, node_id, invoked_at, provider, model_name, model_version, temperature, max_tokens,
             raw_tool_input_hash, sanitized_prompt_input_hash, llm_output_text_hash,
             raw_tool_input_preview, llm_output_preview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            node_id,
            invoked_at,
            provider,
            model_name,
            model_version,
            temperature,
            max_tokens,
            raw_hash,
            sanitized_hash,
            output_hash,
            _normalize_text(raw_json)[:300],
            _normalize_text(output_text)[:300],
        ),
    )
    conn.commit()


def get_llm_invocations(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    cur = conn.execute(
        "SELECT * FROM llm_invocations WHERE run_id = ? ORDER BY invoked_at, id",
        (run_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def verify_run_integrity(conn: sqlite3.Connection, run_id: str) -> dict:
    cur = conn.execute(
        """
        SELECT id, timestamp_iso, run_id, node_id, tool_name, decision, latency_ms, error, prev_hash, event_hash
        FROM execution_log
        WHERE run_id = ?
        ORDER BY timestamp_iso, id
        """,
        (run_id,),
    )
    rows = cur.fetchall()
    if not rows:
        return {
            "valid": True,
            "first_mismatch_index": None,
            "expected_hash": None,
            "found_hash": None,
        }

    prev = "GENESIS"
    for idx, row in enumerate(rows):
        (
            _id,
            timestamp_iso,
            row_run_id,
            node_id,
            tool_name,
            decision,
            latency_ms,
            error,
            stored_prev,
            stored_event,
        ) = row

        canonical_event = canonical_json(
            {
                "run_id": row_run_id,
                "node_id": node_id,
                "tool_name": tool_name,
                "decision": decision,
		"latency_ms": float(latency_ms),
                "error": error or "",
                "timestamp": timestamp_iso,
            }
        )
        expected_event = sha256_hex(prev + canonical_event)

        if stored_prev != prev or stored_event != expected_event:
            return {
                "valid": False,
                "first_mismatch_index": idx,
                "expected_hash": expected_event,
                "found_hash": stored_event,
            }

        prev = stored_event

    return {
        "valid": True,
        "first_mismatch_index": None,
        "expected_hash": None,
        "found_hash": None,
    }


def get_run_logs(
    conn: sqlite3.Connection, run_id: str
) -> list[dict]:
    """Fetch all log entries for a run, ordered by timestamp."""
    cursor = conn.execute(
        "SELECT * FROM execution_log WHERE run_id = ? ORDER BY timestamp_iso",
        (run_id,),
    )
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_cycle_time_breakdown(
    conn: sqlite3.Connection, run_id: str
) -> dict:
    """Compute system_time_ms and human_wait_time_ms for a run."""
    rows = get_run_logs(conn, run_id)
    system_ms = 0.0
    human_ms = 0.0
    for row in rows:
        if row["node_id"] == "n_approval":
            human_ms += row["latency_ms"]
        else:
            system_ms += row["latency_ms"]
    return {
        "run_id": run_id,
        "system_time_ms": round(system_ms, 2),
        "human_wait_time_ms": round(human_ms, 2),
        "total_ms": round(system_ms + human_ms, 2),
    }
