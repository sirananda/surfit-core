"""
SURFIT Wave Engine — Test Suite v1.1
Calibrated for realistic wave distribution.
Most normal actions → Wave 1-3. Only high-consequence → Wave 4-5.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo


def print_result(label, result, target_wave=None):
    status = ""
    if target_wave is not None:
        match = result.wave_score == target_wave if isinstance(target_wave, int) else result.wave_score in target_wave
        status = " ✓" if match else f" ✗ (expected Wave {target_wave})"
    print(f"\n{'─'*60}")
    print(f"  {label}{status}")
    print(f"{'─'*60}")
    print(f"  Wave:      {result.wave_label} (score={result.wave_score}, raw={result.raw_score})")
    print(f"  Handling:  {result.handling}")
    print(f"  Dest:      {result.destination_class_resolved}")
    parts = []
    for f in result.contributing_factors:
        parts.append(f"{f.key}({f.modifier:+d})")
    print(f"  Math:      {' + '.join(parts)} = {result.raw_score} → {result.wave_score}")
    print()


def test_calibrated():
    engine = WaveEngine()
    failures = []

    def check(label, request, expected_wave, expected_handling=None):
        result = engine.evaluate(request)
        wave_ok = result.wave_score == expected_wave if isinstance(expected_wave, int) else result.wave_score in expected_wave
        handling_ok = expected_handling is None or result.handling == expected_handling
        print_result(label, result, expected_wave)
        if not wave_ok or not handling_ok:
            failures.append(f"{label}: got Wave {result.wave_score}/{result.handling}, expected Wave {expected_wave}/{expected_handling}")

    # ── SLACK ──
    check("Slack DM (prod)", EvaluateRequest(
        system="slack", action="post_dm",
        resource=ResourceInfo(resource_id="D0ABC123"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=1, expected_handling="auto")

    check("Slack team channel post (prod)", EvaluateRequest(
        system="slack", action="post_message",
        resource=ResourceInfo(resource_name="eng-platform"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=1, expected_handling="auto")

    check("Slack company announcement (prod)", EvaluateRequest(
        system="slack", action="post_announcement",
        resource=ResourceInfo(resource_name="company-announcements"),
        context=ContextInfo(env="prod", visibility="company_wide", reversible=True),
    ), expected_wave=5, expected_handling="approve")

    check("Slack external channel (prod, external vis)", EvaluateRequest(
        system="slack", action="post_message",
        resource=ResourceInfo(resource_name="external-partner-channel"),
        context=ContextInfo(env="prod", visibility="external", reversible=True),
    ), expected_wave=5, expected_handling="approve")

    check("Slack external channel (prod, internal vis)", EvaluateRequest(
        system="slack", action="post_message",
        resource=ResourceInfo(resource_name="external-partner-channel"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=4, expected_handling="approve")

    check("Slack sensitive channel (prod)", EvaluateRequest(
        system="slack", action="post_message",
        resource=ResourceInfo(resource_name="security-incidents"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=3, expected_handling="check")

    # ── NOTION ──
    check("Notion create page (prod)", EvaluateRequest(
        system="notion", action="create_page",
        resource=ResourceInfo(resource_name="New Doc"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=1, expected_handling="auto")

    check("Notion update page (prod)", EvaluateRequest(
        system="notion", action="update_page",
        resource=ResourceInfo(resource_name="Team Notes"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=1, expected_handling="auto")

    check("Notion protected DB update (prod)", EvaluateRequest(
        system="notion", action="update_database_entry",
        resource=ResourceInfo(resource_name="Sprint Tracker"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=3, expected_handling="check")

    check("Notion protected DB (prod, company-wide)", EvaluateRequest(
        system="notion", action="update_database_entry",
        resource=ResourceInfo(resource_name="OKRs"),
        context=ContextInfo(env="prod", visibility="company_wide", reversible=True),
    ), expected_wave=4, expected_handling="approve")

    check("Notion delete page (prod, irreversible)", EvaluateRequest(
        system="notion", action="delete_page",
        resource=ResourceInfo(resource_name="Important Doc"),
        context=ContextInfo(env="prod", visibility="internal", reversible=False),
    ), expected_wave=4, expected_handling="approve")

    # ── GITHUB ──
    check("GitHub create PR (prod)", EvaluateRequest(
        system="github", action="create_pr",
        resource=ResourceInfo(resource_name="feature-auth"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=2, expected_handling="log")

    check("GitHub push branch (dev)", EvaluateRequest(
        system="github", action="push_branch",
        resource=ResourceInfo(resource_name="feature-xyz"),
        context=ContextInfo(env="dev", visibility="internal", reversible=True),
    ), expected_wave=1, expected_handling="auto")

    check("GitHub merge PR to main (prod, irreversible)", EvaluateRequest(
        system="github", action="merge_pr",
        resource=ResourceInfo(resource_name="main"),
        context=ContextInfo(env="prod", visibility="internal", reversible=False),
    ), expected_wave=5, expected_handling="approve")

    check("GitHub merge PR to dev branch (prod)", EvaluateRequest(
        system="github", action="merge_pr",
        resource=ResourceInfo(resource_name="develop"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ), expected_wave=3, expected_handling="check")

    check("GitHub deploy production (irreversible)", EvaluateRequest(
        system="github", action="deploy_production",
        resource=ResourceInfo(resource_name="production"),
        context=ContextInfo(env="prod", visibility="internal", reversible=False),
    ), expected_wave=5, expected_handling="approve")

    # ── EDGE CASES ──
    check("Unknown system (prod)", EvaluateRequest(
        system="salesforce", action="update_record",
        context=ContextInfo(env="prod"),
    ), expected_wave=2, expected_handling="log")

    check("Manual approval override", EvaluateRequest(
        system="slack", action="post_message",
        resource=ResourceInfo(resource_name="general"),
        context=ContextInfo(approval_required_override=True),
    ), expected_wave=5, expected_handling="approve")

    # ── SUMMARY ──
    print(f"\n{'='*60}")
    if failures:
        print(f"  FAILURES ({len(failures)}):")
        for f in failures:
            print(f"    ✗ {f}")
    else:
        print(f"  ALL 17 TESTS PASSED ✓")
    print(f"{'='*60}\n")

    print("CALIBRATION TABLE — Default Wave Mappings v1.1")
    print(f"{'─'*60}")
    print(f"  {'Scenario':<42} {'Wave':<8} {'Handling'}")
    print(f"{'─'*60}")
    for name, wave, handling in [
        ("Slack DM", 1, "auto"),
        ("Slack team channel post", 1, "auto"),
        ("Slack sensitive channel", 3, "check"),
        ("Slack company announcement", 5, "approve"),
        ("Slack external (internal vis)", 4, "approve"),
        ("Slack external (external vis)", 5, "approve"),
        ("Notion create page", 1, "auto"),
        ("Notion update page", 1, "auto"),
        ("Notion protected DB update", 3, "check"),
        ("Notion protected DB (company-wide)", 4, "approve"),
        ("Notion delete page (irreversible)", 4, "approve"),
        ("GitHub push branch (dev)", 1, "auto"),
        ("GitHub create PR", 2, "log"),
        ("GitHub merge PR (dev branch)", 3, "check"),
        ("GitHub merge PR (main, irreversible)", 5, "approve"),
        ("GitHub deploy production", 5, "approve"),
    ]:
        print(f"  {name:<42} Wave {wave:<4} {handling}")
    print(f"{'─'*60}")
    print("\nGuidance: Customers should override defaults when:")
    print("  • A normally-low-risk channel has special significance in their org")
    print("  • Specific actions need stricter/looser handling than the default")
    print("  • Certain branches or databases carry financial/compliance weight")
    print("  • They want to force-block specific action+system combinations")
    print()

    return len(failures) == 0


if __name__ == "__main__":
    success = test_calibrated()
    exit(0 if success else 1)
