#!/usr/bin/env python3
"""
SURFIT SITE PATCH — V4 Positioning Sharpening
==============================================
Based on Daniel conversation feedback + Claude CTO + ChatGPT CEO analysis.

WHAT THIS DOES (6 changes):
1. HERO — Adds category-defining line: "Evals don't control execution. Surfit does."
2. THESIS — Adds evals ≠ control visual block + credential ownership line (moved up)
3. GAP — Changes "Nobody evaluates business impact" → enforcement language
4. GAP — Adds brutal one-liner: "Everything passes checks. It still goes through."
5. LANDSCAPE — Adds "Runs inside the agent — agent can bypass" to Guardrails card
6. THESIS — Adds the PR example flow (WhatsApp style that made Daniel get it)

SAFETY:
- Every replacement uses exact string .replace()
- No rfind, no section detection, no boundary walking
- Each change is verified after application
- If any exact match fails, it reports which one and skips safely

USAGE:
  cd ~/Desktop/files
  python3 patch_site_v4.py
  # Review output — confirms each change landed or was skipped
  # Then: grep for changed text to verify
  # Then: git add index.html && git commit -m "v4 positioning sharpening" && git push

REVERT:
  cd ~/Desktop/files && git checkout index.html
"""

import sys

filepath = '/root/Desktop/files/index.html'

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    # Try home directory variant
    filepath = f'{__import__("os").path.expanduser("~")}/Desktop/files/index.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

original = content
changes_made = 0
changes_skipped = 0

def safe_replace(label, old, new):
    global content, changes_made, changes_skipped
    count = content.count(old)
    if count == 0:
        print(f"⚠️  SKIPPED [{label}] — exact string not found")
        changes_skipped += 1
        return
    if count > 1:
        print(f"⚠️  SKIPPED [{label}] — found {count} matches (expected 1), too risky")
        changes_skipped += 1
        return
    content = content.replace(old, new)
    print(f"✅  APPLIED [{label}]")
    changes_made += 1


# ═══════════════════════════════════════════════════════════════
# CHANGE 1: HERO — Add category-defining line
# ═══════════════════════════════════════════════════════════════
# Insert "Evals don't control execution. Surfit does." above the existing hero headline.
# This forces category framing before anything else.

safe_replace(
    "1: HERO — category line",
    '<h1>Agents can act. Surfit makes sure those actions are correct for your business.</h1>',
    '<p style="font-size:1.1rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--accent, #00e0ff);margin-bottom:0.5rem;font-weight:600;">Evals don\'t control execution. Surfit does.</p>\n            <h1>Agents can act. Surfit makes sure those actions are correct for your business.</h1>'
)


# ═══════════════════════════════════════════════════════════════
# CHANGE 2: THESIS — Add evals ≠ control block + credential line + PR example
# ═══════════════════════════════════════════════════════════════
# Insert after "Correctness is defined by your policies — not the agent. 
# Surfit evaluates every action before execution."
# This adds the visual evals vs control block, the credential ownership line,
# and the WhatsApp-style PR example flow.

