from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ._common import DemoHandlerDeps, DemoHandlerError, DemoHandlerRequest


def execute_demo3_enterprise_integrations(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    case_key = request.integration_case.strip().lower()
    if case_key == "github":
        method = "PUT"
        url = f"{request.integration_base_url.rstrip('/')}/repo/file_update"
        action_label = "GitHub file mutation attempt"
        target_path = "/repo/infrastructure/terraform/prod.tf"
        tool_name = "repo.file_update"
        payload = {
            "wave_id": request.wave_id,
            "requested_by": request.approved_by,
            "target_path": target_path,
            "content": "resource \"aws_iam_policy\" \"prod\" {}\n",
        }
    elif case_key == "aws":
        method = "POST"
        url = f"{request.integration_base_url.rstrip('/')}/aws/iam/modify_policy"
        action_label = "AWS IAM modification attempt"
        target_path = ""
        tool_name = "aws.iam.modify_policy"
        payload = {
            "wave_id": request.wave_id,
            "requested_by": request.approved_by,
            "policy_name": "ProdAdminPolicy",
            "statement": "Allow:*",
        }
    elif case_key == "slack":
        method = "POST"
        url = f"{request.integration_base_url.rstrip('/')}/slack/channel/post_message"
        action_label = "Deployment approval"
        target_path = ""
        tool_name = "deployment.approve_release"
        payload = {
            "wave_id": request.wave_id,
            "requested_by": request.approved_by,
            "channel": "#ai-governance",
            "message": "Deployment approved via Surfit Wave.",
        }
    else:
        raise DemoHandlerError("BAD_CONTEXT", "integration_case must be github, aws, or slack", "run_wave")

    status_code, proxied = deps.ocean_proxy_http(
        {
            "method": method,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "json_body": payload,
            "wave_mutation_token": request.wave_mutation_token,
            "governance_context": {
                "tool": tool_name,
                "target_path": target_path,
                "integration_case": case_key,
            },
        }
    )
    decision_status = str(proxied.get("status", "REJECTED"))
    reason_code = str(proxied.get("reason_code", "UNKNOWN"))
    message = str(proxied.get("message", proxied.get("body", "")))
    slack_notification = None
    if case_key == "slack" and status_code == 200:
        slack_notification = {
            "channel": "#ai-governance",
            "message": "Deployment approved via Surfit Wave.",
            "status": "sent",
        }
    lines = [
        "# Enterprise Integration Governance Report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Wave ID: {request.wave_id}",
        f"Action: {action_label}",
        f"Integration case: {case_key}",
        f"Target URL: {url}",
        f"Tool: {tool_name}",
        f"Target path: {target_path or 'n/a'}",
        f"Surfit decision: {decision_status}",
        f"Reason code: {reason_code}",
        f"Message: {message}",
        f"Policy manifest hash prefix: {(request.policy_manifest_hash or '')[:12]}",
        "",
        "## Governance Evidence",
        f"- Export bundle: /api/waves/{request.wave_id}/export",
        f"- Verify command: python3 scripts/verify_wave_bundle.py outputs/wave_bundle_{request.wave_id}.json",
        "",
    ]
    if slack_notification:
        lines.extend(
            [
                "## Slack Notification",
                f"- channel: {slack_notification['channel']}",
                f"- message: {slack_notification['message']}",
                "",
            ]
        )
    lines.extend(
        [
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
        rendered_content="\n".join(lines),
        node="enterprise_integration_governance.write",
    )
    if status_code != 200:
        raise DemoHandlerError(
            reason_code if reason_code else "SCOPE_VIOLATION",
            f"{reason_code}: {message}",
            "enterprise_integration_governance.proxy",
        )
    return {
        "workspace_output": workspace_output,
        "action_label": action_label,
        "integration_case": case_key,
        "tool_name": tool_name,
        "target_path": target_path,
        "target_url": url,
        "decision_status": decision_status,
        "reason_code": reason_code,
        "demo3_slack_notification": slack_notification,
    }

