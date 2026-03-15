from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from .artifact_service import ArtifactRetrievalService


class WaveReadService:
    """Read-model assembly for operator/inspection timeline views."""

    def __init__(self, artifact_retrieval: ArtifactRetrievalService):
        self.artifact_retrieval = artifact_retrieval

    @staticmethod
    def _load_context(raw_context: str | None) -> dict[str, Any]:
        if not raw_context:
            return {}
        try:
            payload = json.loads(raw_context)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _max_iso(*values: str | None) -> str | None:
        parsed: list[tuple[datetime, str]] = []
        for value in values:
            if not value:
                continue
            try:
                parsed.append((datetime.fromisoformat(value.replace("Z", "+00:00")), value))
            except Exception:
                continue
        if not parsed:
            return None
        parsed.sort(key=lambda item: item[0], reverse=True)
        return parsed[0][1]

    def list_recent_waves(
        self,
        conn: sqlite3.Connection,
        *,
        tenant_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit), 100))

        wave_rows = conn.execute(
            """
            SELECT wave_id, tenant_id, wave_template_id, context_refs_json, status, created_at, updated_at
            FROM waves
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (tenant_id, normalized_limit),
        ).fetchall()

        artifacts = self.artifact_retrieval.list_recent(tenant_id=tenant_id, limit=max(100, normalized_limit * 5))
        artifact_by_wave: dict[str, dict[str, Any]] = {}
        for row in artifacts:
            wave_id = str(row.get("wave_id") or "").strip()
            if wave_id and wave_id not in artifact_by_wave:
                artifact_by_wave[wave_id] = row

        out: list[dict[str, Any]] = []
        for wave_id, row_tenant_id, wave_template_id, context_refs_json, status, created_at, updated_at in wave_rows:
            context = self._load_context(context_refs_json)
            latest_decision_row = conn.execute(
                """
                SELECT decision, rule, created_at
                FROM wave_decisions
                WHERE tenant_id = ? AND wave_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (tenant_id, wave_id),
            ).fetchone()

            latest_decision = latest_decision_row[0] if latest_decision_row else None
            latest_reason_code = latest_decision_row[1] if latest_decision_row else None
            latest_decision_at = latest_decision_row[2] if latest_decision_row else None

            approval_row = conn.execute(
                """
                SELECT approval_request_id, status, updated_at
                FROM approval_requests
                WHERE wave_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (wave_id,),
            ).fetchone()
            approval_request_id = approval_row[0] if approval_row else None
            approval_status = approval_row[1] if approval_row else None
            approval_updated_at = approval_row[2] if approval_row else None

            artifact_summary = artifact_by_wave.get(str(wave_id), {})
            artifact_id = artifact_summary.get("artifact_id")
            artifact_ts = artifact_summary.get("timestamp")

            approval_linkage: dict[str, Any] | None = None
            approval_wave_id = None
            if artifact_id:
                artifact_full = self.artifact_retrieval.get(str(artifact_id)) or {}
                raw_linkage = artifact_full.get("approval_linkage")
                if isinstance(raw_linkage, dict) and raw_linkage:
                    approval_linkage = raw_linkage
                    linked = raw_linkage.get("linked_wave_id")
                    if isinstance(linked, str) and linked.strip():
                        approval_wave_id = linked

            system = context.get("system")
            action = context.get("action")
            wave_type = context.get("wave_type")

            out.append(
                {
                    "wave_id": wave_id,
                    "tenant_id": row_tenant_id,
                    "template_id": wave_template_id,
                    "wave_type": wave_type if isinstance(wave_type, str) else None,
                    "system": system if isinstance(system, str) else None,
                    "action": action if isinstance(action, str) else None,
                    "status": status,
                    "latest_decision": latest_decision,
                    "latest_reason_code": latest_reason_code,
                    "artifact_id": artifact_id,
                    "approval_request_id": approval_request_id,
                    "approval_status": approval_status,
                    "approval_wave_id": approval_wave_id,
                    "approval_linkage": approval_linkage,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "last_event_at": self._max_iso(
                        updated_at,
                        latest_decision_at,
                        approval_updated_at,
                        artifact_ts if isinstance(artifact_ts, str) else None,
                    ),
                }
            )

        seen_wave_ids = {str(item.get("wave_id")) for item in out if item.get("wave_id")}
        for wave_id, artifact_summary in artifact_by_wave.items():
            if not wave_id or wave_id in seen_wave_ids:
                continue

            artifact_id = artifact_summary.get("artifact_id")
            artifact_ts = artifact_summary.get("timestamp")
            artifact_decision = artifact_summary.get("decision")
            artifact_reason = artifact_summary.get("reason_code")
            approval_row = conn.execute(
                """
                SELECT approval_request_id, status, updated_at
                FROM approval_requests
                WHERE wave_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (wave_id,),
            ).fetchone()
            approval_request_id = approval_row[0] if approval_row else None
            approval_status = approval_row[1] if approval_row else None
            approval_updated_at = approval_row[2] if approval_row else None

            approval_linkage: dict[str, Any] | None = None
            approval_wave_id = None
            if artifact_id:
                artifact_full = self.artifact_retrieval.get(str(artifact_id)) or {}
                raw_linkage = artifact_full.get("approval_linkage")
                if isinstance(raw_linkage, dict) and raw_linkage:
                    approval_linkage = raw_linkage
                    linked = raw_linkage.get("linked_wave_id")
                    if isinstance(linked, str) and linked.strip():
                        approval_wave_id = linked

            out.append(
                {
                    "wave_id": wave_id,
                    "tenant_id": tenant_id,
                    "template_id": artifact_summary.get("wave_template_id") or artifact_summary.get("template_id"),
                    "wave_type": artifact_summary.get("wave_type"),
                    "system": artifact_summary.get("system"),
                    "action": artifact_summary.get("action"),
                    "status": "evaluated",
                    "latest_decision": artifact_decision,
                    "latest_reason_code": artifact_reason,
                    "artifact_id": artifact_id,
                    "approval_request_id": approval_request_id,
                    "approval_status": approval_status,
                    "approval_wave_id": approval_wave_id,
                    "approval_linkage": approval_linkage,
                    "created_at": artifact_ts if isinstance(artifact_ts, str) else None,
                    "updated_at": artifact_ts if isinstance(artifact_ts, str) else None,
                    "last_event_at": self._max_iso(
                        approval_updated_at if isinstance(approval_updated_at, str) else None,
                        artifact_ts if isinstance(artifact_ts, str) else None,
                    ),
                }
            )

        out.sort(
            key=lambda row: (
                row.get("last_event_at") or "",
                row.get("created_at") or "",
            ),
            reverse=True,
        )

        return out[:normalized_limit]

    def get_wave_decisions(self, conn: sqlite3.Connection, *, wave_id: str) -> dict[str, Any] | None:
        wave_row = conn.execute(
            """
            SELECT wave_id, tenant_id, wave_template_id, policy_version, policy_manifest_hash, status, created_at, updated_at
            FROM waves
            WHERE wave_id = ?
            LIMIT 1
            """,
            (wave_id,),
        ).fetchone()
        if not wave_row:
            return None

        (
            row_wave_id,
            tenant_id,
            template_id,
            policy_reference,
            policy_manifest_hash,
            status,
            created_at,
            updated_at,
        ) = wave_row

        artifact_summary: dict[str, Any] | None = None
        for row in self.artifact_retrieval.list_recent(tenant_id=tenant_id, limit=500):
            if str(row.get("wave_id") or "").strip() == str(row_wave_id):
                artifact_summary = row
                break

        artifact_id = artifact_summary.get("artifact_id") if artifact_summary else None
        artifact_timestamp = artifact_summary.get("timestamp") if artifact_summary else None

        approval_linkage: dict[str, Any] | None = None
        approval_wave_id = None
        if artifact_id:
            artifact_full = self.artifact_retrieval.get(str(artifact_id)) or {}
            raw_linkage = artifact_full.get("approval_linkage")
            if isinstance(raw_linkage, dict) and raw_linkage:
                approval_linkage = raw_linkage
                linked = raw_linkage.get("linked_wave_id")
                if isinstance(linked, str) and linked.strip():
                    approval_wave_id = linked

        approval_row = conn.execute(
            """
            SELECT approval_request_id, status, updated_at
            FROM approval_requests
            WHERE wave_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (row_wave_id,),
        ).fetchone()
        approval_request_id = approval_row[0] if approval_row else None
        approval_status = approval_row[1] if approval_row else None
        approval_updated_at = approval_row[2] if approval_row else None

        decision_rows = conn.execute(
            """
            SELECT id, decision, rule, created_at
            FROM wave_decisions
            WHERE wave_id = ?
            ORDER BY id ASC
            """,
            (row_wave_id,),
        ).fetchall()

        decisions = [
            {
                "decision_id": row[0],
                "decision": row[1],
                "reason_code": row[2],
                "policy_reference": policy_reference,
                "policy_manifest_hash": policy_manifest_hash,
                "artifact_id": artifact_id,
                "approval_request_id": approval_request_id,
                "approval_wave_id": approval_wave_id,
                "approval_linkage": approval_linkage,
                "timestamp": row[3],
            }
            for row in decision_rows
        ]

        return {
            "wave_id": row_wave_id,
            "tenant_id": tenant_id,
            "template_id": template_id,
            "status": status,
            "policy_reference": policy_reference,
            "policy_manifest_hash": policy_manifest_hash,
            "artifact_id": artifact_id,
            "approval_request_id": approval_request_id,
            "approval_status": approval_status,
            "approval_wave_id": approval_wave_id,
            "approval_linkage": approval_linkage,
            "created_at": created_at,
            "updated_at": updated_at,
            "last_event_at": self._max_iso(
                updated_at,
                approval_updated_at,
                artifact_timestamp if isinstance(artifact_timestamp, str) else None,
                decisions[-1]["timestamp"] if decisions else None,
            ),
            "count": len(decisions),
            "decisions": decisions,
        }


    def list_recent_approvals(
        self,
        conn: sqlite3.Connection,
        *,
        tenant_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit), 100))

        approval_rows = conn.execute(
            """
            SELECT ar.approval_request_id, ar.wave_id, ar.status, ar.created_at, ar.updated_at
            FROM approval_requests ar
            JOIN waves w ON w.wave_id = ar.wave_id
            WHERE w.tenant_id = ?
            ORDER BY ar.updated_at DESC, ar.created_at DESC
            LIMIT ?
            """,
            (tenant_id, normalized_limit),
        ).fetchall()

        artifacts = self.artifact_retrieval.list_recent(tenant_id=tenant_id, limit=max(100, normalized_limit * 5))
        artifact_by_wave: dict[str, dict[str, Any]] = {}
        for row in artifacts:
            wave_id = str(row.get("wave_id") or "").strip()
            if wave_id and wave_id not in artifact_by_wave:
                artifact_by_wave[wave_id] = row

        out: list[dict[str, Any]] = []
        for approval_request_id, wave_id, approval_status, created_at, updated_at in approval_rows:
            wave_row = conn.execute(
                """
                SELECT tenant_id, wave_template_id, context_refs_json
                FROM waves
                WHERE wave_id = ?
                LIMIT 1
                """,
                (wave_id,),
            ).fetchone()
            if not wave_row:
                continue

            row_tenant_id, template_id, context_refs_json = wave_row
            context = self._load_context(context_refs_json)

            latest_decision_row = conn.execute(
                """
                SELECT decision, rule, created_at
                FROM wave_decisions
                WHERE wave_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (wave_id,),
            ).fetchone()
            latest_decision = latest_decision_row[0] if latest_decision_row else None
            latest_reason_code = latest_decision_row[1] if latest_decision_row else None
            latest_decision_at = latest_decision_row[2] if latest_decision_row else None

            artifact_summary = artifact_by_wave.get(str(wave_id), {})
            artifact_id = artifact_summary.get("artifact_id")
            artifact_ts = artifact_summary.get("timestamp")

            approval_linkage: dict[str, Any] | None = None
            approval_wave_id = None
            linked_wave_id = None
            if artifact_id:
                artifact_full = self.artifact_retrieval.get(str(artifact_id)) or {}
                raw_linkage = artifact_full.get("approval_linkage")
                if isinstance(raw_linkage, dict) and raw_linkage:
                    approval_linkage = raw_linkage
                    approval_wave_raw = raw_linkage.get("approval_wave_id")
                    if isinstance(approval_wave_raw, str) and approval_wave_raw.strip():
                        approval_wave_id = approval_wave_raw
                    linked_wave_raw = raw_linkage.get("linked_wave_id")
                    if isinstance(linked_wave_raw, str) and linked_wave_raw.strip():
                        linked_wave_id = linked_wave_raw

            system = context.get("system")
            action = context.get("action")

            out.append(
                {
                    "approval_request_id": approval_request_id,
                    "tenant_id": row_tenant_id,
                    "wave_id": wave_id,
                    "approval_wave_id": approval_wave_id,
                    "linked_wave_id": linked_wave_id,
                    "approval_status": approval_status,
                    "template_id": template_id,
                    "system": system if isinstance(system, str) else None,
                    "action": action if isinstance(action, str) else None,
                    "latest_decision": latest_decision,
                    "latest_reason_code": latest_reason_code,
                    "artifact_id": artifact_id,
                    "approval_linkage": approval_linkage,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "last_event_at": self._max_iso(
                        updated_at,
                        latest_decision_at,
                        artifact_ts if isinstance(artifact_ts, str) else None,
                    ),
                }
            )

        return out
