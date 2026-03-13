from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable


@dataclass(frozen=True)
class WaveInsertPayload:
    wave_id: str
    tenant_id: str
    agent_id: str | None
    wave_template_id: str
    policy_version: str
    intent: str
    context_refs: dict[str, Any]
    status: str
    workspace_dir: str | None = None
    wave_token_hash: str | None = None
    wave_token_expires_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_node: str | None = None
    policy_manifest_hash: str | None = None
    policy_manifest_version: str | None = None
    policy_manifest_json: str | None = None
    wave_mutation_token: str | None = None
    wave_mutation_token_hash: str | None = None
    wave_mutation_token_expires_at: str | None = None
    wave_mutation_token_payload_json: str | None = None


class WaveLifecycleStore:
    def __init__(
        self,
        *,
        default_tenant_id: str,
        now_iso: Callable[[], str],
        sha256_text: Callable[[str], str],
        canonicalize_policy_manifest: Callable[[dict[str, Any]], str],
    ):
        self.default_tenant_id = default_tenant_id
        self.now_iso = now_iso
        self.sha256_text = sha256_text
        self.canonicalize_policy_manifest = canonicalize_policy_manifest

    def ensure_schema(self, conn: sqlite3.Connection) -> None:
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
                tenant_id TEXT,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                rule TEXT NOT NULL,
                node TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                wave_id TEXT,
                event_type TEXT NOT NULL,
                reason_code TEXT,
                node TEXT,
                status TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._ensure_wave_columns(conn)
        self._ensure_wave_decision_columns(conn)
        self._ensure_api_event_columns(conn)
        conn.commit()

    def log_api_event(
        self,
        conn: sqlite3.Connection,
        *,
        tenant_id: str,
        event_type: str,
        wave_id: str | None = None,
        reason_code: str | None = None,
        node: str | None = None,
        status: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO api_events (tenant_id, wave_id, event_type, reason_code, node, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (tenant_id, wave_id, event_type, reason_code, node, status, self.now_iso()),
        )

    def log_decision(
        self,
        conn: sqlite3.Connection,
        *,
        wave_id: str,
        decision: str,
        reason: str,
        rule: str,
        node: str,
        tenant_id: str | None = None,
    ) -> None:
        created_at = self.now_iso()
        if tenant_id is None:
            wave_row = conn.execute("SELECT tenant_id FROM waves WHERE wave_id = ?", (wave_id,)).fetchone()
            tenant_id = str(wave_row[0]) if wave_row and wave_row[0] else self.default_tenant_id
        last = conn.execute(
            """
            SELECT event_hash
            FROM wave_decisions
            WHERE wave_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (wave_id,),
        ).fetchone()
        prev_hash = last[0] if last else None
        event_payload = {
            "wave_id": wave_id,
            "tenant_id": tenant_id,
            "decision": decision,
            "reason": reason,
            "rule": rule,
            "node": node,
            "created_at": created_at,
            "prev_hash": prev_hash,
        }
        event_hash = self.sha256_text(json.dumps(event_payload, sort_keys=True))
        conn.execute(
            """
            INSERT INTO wave_decisions (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (wave_id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash),
        )

    def fetch_decisions(self, conn: sqlite3.Connection, wave_id: str) -> list[dict[str, str | None]]:
        rows = conn.execute(
            """
            SELECT tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash
            FROM wave_decisions
            WHERE wave_id = ?
            ORDER BY id ASC
            """,
            (wave_id,),
        ).fetchall()
        return [
            {
                "tenant_id": r[0],
                "decision": r[1],
                "reason": r[2],
                "rule": r[3],
                "node": r[4],
                "timestamp": r[5],
                "prev_hash": r[6],
                "event_hash": r[7],
            }
            for r in rows
        ]

    def verify_decision_chain(self, conn: sqlite3.Connection, wave_id: str) -> dict[str, Any]:
        rows = conn.execute(
            """
            SELECT id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash
            FROM wave_decisions
            WHERE wave_id = ?
            ORDER BY id ASC
            """,
            (wave_id,),
        ).fetchall()
        prior_hash = None
        for row in rows:
            _id, tenant_id, decision, reason, rule, node, created_at, prev_hash, event_hash = row
            payload_v2 = {
                "wave_id": wave_id,
                "tenant_id": tenant_id,
                "decision": decision,
                "reason": reason,
                "rule": rule,
                "node": node,
                "created_at": created_at,
                "prev_hash": prev_hash,
            }
            recomputed = self.sha256_text(json.dumps(payload_v2, sort_keys=True))
            if event_hash != recomputed:
                payload_legacy = {
                    "wave_id": wave_id,
                    "decision": decision,
                    "reason": reason,
                    "rule": rule,
                    "node": node,
                    "created_at": created_at,
                    "prev_hash": prev_hash,
                }
                recomputed = self.sha256_text(json.dumps(payload_legacy, sort_keys=True))
            if prev_hash != prior_hash:
                return {
                    "valid": False,
                    "failure": "prev_hash_mismatch",
                    "decision_id": _id,
                    "expected_prev_hash": prior_hash,
                    "found_prev_hash": prev_hash,
                }
            if event_hash != recomputed:
                return {
                    "valid": False,
                    "failure": "event_hash_mismatch",
                    "decision_id": _id,
                    "expected_event_hash": recomputed,
                    "found_event_hash": event_hash,
                }
            prior_hash = event_hash
        return {"valid": True, "decision_count": len(rows), "head_event_hash": prior_hash}

    def verify_policy_manifest(self, policy_manifest_hash: str | None, policy_manifest_json: str | None) -> dict[str, Any]:
        if not policy_manifest_hash or not policy_manifest_json:
            return {
                "valid": False,
                "reason": "missing_policy_manifest_data",
                "recomputed_policy_manifest_hash": None,
                "policy_manifest_payload": None,
            }
        try:
            payload = json.loads(policy_manifest_json)
            canonical = self.canonicalize_policy_manifest(payload)
            recomputed = self.sha256_text(canonical)
            return {
                "valid": recomputed == policy_manifest_hash,
                "reason": None if recomputed == policy_manifest_hash else "policy_manifest_hash_mismatch",
                "recomputed_policy_manifest_hash": recomputed,
                "policy_manifest_payload": payload,
            }
        except Exception as e:
            return {
                "valid": False,
                "reason": f"policy_manifest_json_invalid: {e}",
                "recomputed_policy_manifest_hash": None,
                "policy_manifest_payload": None,
            }

    def insert_wave(self, conn: sqlite3.Connection, payload: WaveInsertPayload) -> None:
        now = self.now_iso()
        conn.execute(
            """
            INSERT INTO waves
                (wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, context_refs_json, status,
                 error_code, error_message, error_node, workspace_dir, wave_token_hash, wave_token_expires_at,
                 policy_manifest_hash, policy_manifest_version, policy_manifest_json,
                 wave_mutation_token, wave_mutation_token_hash, wave_mutation_token_expires_at, wave_mutation_token_payload_json,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.wave_id,
                payload.tenant_id,
                payload.agent_id,
                payload.wave_template_id,
                payload.policy_version,
                payload.intent,
                json.dumps(payload.context_refs, sort_keys=True),
                payload.status,
                payload.error_code,
                payload.error_message,
                payload.error_node,
                payload.workspace_dir,
                payload.wave_token_hash,
                payload.wave_token_expires_at,
                payload.policy_manifest_hash,
                payload.policy_manifest_version,
                payload.policy_manifest_json,
                payload.wave_mutation_token,
                payload.wave_mutation_token_hash,
                payload.wave_mutation_token_expires_at,
                payload.wave_mutation_token_payload_json,
                now,
                now,
            ),
        )

    def update_wave_status(
        self,
        conn: sqlite3.Connection,
        *,
        wave_id: str,
        status: str,
        error_code: str | None,
        error_message: str | None,
        error_node: str | None,
    ) -> None:
        conn.execute(
            """
            UPDATE waves
            SET status = ?, error_code = ?, error_message = ?, error_node = ?, updated_at = ?
            WHERE wave_id = ?
            """,
            (status, error_code, error_message, error_node, self.now_iso(), wave_id),
        )

    def fetch_wave_status_row(self, conn: sqlite3.Connection, wave_id: str) -> tuple[Any, ...] | None:
        return conn.execute(
            """
            SELECT wave_id, status, error_code, error_message, error_node, context_refs_json,
                   wave_mutation_token_expires_at, policy_manifest_hash
            FROM waves
            WHERE wave_id = ?
            """,
            (wave_id,),
        ).fetchone()

    def fetch_approval_wave_id(self, conn: sqlite3.Connection, approval_request_id: str) -> str | None:
        row = conn.execute(
            """
            SELECT wave_id
            FROM approval_requests
            WHERE approval_request_id = ?
            """,
            (approval_request_id,),
        ).fetchone()
        return str(row[0]) if row and row[0] else None

    def find_wave_ids_by_prefix(self, conn: sqlite3.Connection, wave_prefix: str) -> list[str]:
        rows = conn.execute(
            "SELECT wave_id FROM waves WHERE wave_id LIKE ? ORDER BY created_at DESC",
            (f"{wave_prefix}%",),
        ).fetchall()
        return [str(r[0]) for r in rows if r and r[0]]

    def create_approval_record(
        self,
        conn: sqlite3.Connection,
        *,
        approval_request_id: str,
        wave_id: str,
        approved_by: str,
        note: str | None,
        target_write_path: str = "./outputs/report.md",
        proposed_write_hash: str = "demo_proposed_write_hash_placeholder",
    ) -> None:
        now = self.now_iso()
        conn.execute(
            """
            INSERT INTO approval_requests
                (approval_request_id, wave_id, target_write_path, proposed_write_hash, approved_by, approved_at, note, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_request_id,
                wave_id,
                target_write_path,
                proposed_write_hash,
                approved_by,
                now,
                note,
                "approved",
                now,
                now,
            ),
        )

    def update_approval_record(
        self,
        conn: sqlite3.Connection,
        *,
        approval_request_id: str,
        approved_by: str,
        note: str | None,
    ) -> None:
        now = self.now_iso()
        conn.execute(
            """
            UPDATE approval_requests
            SET approved_by = ?, approved_at = ?, note = ?, status = 'approved', updated_at = ?
            WHERE approval_request_id = ?
            """,
            (approved_by, now, note, now, approval_request_id),
        )

    def mark_wave_complete_if_running(self, conn: sqlite3.Connection, wave_id: str) -> None:
        conn.execute(
            "UPDATE waves SET status = CASE WHEN status = 'running' THEN 'complete' ELSE status END, updated_at = ? WHERE wave_id = ?",
            (self.now_iso(), wave_id),
        )

    def write_manifest(
        self,
        conn: sqlite3.Connection,
        *,
        wave_id: str,
        workspace_dir: str,
        wave_template_id: str,
        policy_version: str,
        intent: str,
        context_refs: dict[str, Any],
        output_path: str,
        evidence: dict[str, Any],
        agent_id: str | None,
    ) -> tuple[str, str]:
        wave_row = conn.execute("SELECT tenant_id FROM waves WHERE wave_id = ?", (wave_id,)).fetchone()
        tenant_id = str(wave_row[0]) if wave_row and wave_row[0] else self.default_tenant_id
        manifest = {
            "wave_id": wave_id,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "wave_template_id": wave_template_id,
            "policy_version": policy_version,
            "intent": intent,
            "context_refs": context_refs,
            "output_path": output_path,
            "timestamps": {"manifested_at": self.now_iso()},
            "evidence": evidence,
        }
        manifest_text = json.dumps(manifest, sort_keys=True, indent=2)
        manifest_hash = self.sha256_text(manifest_text)
        manifest_path = str(Path(workspace_dir) / "manifest.json")
        Path(manifest_path).write_text(manifest_text, encoding="utf-8")
        conn.execute(
            "UPDATE waves SET manifest_hash = ?, manifest_path = ?, updated_at = ? WHERE wave_id = ?",
            (manifest_hash, manifest_path, self.now_iso(), wave_id),
        )
        self.log_decision(
            conn,
            wave_id=wave_id,
            decision="ALLOW",
            reason="manifest signed and stored",
            rule="manifest_sign",
            node="manifest",
        )
        return manifest_hash, manifest_path

    @staticmethod
    def resolve_output_path(context_refs_json: str | None) -> str | None:
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

    def _ensure_wave_columns(self, conn: sqlite3.Connection) -> None:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(waves)").fetchall()}
        required = {
            "tenant_id": "TEXT",
            "agent_id": "TEXT",
            "error_code": "TEXT",
            "error_message": "TEXT",
            "error_node": "TEXT",
            "workspace_dir": "TEXT",
            "wave_token_hash": "TEXT",
            "wave_token_expires_at": "TEXT",
            "manifest_hash": "TEXT",
            "manifest_path": "TEXT",
            "policy_manifest_hash": "TEXT",
            "policy_manifest_version": "TEXT",
            "policy_manifest_json": "TEXT",
            "wave_mutation_token": "TEXT",
            "wave_mutation_token_hash": "TEXT",
            "wave_mutation_token_expires_at": "TEXT",
            "wave_mutation_token_payload_json": "TEXT",
        }
        for col, sql_type in required.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE waves ADD COLUMN {col} {sql_type}")

    def _ensure_wave_decision_columns(self, conn: sqlite3.Connection) -> None:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(wave_decisions)").fetchall()}
        required = {"tenant_id": "TEXT", "prev_hash": "TEXT", "event_hash": "TEXT"}
        for col, sql_type in required.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE wave_decisions ADD COLUMN {col} {sql_type}")

    def _ensure_api_event_columns(self, conn: sqlite3.Connection) -> None:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(api_events)").fetchall()}
        required = {
            "tenant_id": "TEXT",
            "wave_id": "TEXT",
            "event_type": "TEXT",
            "reason_code": "TEXT",
            "node": "TEXT",
            "status": "TEXT",
            "created_at": "TEXT",
        }
        for col, sql_type in required.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE api_events ADD COLUMN {col} {sql_type}")
