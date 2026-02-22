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
"""


def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create DB + table if needed. Returns connection."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
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
