from pathlib import Path

from engine import run_saw
from logger import init_db, verify_run_integrity
from models import RunContext
from app import BOARD_METRICS_SPEC


def test_tamper_detection():
    test_db = Path("tamper_test_pytest.db")
    if test_db.exists():
        test_db.unlink()

    conn = init_db(test_db)

    ctx = RunContext(
        run_id="tamper_test_run_pytest_001",
        saw_id=BOARD_METRICS_SPEC["saw_id"],
        state={
            "_approval_granted": True,
            "_approval_wait_ms": 500,
            "_approved_by": "tamper.test@surfit.ai",
            "_approval_note": "tamper pytest test",
        },
    )

    result = run_saw(BOARD_METRICS_SPEC, ctx, conn)
    assert result.status == "completed"

    before = verify_run_integrity(conn, ctx.run_id)
    assert before["valid"] is True

    rows = conn.execute(
        """
        SELECT id, latency_ms
        FROM execution_log
        WHERE run_id = ?
        ORDER BY timestamp_iso, id
        """,
        (ctx.run_id,),
    ).fetchall()

    assert len(rows) >= 4
    target_id, target_latency = rows[3]

    conn.execute(
        "UPDATE execution_log SET latency_ms = ? WHERE id = ?",
        (float(target_latency) + 1.0, target_id),
    )
    conn.commit()

    after = verify_run_integrity(conn, ctx.run_id)
    assert after["valid"] is False
    assert after["first_mismatch_index"] is not None
    assert after["expected_hash"] != after["found_hash"]

