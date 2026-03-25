"""
Round 1: Text-only replacements. No structural HTML changes.
Every replacement is an exact string .replace() call.
If a string isn't found, it skips and reports.

Run from ~/Desktop/files/: python3 patch_round1.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. HERO SUBTITLE — "checked or escalated" → concrete
# ═══════════════════════════════════════════════════════════

old = 'Low-risk actions run automatically. High-risk actions are checked or escalated.'
new = 'Low-risk actions execute automatically. High-risk actions require approval before execution.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1. Hero subtitle fixed")
else:
    print("⚠️  1. Hero subtitle — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 2. WAVE FAQ — simplify definition
# ═══════════════════════════════════════════════════════════

old = 'A Wave is a bounded execution container carrying a pinned policy manifest, execution constraints, and audit lineage for a specific action.'
new = 'A Wave is a risk level assigned to each agent action. Lower-risk Waves execute automatically with logging. Higher-risk Waves are held for approval before execution. Every Wave produces an auditable record of what happened and why.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. Wave FAQ definition simplified")
else:
    print("⚠️  2. Wave FAQ — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 3. ARCHITECTURE CARD 01 — title
# ═══════════════════════════════════════════════════════════

old = '<div class="arch-card-title">Policy-Governed Graph Executor</div>'
new = '<div class="arch-card-title">Policy-Governed Execution Engine</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3a. Arch card 01 title fixed")
else:
    print("⚠️  3a. Arch card 01 title — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 4. ARCHITECTURE CARD 01 — body
# ═══════════════════════════════════════════════════════════

old = 'Graph-based Wave execution with policy check before every tool invocation. Each node is evaluated at runtime. The execution structure is governed — the reasoning inside tool nodes is not constrained.'
new = 'Every agent action passes through policy evaluation before execution. Each action is classified, risk-scored, and routed at runtime. The execution boundary is governed — the agent\'s internal reasoning is not constrained.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3b. Arch card 01 body fixed")
else:
    print("⚠️  3b. Arch card 01 body — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 5. ARCHITECTURE CARD 03 — tag
# ═══════════════════════════════════════════════════════════

old = '<div class="arch-card-tag tag-blue">Intelligence</div>'
new = '<div class="arch-card-tag tag-blue">Control</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4a. Arch card 03 tag fixed")
else:
    print("⚠️  4a. Arch card 03 tag — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 6. ARCHITECTURE CARD 03 — title
# ═══════════════════════════════════════════════════════════

old = '<div class="arch-card-title">Governed LLM Integration</div>'
new = '<div class="arch-card-title">System-Level Action Control</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4b. Arch card 03 title fixed")
else:
    print("⚠️  4b. Arch card 03 title — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 7. ARCHITECTURE CARD 03 — body
# ═══════════════════════════════════════════════════════════

old = 'LLM treated as a tool node — not a privileged actor. Provider, model, prompt boundary, raw input, sanitized input, and output all logged. Write actions are policy-evaluated, not manually reviewed.'
new = 'Agent actions are evaluated at the system boundary — not at the model layer. Surfit governs what agents do to external systems, not how they reason internally. Every write action is policy-evaluated and classified by business context before execution.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4c. Arch card 03 body fixed")
else:
    print("⚠️  4c. Arch card 03 body — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 8. ARCHITECTURE DESCRIPTION — simplify
# ═══════════════════════════════════════════════════════════

old = 'Surfit enforces policy checks before tool invocation, isolates workspace per Wave, anchors policy lineage with hashes, gates mutation paths with wave tokens, and exposes audit verification endpoints.'
new = 'Surfit evaluates every agent action against business policy before execution. Each action is classified by risk, routed to the right team when needed, and recorded with a hash-chained audit trail.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 5. Architecture description simplified")
else:
    print("⚠️  5. Architecture description — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 9. CISOs CARD — remove "scoped mutation tokens"
# ═══════════════════════════════════════════════════════════

old = 'Surfit enforces deterministic boundaries using scoped mutation tokens, policy manifests, and runtime validation before actions are executed.'
new = 'Surfit enforces deterministic boundaries at the execution layer — every agent action is policy-evaluated, risk-classified, and either auto-executed or held for approval before reaching any system.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 6. CISOs card fixed")
else:
    print("⚠️  6. CISOs card — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 10. ENTERPRISE ARCHITECTURE CARD — simplify
# ═══════════════════════════════════════════════════════════

old = 'Surfit provides a neutral governance runtime that sits in the execution path without requiring framework lock-in.'
new = 'Surfit provides a neutral decision layer that sits at the execution boundary — evaluating every agent action in business context regardless of which framework produced it.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 7. Enterprise Architecture card fixed")
else:
    print("⚠️  7. Enterprise Architecture card — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} text replacements applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'round 1: text cleanup — hero, wave, architecture, CISOs, enterprise cards' && git push")
