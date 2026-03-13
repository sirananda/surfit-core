from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surfit.runtime.wave_lifecycle_store import WaveInsertPayload, WaveLifecycleStore


def _store() -> WaveLifecycleStore:
    return WaveLifecycleStore(
        default_tenant_id="tenant_demo",
        now_iso=lambda: "2026-03-13T00:00:00+00:00",
        sha256_text=lambda text: __import__("hashlib").sha256(text.encode("utf-8")).hexdigest(),
        canonicalize_policy_manifest=lambda payload: json.dumps(payload, sort_keys=True, separators=(",", ":")),
    )


class WaveLifecycleStoreTests(unittest.TestCase):
    def test_wave_start_and_status_transition(self):
        store = _store()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runs.db"
            conn = sqlite3.connect(str(db))
            store.ensure_schema(conn)
            store.insert_wave(
                conn,
                WaveInsertPayload(
                    wave_id="wave-1",
                    tenant_id="tenant_a",
                    agent_id="agent",
                    wave_template_id="sales_report_v1",
                    policy_version="sales_report_policy_v1",
                    intent="test",
                    context_refs={"output_report_path": "./outputs/report.md"},
                    status="running",
                ),
            )
            conn.commit()
            row = conn.execute("SELECT status FROM waves WHERE wave_id = ?", ("wave-1",)).fetchone()
            self.assertEqual(row[0], "running")
            store.update_wave_status(
                conn,
                wave_id="wave-1",
                status="complete",
                error_code=None,
                error_message=None,
                error_node=None,
            )
            conn.commit()
            row2 = conn.execute("SELECT status FROM waves WHERE wave_id = ?", ("wave-1",)).fetchone()
            self.assertEqual(row2[0], "complete")
            conn.close()

    def test_decision_chain_integrity(self):
        store = _store()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runs.db"
            conn = sqlite3.connect(str(db))
            store.ensure_schema(conn)
            store.insert_wave(
                conn,
                WaveInsertPayload(
                    wave_id="wave-2",
                    tenant_id="tenant_a",
                    agent_id="agent",
                    wave_template_id="sales_report_v1",
                    policy_version="sales_report_policy_v1",
                    intent="test",
                    context_refs={},
                    status="running",
                ),
            )
            store.log_decision(
                conn,
                wave_id="wave-2",
                decision="ALLOW",
                reason="ok",
                rule="r1",
                node="n1",
                tenant_id="tenant_a",
            )
            store.log_decision(
                conn,
                wave_id="wave-2",
                decision="DENY",
                reason="blocked",
                rule="r2",
                node="n2",
                tenant_id="tenant_a",
            )
            conn.commit()
            verify = store.verify_decision_chain(conn, "wave-2")
            self.assertTrue(verify["valid"])
            self.assertEqual(verify["decision_count"], 2)
            conn.close()

    def test_manifest_write_and_output_resolution(self):
        store = _store()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runs.db"
            workspace = Path(td) / "runs" / "wave-3"
            workspace.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db))
            store.ensure_schema(conn)
            store.insert_wave(
                conn,
                WaveInsertPayload(
                    wave_id="wave-3",
                    tenant_id="tenant_a",
                    agent_id="agent",
                    wave_template_id="sales_report_v1",
                    policy_version="sales_report_policy_v1",
                    intent="test",
                    context_refs={"output_report_path": "./outputs/report.md"},
                    status="running",
                ),
            )
            manifest_hash, manifest_path = store.write_manifest(
                conn,
                wave_id="wave-3",
                workspace_dir=str(workspace),
                wave_template_id="sales_report_v1",
                policy_version="sales_report_policy_v1",
                intent="test",
                context_refs={"output_report_path": "./outputs/report.md"},
                output_path="./outputs/report.md",
                evidence={"ok": True},
                agent_id="agent",
            )
            conn.commit()
            self.assertTrue(manifest_hash)
            self.assertTrue(Path(manifest_path).exists())
            resolved = store.resolve_output_path(json.dumps({"output_report_path": "./outputs/report.md"}))
            self.assertEqual(resolved, "./outputs/report.md")
            conn.close()


if __name__ == "__main__":
    unittest.main()

