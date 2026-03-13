from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ._common import DemoHandlerDeps, DemoHandlerError, DemoHandlerRequest


def execute_demo2_change_control(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    target_url = f"{request.repo_base_url.rstrip('/')}/repo/{request.attempted_action}"
    status_code, proxied = deps.ocean_proxy_http(
        {
            "method": "POST",
            "url": target_url,
            "headers": {"Content-Type": "application/json"},
            "json_body": {
                "wave_id": request.wave_id,
                "attempted_action": request.attempted_action,
                "requested_by": request.approved_by,
            },
            "wave_mutation_token": request.wave_mutation_token,
        }
    )
    decision_status = str(proxied.get("status", "REJECTED"))
    reason_code = str(proxied.get("reason_code", "UNKNOWN"))
    message = str(proxied.get("message", proxied.get("body", "")))
    rendered = "\n".join(
        [
            "# Enterprise Change Control Report",
            "",
            f"Generated at: {datetime.now(timezone.utc).isoformat()}",
            f"Wave ID: {request.wave_id}",
            f"Attempted action: {request.attempted_action}",
            f"Target URL: {target_url}",
            f"Surfit decision: {decision_status}",
            f"Reason code: {reason_code}",
            f"Message: {message}",
            f"Policy manifest hash prefix: {(request.policy_manifest_hash or '')[:12]}",
            "",
            "## Governance Evidence",
            f"- Export bundle: /api/waves/{request.wave_id}/export",
            f"- Verify command: python3 scripts/verify_wave_bundle.py outputs/wave_bundle_{request.wave_id}.json",
            "",
            "## Approval Metadata",
            f"- approved_by: {request.approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "",
        ]
    )
    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content=rendered,
        node="enterprise_change_control.write",
    )
    if status_code != 200:
        raise DemoHandlerError(
            reason_code if reason_code else "SCOPE_VIOLATION",
            f"{reason_code}: {message}",
            "enterprise_change_control.proxy",
        )
    return {
        "workspace_output": workspace_output,
        "target_url": target_url,
        "attempted_action": request.attempted_action,
        "decision_status": decision_status,
        "reason_code": reason_code,
    }

