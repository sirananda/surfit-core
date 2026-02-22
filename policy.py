"""
SurFit V1 — Policy Enforcement
policy_check() runs BEFORE every tool execution.
Returns PolicyDecision(ALLOW) or PolicyDecision(DENY) with reasons.
"""

from __future__ import annotations

from models import Decision, PolicyDecision, RunContext

# ── Policy bundle (loaded from spec, hardcoded for V1) ────────────

DEFAULT_POLICY = {
    "policy_id": "policy_board_metrics_v1",
    "sensitivity_level": "medium",
    "tool_allowlist": {
        "tool_salesforce_read_pipeline",
        "tool_stripe_read_revenue",
        "tool_reconcile_metrics",
        "tool_generate_board_summary",
        "tool_slides_update_template",
        "tool_logger_write",
    },
    "tool_denylist": {
        "tool_browser",
        "tool_shell_exec",
        "tool_external_http",
        "tool_email_send",
        "tool_slack_dm",
    },
    "egress": {
        "allow_external_http": False,
        "allowed_domains": [],
        "allow_email_send": False,
        "allow_slack_dm": False,
    },
    "write_restrictions": {
        "tool_slides_update_template": {
            "allowed_template_ids": ["TEMPLATE_DECK_V1"],
            "allow_create_new_decks": False,
        }
    },
}

# Tools that are infrastructure — exempt from policy deny
INFRA_TOOLS = {"tool_logger_write"}


def policy_check(
    tool_name: str,
    tool_inputs: dict,
    ctx: RunContext,
    is_write: bool = False,
    policy: dict | None = None,
) -> PolicyDecision:
    """
    Evaluate whether a tool call is permitted under the active policy.

    Checks in order:
      1. Denylist (explicit block)
      2. Allowlist (must be present)
      3. Egress rules (if tool would make external calls)
      4. Write restrictions (template ID validation)

    If `policy` is passed, use it. Otherwise fall back to DEFAULT_POLICY.
    Returns DENY on first failure with accumulated reasons.
    """
    policy = policy if policy is not None else DEFAULT_POLICY
    reasons: list[str] = []

    # ── 1. Denylist ───────────────────────────────────────────────
    if tool_name in policy["tool_denylist"]:
        reasons.append(f"Tool '{tool_name}' is on the denylist.")
        return PolicyDecision(
            decision=Decision.DENY, tool_name=tool_name, reasons=reasons
        )

    # ── 2. Allowlist ──────────────────────────────────────────────
    if tool_name not in policy["tool_allowlist"]:
        reasons.append(
            f"Tool '{tool_name}' is not on the allowlist for policy "
            f"'{policy['policy_id']}'."
        )
        return PolicyDecision(
            decision=Decision.DENY, tool_name=tool_name, reasons=reasons
        )

    # ── 3. Egress rules ──────────────────────────────────────────
    egress = policy["egress"]
    if tool_name == "tool_external_http" and not egress["allow_external_http"]:
        reasons.append("External HTTP egress is disabled by policy.")
    if tool_name == "tool_email_send" and not egress["allow_email_send"]:
        reasons.append("Email send is disabled by policy.")
    if tool_name == "tool_slack_dm" and not egress["allow_slack_dm"]:
        reasons.append("Slack DM is disabled by policy.")

    if reasons:
        return PolicyDecision(
            decision=Decision.DENY, tool_name=tool_name, reasons=reasons
        )

    # ── 4. Write restrictions ─────────────────────────────────────
    if is_write and tool_name in policy["write_restrictions"]:
        restrictions = policy["write_restrictions"][tool_name]

        template_id = tool_inputs.get("template_id", "")
        if template_id not in restrictions["allowed_template_ids"]:
            reasons.append(
                f"Template ID '{template_id}' is not in the allowed list: "
                f"{restrictions['allowed_template_ids']}."
            )

        if tool_inputs.get("create_new_deck", False) and not restrictions.get(
            "allow_create_new_decks", False
        ):
            reasons.append("Creating new decks is not allowed by policy.")

        if reasons:
            return PolicyDecision(
                decision=Decision.DENY, tool_name=tool_name, reasons=reasons
            )

    # ── All checks passed ─────────────────────────────────────────
    return PolicyDecision(
        decision=Decision.ALLOW, tool_name=tool_name, reasons=["all_checks_passed"]
    )


def policy_from_spec(saw_spec: dict) -> dict:
    """Extract a policy dict from a SAW spec JSON, matching DEFAULT_POLICY shape."""
    pb = saw_spec["policy_bundle"]
    return {
        "policy_id": pb["policy_id"],
        "sensitivity_level": pb["sensitivity_level"],
        "tool_allowlist": set(pb["tools"]["allowlist"]),
        "tool_denylist": set(pb["tools"]["denylist"]),
        "egress": pb["egress"],
        "write_restrictions": pb.get("write_restrictions", {}),
    }
