from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApprovalCheckResult:
    approved: bool
    reason_code: str
    details: dict[str, Any]


class ApprovalService:
    """Initial approval abstraction; later implementations can query durable stores."""

    def is_approved(self, approval_linkage: dict[str, Any] | None) -> ApprovalCheckResult:
        payload = approval_linkage if isinstance(approval_linkage, dict) else {}
        approval_id = str(payload.get("approval_id", "")).strip()
        if approval_id:
            return ApprovalCheckResult(approved=True, reason_code="APPROVED", details={"approval_id": approval_id})
        return ApprovalCheckResult(approved=False, reason_code="APPROVAL_MISSING", details={})

