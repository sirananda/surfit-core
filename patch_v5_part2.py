"""
V5 POSITIONING — Part 2
Landscape, Who Needs Surfit, Platform, Scare Table, Dominance, FAQ, CTA.
All exact string replacements.

Run from ~/Desktop/files/: python3 patch_v5_part2.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

def safe_replace(label, old, new):
    global content, changes
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"✅ {label}")
    else:
        print(f"⚠️  {label} — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 1. LANDSCAPE — title + Surfit card body + competitor endings
# ═══════════════════════════════════════════════════════════

safe_replace("1a. Landscape title",
    '<div class="section-title brand-heading" style="">Every tool solves a different problem.<br>None of them solve this one.</div>',
    '<div class="section-title brand-heading" style="">Every tool makes agents capable.<br>Surfit is where capable agents execute.</div>')

safe_replace("1b. Landscape Surfit card body",
    'Surfit sits at the execution boundary — between the agent and every system it touches. Every action is intercepted, evaluated in business context, and either auto-executed or routed to the right team. The agent proposes. Surfit decides whether it should happen.',
    'Every tool above feeds into the agent. Surfit is where the agent\'s output becomes real. The agent proposes. Surfit evaluates in business context. Surfit holds the credentials. Surfit executes. This is not another layer in the stack — this is the layer the stack was missing.')

safe_replace("1c. Landscape Surfit badge",
    'DIFFERENT LAYER',
    'WHERE EXECUTION HAPPENS')

safe_replace("1d. Landscape Surfit answer",
    'Answers: "Is this the right action for the business right now — and does the right person know?"',
    'Answers: "Is this the right action for the business right now?"')

# Competitor card endings — change ✗ to → flow language
safe_replace("1e. Guardrails card ending",
    '✗ Runs inside the agent — agent can bypass, remove, or reconfigure',
    '→ Makes the output safe. The agent still executes on its own')

safe_replace("1f. CTGT card ending",
    '✗ Does not sit at the execution boundary of real systems',
    '→ Makes the model compliant. The agent still executes on its own')

safe_replace("1g. IronClaw card ending",
    '✗ Once access is granted, no business-level decision control',
    '→ Grants access. The agent still executes on its own')

safe_replace("1h. CrowdStrike card ending",
    '✗ No concept of business context or action correctness',
    '→ Secures infrastructure. The agent still executes on its own')

safe_replace("1i. OpenClaw card ending",
    '✗ Self-regulation is not enforcement — internal controls are optional and framework-bound',
    '→ Decides what to do. The agent still executes on its own')


# ═══════════════════════════════════════════════════════════
# 2. WHO NEEDS SURFIT — title + subtitle
# ═══════════════════════════════════════════════════════════

safe_replace("2a. Who Needs title",
    '<div class="section-title brand-heading" style="">Organizations deploying high-authority AI agents into real operational environments.</div>',
    '<div class="section-title brand-heading" style="">Organizations ready to make agents operational.</div>')

safe_replace("2b. Who Needs subtitle",
    'Surfit is designed for teams that want to move agents beyond advisory roles without losing deterministic control over execution.',
    'Surfit is how teams move agents from advisory to operational — with every action evaluated, every decision accounted for.')


# ═══════════════════════════════════════════════════════════
# 3. PLATFORM CAPABILITIES — add Ripple to roadmap
# ═══════════════════════════════════════════════════════════

safe_replace("3. Platform — add Ripple Workflows",
    'SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria',
    'SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria</span></div><div style="margin-bottom:0;">• <strong style="color:var(--text);">Ripple Workflows</strong><br><span style="color:var(--muted);">When a pre-defined action completes in one system, Surfit initiates the next action in the next system. One agent action cascades across systems under defined conditions, each step evaluated and executed by Surfit</span>')


# ═══════════════════════════════════════════════════════════
# 4. WHERE AGENTS FAIL — title + framing
# ═══════════════════════════════════════════════════════════

safe_replace("4a. Scare table label",
    '>Where agents fail</div>',
    '>What happens when agents execute alone</div>')

safe_replace("4b. Scare table punchline",
    'Every action above was technically valid — but operationally wrong.',
    'Every action above was technically valid. The agent had credentials. No layer evaluated business context. The agent executed alone.')


# ═══════════════════════════════════════════════════════════
# 5. DOMINANCE — title + add point 6 + update points 2 and 4
# ═══════════════════════════════════════════════════════════

safe_replace("5a. Dominance title",
    'Agent control requires a dedicated layer.',
    'Why this layer becomes the center of agent operations.')

safe_replace("5b. Dominance point 2",
    '<strong style="color:var(--blue);">Business context cannot live inside the agent.</strong> The agent knows what it wants to do. It does not know whether this is the right action for the organization right now.',
    '<strong style="color:var(--blue);">The agent knows what it wants to do. Surfit knows whether it should happen for the business.</strong> These are different functions that require different systems.')

safe_replace("5c. Dominance point 4",
    '<strong style="color:var(--blue);">Self-regulation is not enforcement.</strong> When governance lives inside the agent framework, it is controlled by the same system it is supposed to constrain. Independent control requires architectural separation.',
    '<strong style="color:var(--blue);">When the agent governs itself, governance is optional.</strong> When Surfit governs the execution path, governance is architectural. The agent cannot bypass what it cannot reach.')

# Add point 6 after point 5
safe_replace("5d. Dominance add point 6",
    'independent of the agent\'s own reporting.\n        </div>',
    'independent of the agent\'s own reporting.<br>\n          • <strong style="color:var(--blue);">Every system connected to Surfit increases the value of routing through it.</strong> Every agent added benefits from policies already in place. This is infrastructure that compounds — the more you route through Surfit, the stronger it becomes.\n        </div>')


# ═══════════════════════════════════════════════════════════
# 6. FAQ — update What is Surfit + add new FAQs
# ═══════════════════════════════════════════════════════════

safe_replace("6a. FAQ — What is Surfit",
    'Surfit is a control layer for AI agents that evaluates every action against your business rules before execution — governing actions across Slack, GitHub, X, Notion, Gmail, Outlook, AWS, and more based on risk.',
    'Surfit is the execution layer for AI agent actions. Agents propose actions. Surfit evaluates each one in business context, executes low-risk actions instantly, holds high-risk actions for routing, and produces a full audit trail. Surfit holds the credentials — the agent never executes directly on business systems.')

# Add two new FAQ entries after the OpenClaw one
safe_replace("6b. FAQ — add Does Surfit slow down + Why can't we build",
    'The agent can\'t override Surfit because Surfit holds the execution credentials, not the agent.</p></div>',
    'The agent can\'t override Surfit because Surfit holds the execution credentials, not the agent.</p></div>\n      <div class="faq-item"><h4>Does Surfit slow down agents?</h4><p>No. Most actions execute instantly through Surfit with full logging. Surfit only holds actions where business context demands it. Routine work flows without friction. Surfit is designed to make agents faster to deploy, not slower to operate.</p></div>\n      <div class="faq-item"><h4>Why can\'t we just add this to our agent framework?</h4><p>Because the agent would still hold the credentials. Any governance that lives inside the agent is controlled by the agent. Surfit sits outside — it holds the credentials, evaluates the actions, and executes on behalf of the agent. That architectural separation is what makes governance real, not optional.</p></div>')


# ═══════════════════════════════════════════════════════════
# 7. CTA — new language
# ═══════════════════════════════════════════════════════════

safe_replace("7a. CTA title",
    'Decide what gets executed —<br>before it happens.',
    'Let your agents operate.<br>Surfit is in the path.')

safe_replace("7b. CTA body",
    'As agents gain autonomy, a control layer becomes required — not optional. Every action evaluated, every decision explained, every outcome recorded — across every system your agents touch.',
    'Start with one system. Route your agent\'s actions through Surfit. See what flows instantly, what gets held for context, and what gets receipted. Every system you connect makes the next one stronger.')


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Part 2 done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If all good: git add -A && git commit -m 'V5 positioning: enablement framing, execution authority, gravitational language' && git push")
