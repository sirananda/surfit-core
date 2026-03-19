#!/usr/bin/env python3
"""
SURFIT — Agent Demo (V2.4)
Proves Surfit controls any caller, not just Slack.
This is a dumb script that acts like an agent hitting Surfit's API.

Usage:
  python agent_demo.py                          # runs all examples
  python agent_demo.py "deploy to production"   # custom action

No LLMs. No frameworks. No orchestration.
Just a caller → Surfit → decision → enforced outcome.
"""

import json
import sys
import urllib.request

API_BASE = "http://localhost:8000"

def surfit_evaluate(system, action, resource, context):
    """Send an action to Surfit and get a decision."""
    payload = {
        "system": system,
        "action": action,
        "resource": resource,
        "context": context,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/governance/evaluate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR: Could not reach Surfit at {API_BASE}: {e}")
        return None


def surfit_ingest_slack(action, channel_name, text, visibility="internal"):
    """Send a Slack action through the ingestion endpoint."""
    payload = {
        "event_type": "agent_action",
        "system": "slack",
        "action": action,
        "resource": {"channel_name": channel_name},
        "context": {"env": "prod", "visibility": visibility},
        "content": {"text": text},
        "agent_id": "agent-demo-v1",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/ingest/slack",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR: Could not reach Surfit at {API_BASE}: {e}")
        return None


def display_result(label, result):
    if not result:
        return
    wave = result.get("wave_score") or result.get("wave_score")
    handling = result.get("handling")
    wave_label = result.get("wave_label", f"Wave {wave}")

    icons = {"auto": "\u2705", "log": "\U0001F4DD", "check": "\U0001F50D", "approve": "\u26A0\uFE0F", "block": "\U0001F6D1"}
    outcomes = {"auto": "EXECUTED", "log": "EXECUTED (logged)", "check": "HELD (verification)", "approve": "HELD (awaiting approval)", "block": "BLOCKED"}

    icon = icons.get(handling, "\U0001F30A")
    outcome = outcomes.get(handling, handling)

    print(f"\n  {icon} {label}")
    print(f"     {wave_label} \u2192 {outcome}")
    if result.get("destination_class") or result.get("destination_class_resolved"):
        dest = result.get("destination_class") or result.get("destination_class_resolved")
        print(f"     Destination: {dest}")
    print()


def run_examples():
    print("\n" + "="*55)
    print("  SURFIT AGENT DEMO")
    print("  Proving system-agnostic execution control")
    print("="*55)

    # 1. Slack DM — should auto-execute
    print("\n--- Slack: Direct Message ---")
    r = surfit_evaluate("slack", "post_dm", {"resource_id": "D0AGENT1"}, {"env": "prod", "visibility": "internal"})
    display_result("Slack DM", r)

    # 2. Slack team channel — should auto-execute
    print("--- Slack: Team Channel ---")
    r = surfit_ingest_slack("post_message", "eng-platform", "Agent: CI pipeline green, all tests passing.")
    display_result("Slack #eng-platform", r)

    # 3. Slack announcement — should be held
    print("--- Slack: Company Announcement ---")
    r = surfit_ingest_slack("post_announcement", "company-announcements", "Agent: Q1 revenue report is ready.", "company_wide")
    display_result("Slack #company-announcements", r)

    # 4. GitHub merge to main — should be held
    print("--- GitHub: Merge PR to main ---")
    r = surfit_evaluate("github", "merge_pr", {"repo": "main"}, {"env": "prod", "reversible": False})
    display_result("GitHub merge to main", r)

    # 5. GitHub push to dev — should auto-execute
    print("--- GitHub: Push to dev branch ---")
    r = surfit_evaluate("github", "push_branch", {"repo": "feature-xyz"}, {"env": "dev"})
    display_result("GitHub push (dev)", r)

    # 6. Notion DB update — should be checked
    print("--- Notion: Update protected database ---")
    r = surfit_evaluate("notion", "update_database_entry", {"database": "Sprint Tracker"}, {"env": "prod"})
    display_result("Notion Sprint Tracker update", r)

    # 7. Unknown system — should default to moderate
    print("--- Unknown: Salesforce record update ---")
    r = surfit_evaluate("salesforce", "update_record", {}, {"env": "prod"})
    display_result("Salesforce (unknown system)", r)

    print("="*55)
    print("  Every action evaluated by the same engine.")
    print("  Every decision deterministic and explainable.")
    print("  Surfit is system-agnostic.")
    print("="*55 + "\n")


def run_custom(text):
    print(f"\n  Agent attempting: \"{text}\"")
    r = surfit_ingest_slack("post_message", "company-announcements", text, "company_wide")
    display_result(f"Custom action", r)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_custom(" ".join(sys.argv[1:]))
    else:
        run_examples()
