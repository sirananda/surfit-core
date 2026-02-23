import os
import sqlite3
from pathlib import Path

from engine import run_saw
from logger import init_db, verify_run_integrity, get_run_logs
from models import RunContext
from app import BOARD_METRICS_SPEC  # reuse existing spec


TEST_DB = Path("tamper_test.db")


def main() -> int:
    if TEST_DB.exists():
        TEST_DB.unlink()

    conn = init_db(TEST_DB)

    ctx = RunContext(
        run_id="tamper_test_run_001",
        saw_id=BOARD_METRICS_SPEC["saw_id"],
        state={
            "_approval_granted": True,
            "_approval_wait_ms": 500,
            "_approved_by": "tamper.test@surfit.ai",
            "_approval_note": "tamper integrity test",
        },
    )

    result = run_saw(BOARD_METRICS_SPEC, ctx, conn)
    if result.status != "completed":
        print(f"FAIL: baseline run not completed (status={result.status})")
        return 1

    before = verify_run_integrity(conn, ctx.run_id)
    if not before.get("valid"):
        print(f"FAIL: integrity should pass before tamper: {before}")
        return 1

    rows = conn.execute(
        """
        SELECT id, latency_ms
        FROM execution_log
        WHERE run_id = ?
        ORDER BY timestamp_iso, id
        """,
        (ctx.run_id,),
    ).fetchall()

    if len(rows) < 4:
        print("FAIL: not enough rows to perform deterministic tamper")
        return 1

    # Mutate the 4th event (index 3): latency_ms is part of hash canonical payload.
    target_id, target_latency = rows[3]
    conn.execute(
        "UPDATE execution_log SET latency_ms = ? WHERE id = ?",
        (float(target_latency) + 1.0, target_id),
    )
    conn.commit()

    after = verify_run_integrity(conn, ctx.run_id)
    if after.get("valid"):
        print(f"FAIL: integrity should fail after tamper: {after}")
        return 1

    if after.get("first_mismatch_index") is None:
        print(f"FAIL: expected mismatch index, got: {after}")
        return 1

    if after.get("expected_hash") == after.get("found_hash"):
        print(f"FAIL: expected/found hash should differ: {after}")
        return 1

    print("PASS")
    print(f"Run ID: {ctx.run_id}")
    print(f"Mismatch index: {after.get('first_mismatch_index')}")
    print(f"Expected hash: {after.get('expected_hash')}")
    print(f"Found hash: {after.get('found_hash')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