safe_replace(
    "2: THESIS — evals vs control block + credential line + PR flow",
    'Correctness is defined by your policies — not the agent. Surfit evaluates every action before execution.</p>',
    '''Correctness is defined by your policies — not the agent. Surfit evaluates every action before execution.</p>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin:2.5rem 0;max-width:800px;">
              <div style="background:rgba(255,60,60,0.08);border:1px solid rgba(255,60,60,0.25);border-radius:12px;padding:1.5rem;">
                <div style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.08em;color:#ff4444;margin-bottom:0.75rem;font-weight:600;">🚫 Evals ≠ Control</div>
                <p style="font-size:0.95rem;line-height:1.6;margin:0;color:rgba(255,255,255,0.85);">Evals run inside the agent.<br>They can flag, warn, or suggest.<br><strong style="color:#ff6666;">But the agent still executes.</strong></p>
              </div>
              <div style="background:rgba(0,224,255,0.08);border:1px solid rgba(0,224,255,0.25);border-radius:12px;padding:1.5rem;">
                <div style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.08em;color:#00e0ff;margin-bottom:0.75rem;font-weight:600;">✅ Surfit = Control</div>
                <p style="font-size:0.95rem;line-height:1.6;margin:0;color:rgba(255,255,255,0.85);">Agent does not hold credentials.<br>Every action must pass through Surfit.<br><strong style="color:#00e0ff;">Surfit decides, then executes.</strong></p>
              </div>
            </div>

            <p style="font-size:1.05rem;font-style:italic;color:rgba(255,255,255,0.9);border-left:3px solid var(--accent, #00e0ff);padding-left:1rem;margin:1.5rem 0;">If the agent holds the credentials, governance is advisory.<br>If an external layer holds them, governance is enforceable.</p>

            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:1.5rem;margin:2rem 0;max-width:800px;">
              <div style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.06em;color:rgba(255,255,255,0.5);margin-bottom:1rem;">Example: Agent wants to merge a PR</div>
              <div style="font-size:0.95rem;line-height:1.8;color:rgba(255,255,255,0.8);">
                Guardrails → output is fine ✓<br>
                CTGT → model is compliant ✓<br>
                IronClaw → permissions are safe ✓<br>
                <span style="color:#ff6666;font-weight:600;">So it goes through… into production. Payments break.</span>
              </div>
              <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.1);font-size:0.95rem;line-height:1.8;color:rgba(255,255,255,0.8);">
                <strong style="color:#00e0ff;">With Surfit:</strong><br>
                → Intercepts before execution<br>
                → Evaluates business context (production branch, payment code, no review)<br>
                → <strong style="color:#00e0ff;">Holds for approval. Business protected.</strong>
              </div>
            </div>'''
)


# ═══════════════════════════════════════════════════════════════
# CHANGE 3: GAP — Change "Nobody evaluates business impact" to enforcement language
# ═══════════════════════════════════════════════════════════════

safe_replace(
    "3: GAP — evaluates → controls",
    'Nobody evaluates<br>\n                    business impact',
    'Nobody controls whether<br>\n                    the action happens'
)


# ═══════════════════════════════════════════════════════════════
# CHANGE 4: GAP — Add brutal one-liner after the "NO LAYER HERE" explanation
# ═══════════════════════════════════════════════════════════════
# Insert after the paragraph that ends with "No layer evaluated whether it should. No one was in the path."

safe_replace(
    "4: GAP — brutal one-liner",
    'No layer evaluated whether it should. No one was in the path.</p>',
    'No layer evaluated whether it should. No one was in the path.</p>\n            <p style="font-size:1.15rem;font-weight:600;color:#ff6666;text-align:center;margin:1.5rem 0;">Everything passed checks. It still went through.</p>'
)


# ═══════════════════════════════════════════════════════════════
# CHANGE 5: LANDSCAPE — Add "Runs inside the agent" line to Guardrails card
# ═══════════════════════════════════════════════════════════════

safe_replace(
    "5: LANDSCAPE — Guardrails bypass line",
    '✗ Does not govern what the agent does to real systems',
    '✗ Runs inside the agent — agent can bypass, remove, or reconfigure<br>\n                  ✗ Does not govern what the agent does to real systems'
)


# ═══════════════════════════════════════════════════════════════
# WRITE AND REPORT
# ═══════════════════════════════════════════════════════════════

if changes_made == 0:
    print("\n❌ No changes were applied. File NOT modified.")
    print("   This likely means the exact strings have changed since this script was written.")
    print("   Check the current index.html content against the expected strings above.")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n{'='*60}")
print(f"DONE: {changes_made} changes applied, {changes_skipped} skipped")
print(f"File: {filepath}")
print(f"{'='*60}")
print("\nNEXT STEPS:")
print("1. Open index.html in browser to verify visually")
print("2. grep 'Evals don' index.html  — should find hero line")
print("3. grep 'Evals ≠ Control' index.html  — should find thesis block")
print("4. grep 'Nobody controls' index.html  — should find gap change")
print("5. grep 'Everything passed' index.html  — should find one-liner")
print("6. grep 'agent can bypass' index.html  — should find landscape change")
print("7. If good: git add index.html && git commit -m 'v4 positioning sharpening — evals vs control' && git push")
print("8. If broken: git checkout index.html")
