from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import sqlite3
from typing import Any, Callable

from .token_validation import TokenValidationLayer


@dataclass(frozen=True)
class TokenServiceError(Exception):
    code: str
    message: str
    node: str


class TokenService:
    def __init__(
        self,
        token_validation: TokenValidationLayer,
        *,
        wave_token_ttl_seconds: int,
        sha256_text: Callable[[str], str],
        now_utc: Callable[[], datetime] | None = None,
    ):
        self.token_validation = token_validation
        self.wave_token_ttl_seconds = wave_token_ttl_seconds
        self.sha256_text = sha256_text
        self.now_utc = now_utc or (lambda: datetime.now(timezone.utc))

    def issue_wave_token(self, wave_id: str, agent_id: str) -> tuple[str, str, str]:
        del wave_id, agent_id  # kept for call-site compatibility and future token claims.
        token = secrets.token_urlsafe(24)
        token_hash = self.sha256_text(token)
        expires_at = (self.now_utc() + timedelta(seconds=self.wave_token_ttl_seconds)).isoformat()
        return token, token_hash, expires_at

    def validate_wave_token(
        self,
        conn: sqlite3.Connection,
        wave_id: str,
        wave_token: str,
        *,
        log_decision: Callable[[sqlite3.Connection, str, str, str, str, str], None],
        node: str = "token_validation",
    ) -> None:
        row = conn.execute(
            """
            SELECT wave_token_hash, wave_token_expires_at
            FROM waves
            WHERE wave_id = ?
            """,
            (wave_id,),
        ).fetchone()
        if not row:
            log_decision(conn, wave_id, "DENY", "wave not found for token validation", "wave_id_exists", node)
            raise TokenServiceError(
                code="WAVE_TOKEN_INVALID",
                message="Wave token validation failed (wave not found).",
                node=node,
            )

        token_result = self.token_validation.validate_wave_token_hash(
            provided_token=wave_token,
            stored_token_hash=row[0],
            expires_at_iso=row[1],
        )
        if not token_result.is_valid:
            rule = str(token_result.details.get("rule", "token_validation"))
            if token_result.reason_code == "WAVE_TOKEN_MISSING":
                reason = "wave token hash missing"
                message = "Wave token is missing for mutation step."
            elif token_result.reason_code == "WAVE_TOKEN_HASH_MISMATCH":
                reason = "token hash mismatch"
                message = "Wave token does not match run scope."
            else:
                reason = "token expired"
                message = "Wave token expired."
            log_decision(conn, wave_id, "DENY", reason, rule, node)
            raise TokenServiceError(code="WAVE_TOKEN_INVALID", message=message, node=node)

        log_decision(conn, wave_id, "ALLOW", "token valid", "token_validation", node)
