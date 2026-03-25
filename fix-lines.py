#!/usr/bin/env python3
"""4 surgical line additions — no new sections, no rewrites"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".v29")

with open(FILE, "r") as f:
    html = f.read()

# 1. Wave system — add enforcement line after "Most actions never need a human."
html = html.replace(
    'Most actions never need a human. Execution is controlled dynamically — not blocked by default.',
    'Most actions never need a human. Automatic does not mean unrestricted — execution is still constrained and logged.'
)

# 2. Correctness section — add after the arrow list
html = html.replace(
    '→ for your business<br><br>\n          Surfit evaluates every action before execution.',
    '→ for your business<br><br>\n          Correctness is defined by your policies — not the agent. Surfit evaluates every action before execution.'
)

# 3. Enforcement line — add to the diagram summary
html = html.replace(
    'Surfit controls <span style="color:var(--blue);font-weight:500;">whether the action is correct.</span></p>',
    'Surfit controls <span style="color:var(--blue);font-weight:500;">whether the action is correct.</span> Surfit doesn\'t just decide — it enforces.</p>'
)

# 4. Inevitability line — add to CTA section
html = html.replace(
    'Surfit is the control layer for agent actions. Every action evaluated, every decision explained, every outcome recorded — across every system your agents touch.',
    'As agents gain autonomy, a control layer becomes required — not optional. Every action evaluated, every decision explained, every outcome recorded — across every system your agents touch.'
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ 4 lines added")
print("Deploy: git add index.html && git commit -m 'Copy refinements' && git push")
