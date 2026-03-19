"""
SURFIT Wave Engine — Test Suite
Walks through all required examples from the directive.
"""

import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo
from surfit_wave.policy import load_default_policy


def print_result(label, result):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Wave:      {result.wave_label} (score={result.wave_score}, raw={result.raw_score})")
    print(f"  Handling:  {result.handling}")
    print(f"  Dest:      {result.destination_class_resolved}")
    print(f"  Reasons:")
    for r in result.reasons:
        print(f"    → {r}")
    print(f"  Factors:")
    for f in result.contributing_factors:
        print(f"    [{f.source}] {f.key} = {f.modifier:+d}  ({f.description})")
    print()


def test_all():
    engine = WaveEngine()

    # ── A. Slack DM ──
    # Expected: low baseline, dm destination, Wave 1-2, auto/log
    result_a = engine.evaluate(EvaluateRequest(
        system="slack",
        action="post_dm",
        resource=ResourceInfo(resource_id="D0ABC123", resource_name=None),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ))
    print_result("A. Slack DM", result_a)
    assert result_a.wave_score <= 2, f"Slack DM should be Wave 1-2, got {result_a.wave_score}"
    assert result_a.handling in ("auto", "log"), f"Slack DM should be auto/log, got {result_a.handling}"
    assert result_a.destination_class_resolved == "dm"

    # ── B. Slack Company Announcement ──
    # Expected: announcement dest, company_wide visibility, Wave 4-5, approve
    result_b = engine.evaluate(EvaluateRequest(
        system="slack",
        action="post_announcement",
        resource=ResourceInfo(resource_name="company-announcements"),
        context=ContextInfo(env="prod", visibility="company_wide", reversible=True),
    ))
    print_result("B. Slack Company Announcement", result_b)
    assert result_b.wave_score >= 4, f"Slack announcement should be Wave 4+, got {result_b.wave_score}"
    assert result_b.handling in ("approve", "check"), f"Slack announcement should be approve/check, got {result_b.handling}"
    assert result_b.destination_class_resolved == "company_announcement"

    # ── C. Notion Database Update ──
    # Expected: medium baseline, structured data, Wave 3, check
    result_c = engine.evaluate(EvaluateRequest(
        system="notion",
        action="update_database_entry",
        resource=ResourceInfo(resource_name="Sprint Tracker"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ))
    print_result("C. Notion Database Update", result_c)
    assert result_c.wave_score >= 3, f"Notion DB update should be Wave 3+, got {result_c.wave_score}"
    assert result_c.handling in ("check", "approve")

    # ── D. GitHub Create PR ──
    # Expected: medium-high, code change, Wave 3, check
    result_d = engine.evaluate(EvaluateRequest(
        system="github",
        action="create_pr",
        resource=ResourceInfo(resource_name="feature-branch"),
        context=ContextInfo(env="prod", visibility="internal", reversible=True),
    ))
    print_result("D. GitHub Create PR", result_d)
    assert result_d.wave_score >= 3, f"GitHub create PR should be Wave 3+, got {result_d.wave_score}"
    assert result_d.handling in ("check", "approve")

    # ── E. GitHub Merge PR to main/prod ──
    # Expected: irreversible, production, Wave 5, approve
    result_e = engine.evaluate(EvaluateRequest(
        system="github",
        action="merge_pr",
        resource=ResourceInfo(resource_name="main"),
        context=ContextInfo(env="prod", visibility="internal", reversible=False),
    ))
    print_result("E. GitHub Merge PR to main (prod, irreversible)", result_e)
    assert result_e.wave_score == 5, f"GitHub merge to main should be Wave 5, got {result_e.wave_score}"
    assert result_e.handling == "approve"

    # ── ADDITIONAL: Edge cases ──

    # F. Unknown system
    result_f = engine.evaluate(EvaluateRequest(
        system="salesforce",
        action="update_record",
        context=ContextInfo(env="prod"),
    ))
    print_result("F. Unknown System (salesforce)", result_f)
    assert result_f.wave_score >= 2  # defaults to moderate

    # G. Slack external channel
    result_g = engine.evaluate(EvaluateRequest(
        system="slack",
        action="post_message",
        resource=ResourceInfo(resource_name="external-partner-channel"),
        context=ContextInfo(env="prod", visibility="external"),
    ))
    print_result("G. Slack External Channel", result_g)
    assert result_g.wave_score >= 4
    assert result_g.destination_class_resolved == "external_shared_channel"

    # H. Dev environment (should reduce risk)
    result_h = engine.evaluate(EvaluateRequest(
        system="github",
        action="merge_pr",
        resource=ResourceInfo(resource_name="dev-branch"),
        context=ContextInfo(env="dev", visibility="internal", reversible=True),
    ))
    print_result("H. GitHub Merge PR (dev env, reversible)", result_h)
    assert result_h.wave_score < result_e.wave_score, "Dev env merge should be lower wave than prod"

    # I. Approval override
    result_i = engine.evaluate(EvaluateRequest(
        system="slack",
        action="post_message",
        resource=ResourceInfo(resource_name="general"),
        context=ContextInfo(approval_required_override=True),
    ))
    print_result("I. Manual Approval Override", result_i)
    assert result_i.wave_score == 5
    assert result_i.handling == "approve"

    print("\n" + "="*60)
    print("  ALL TESTS PASSED ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_all()
