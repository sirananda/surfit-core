"""
SurFit V1 — Execution Logger (SQLite)
One table, one writer function. No ORM.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from models import LogEntry

DEFAULT_DB_PATH = Path("surfit_runs.db")

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

def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create DB + table if needed. Returns connection."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    _ensure_runs_columns(conn)
    conn.commit()
    return conn


def write_log(conn: sqlite3.Connection, entry: LogEntry) -> None:
    """Insert one log row."""
    conn.execute(
        """
        INSERT INTO execution_log
            (timestamp_iso, run_id, saw_id, node_id, tool_name, decision, latency_ms, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.timestamp_iso,
            entry.run_id,
            entry.saw_id,
            entry.node_id,
            entry.tool_name,
            entry.decision,
            entry.latency_ms,
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
