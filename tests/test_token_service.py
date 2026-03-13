from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import sqlite3
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from surfit.runtime.token_service import TokenService, TokenServiceError
from surfit.runtime.token_validation import TokenValidationLayer


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_service(ttl_seconds: int = 180) -> TokenService:
    return TokenService(
        token_validation=TokenValidationLayer(),
        wave_token_ttl_seconds=ttl_seconds,
        sha256_text=_sha256_text,
    )


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE waves (
            wave_id TEXT PRIMARY KEY,
            wave_token_hash TEXT,
            wave_token_expires_at TEXT
        )
        """
    )
    conn.commit()
    return conn


class TokenServiceTests(unittest.TestCase):
    def test_issue_wave_token_returns_hash_and_expiry(self):
        service = _build_service(ttl_seconds=120)
        token, token_hash, expires_at = service.issue_wave_token("wave-1", "agent-1")
        self.assertTrue(token)
        self.assertEqual(token_hash, _sha256_text(token))
        self.assertGreater(datetime.fromisoformat(expires_at), datetime.now(timezone.utc))

    def test_validate_wave_token_allows_valid_token(self):
        service = _build_service()
        conn = _make_conn()
        events: list[tuple[str, str, str, str]] = []

        def _log(_conn, wave_id, decision, reason, rule, node):
            events.append((wave_id, decision, reason, node))

        try:
            token, token_hash, expires_at = service.issue_wave_token("wave-valid", "agent-1")
            conn.execute(
                "INSERT INTO waves (wave_id, wave_token_hash, wave_token_expires_at) VALUES (?, ?, ?)",
                ("wave-valid", token_hash, expires_at),
            )
            conn.commit()

            service.validate_wave_token(
                conn,
                "wave-valid",
                token,
                log_decision=_log,
                node="run_wave.token",
            )
            self.assertEqual(events[-1][1], "ALLOW")
        finally:
            conn.close()

    def test_validate_wave_token_rejects_missing_and_mismatch(self):
        service = _build_service()
        conn = _make_conn()
        events: list[tuple[str, str, str, str]] = []

        def _log(_conn, wave_id, decision, reason, rule, node):
            events.append((wave_id, decision, reason, node))

        try:
            with self.assertRaises(TokenServiceError) as missing_err:
                service.validate_wave_token(conn, "wave-missing", "abc", log_decision=_log)
            self.assertEqual(missing_err.exception.code, "WAVE_TOKEN_INVALID")

            token, _, _ = service.issue_wave_token("wave-mismatch", "agent-1")
            conn.execute(
                "INSERT INTO waves (wave_id, wave_token_hash, wave_token_expires_at) VALUES (?, ?, ?)",
                (
                    "wave-mismatch",
                    _sha256_text("different-token"),
                    (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
                ),
            )
            conn.commit()

            with self.assertRaises(TokenServiceError) as mismatch_err:
                service.validate_wave_token(conn, "wave-mismatch", token, log_decision=_log)
            self.assertEqual(mismatch_err.exception.code, "WAVE_TOKEN_INVALID")
            self.assertTrue(any(decision == "DENY" for _, decision, _, _ in events))
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
