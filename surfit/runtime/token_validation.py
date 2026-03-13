from __future__ import annotations

from datetime import datetime, timezone
import hashlib

from .models import TokenValidationResult


class TokenValidationLayer:
    """Validates token/policy/runtime intersections and basic token hashes."""

    def validate_scope_intersection(
        self,
        *,
        token_scope: set[str],
        pinned_policy_manifest: set[str],
        runtime_rules: set[str],
    ) -> TokenValidationResult:
        effective_scope = token_scope & pinned_policy_manifest & runtime_rules
        if not effective_scope:
            return TokenValidationResult(
                is_valid=False,
                reason_code="TOKEN_SCOPE_INTERSECTION_EMPTY",
                effective_scope=set(),
                details={
                    "token_scope": sorted(token_scope),
                    "pinned_policy_manifest": sorted(pinned_policy_manifest),
                    "runtime_rules": sorted(runtime_rules),
                },
            )
        return TokenValidationResult(
            is_valid=True,
            reason_code="TOKEN_SCOPE_VALID",
            effective_scope=effective_scope,
            details={"effective_scope": sorted(effective_scope)},
        )

    def validate_wave_token_hash(
        self,
        *,
        provided_token: str,
        stored_token_hash: str | None,
        expires_at_iso: str | None,
    ) -> TokenValidationResult:
        if not stored_token_hash:
            return TokenValidationResult(
                is_valid=False,
                reason_code="WAVE_TOKEN_MISSING",
                details={"rule": "token_present"},
            )
        provided_hash = hashlib.sha256(provided_token.encode("utf-8")).hexdigest()
        if provided_hash != stored_token_hash:
            return TokenValidationResult(
                is_valid=False,
                reason_code="WAVE_TOKEN_HASH_MISMATCH",
                details={"rule": "token_match"},
            )
        if not expires_at_iso:
            return TokenValidationResult(
                is_valid=False,
                reason_code="WAVE_TOKEN_EXPIRED",
                details={"rule": "token_expiry"},
            )
        expires_at = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            return TokenValidationResult(
                is_valid=False,
                reason_code="WAVE_TOKEN_EXPIRED",
                details={"rule": "token_expiry"},
            )
        return TokenValidationResult(
            is_valid=True,
            reason_code="WAVE_TOKEN_VALID",
            details={"rule": "token_validation"},
        )

