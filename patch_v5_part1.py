"""
V5 POSITIONING — Part 1
Hero, Thesis, Agent Integration, Gap section updates.
All exact string replacements. No structural changes.

Run from ~/Desktop/files/: python3 patch_v5_part1.py
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
# 1. HERO — new tagline + remove redundant lines
# ═══════════════════════════════════════════════════════════

safe_replace("1a. Hero tagline",
    '<p class="hero-tagline">Agents can act. Surfit makes sure those actions are correct for your business.</p>',
    '<p class="hero-tagline">Your agents are ready to act. Surfit is how they do it right.</p>')

safe_replace("1b. Hero sub line 1 — remove",
    '<p class="hero-saw-def" style="margin-top:20px;margin-bottom:8px;font-size:13px;">Control and route AI actions across your systems — before they execute.</p>',
    '')

safe_replace("1c. Hero sub line 2 — rewrite",
    '<p class="hero-saw-def" style="margin-bottom:32px;font-size:12px;">Low-risk actions execute automatically. High-risk actions require approval before execution.</p>',
    '<p class="hero-saw-def" style="margin-top:20px;margin-bottom:32px;font-size:13px;">Low-risk flows instantly. High-risk gets routed. Everything gets a receipt.</p>')


# ═══════════════════════════════════════════════════════════
# 2. THESIS — title, body, evals block, credential line, PR example
# ═══════════════════════════════════════════════════════════

safe_replace("2a. Thesis title",
    '''Agents don't just think — they act.
          <span class="accent-blue"> The missing layer is correctness.</span>''',
    '''Agents don't just think — they act.
          <span class="accent-blue"> The missing layer is the one that lets you say yes.</span>''')

safe_replace("2b. Thesis body",
    'AI agents now post messages, publish content, modify systems, and trigger workflows with real business impact. Most systems ensure agents run. Nothing ensures they act correctly for your business.',
    'AI agents now post messages, publish content, modify systems, and trigger workflows with real business impact. Most systems ensure agents run. Nothing gives them the authority to act on real business systems with confidence. <strong style="color:var(--blue);">Surfit is that authority.</strong>')

safe_replace("2c. Thesis point 1 — Policy-Driven Execution",
    '<strong>Policy-Driven Execution</strong>\n            <p>Every action is classified by risk and handled according to your business rules. Low-risk actions execute automatically. High-risk actions are checked or escalated.</p>',
    '<strong>Policy-Driven Execution</strong>\n            <p>Every action is classified by risk and handled according to your business rules. Low-risk actions execute instantly. High-risk actions get routed by Surfit for business context.</p>')

safe_replace("2d. Evals block right title",
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Surfit = Control</div>',
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Surfit = Execution Authority</div>')

safe_replace("2e. Evals block right body",
    'Agent does not hold credentials.<br>Every action must pass through Surfit.<br><strong style="color:var(--blue);">Surfit decides, then executes.</strong>',
    'The agent does not hold credentials.<br>Every action flows through Surfit.<br>Surfit evaluates in business context and executes on behalf of the agent.<br><strong style="color:var(--blue);">The agent proposes. Surfit acts.</strong>')

safe_replace("2f. Credential line",
    'If the agent holds the credentials, governance is advisory.<br>If an external layer holds them, governance is enforceable.',
    'If the agent holds the credentials, it governs itself.<br><strong style="color:var(--blue);">If Surfit holds them, the business governs the agent.</strong>')

safe_replace("2g. PR example ending",
    '→ <strong style="color:var(--blue);">Holds the action. Business protected.</strong>',
    '→ <strong style="color:var(--blue);">Surfit holds the action. Evaluates context. Executes when correct. Business protected.</strong>')


# ═══════════════════════════════════════════════════════════
# 3. AGENT INTEGRATION — title + bottom line
# ═══════════════════════════════════════════════════════════

safe_replace("3a. Agent Integration title",
    '<div class="section-title brand-heading">How agents connect through Surfit.</div>',
    '<div class="section-title brand-heading">How agents operate through Surfit.</div>')

safe_replace("3b. Agent Integration bottom line",
    'Frameworks decide <span style="color:var(--orange);font-weight:500;">what</span> to do. Sandboxes control <span style="color:#a78bfa;font-weight:500;">where</span> agents run. Surfit controls <span style="color:var(--blue);font-weight:500;">whether the action is correct.</span> Surfit doesn\'t just decide — it enforces.',
    'Frameworks decide <span style="color:var(--orange);font-weight:500;">what</span> to do. Sandboxes control <span style="color:#a78bfa;font-weight:500;">where</span> agents run. <span style="color:var(--blue);font-weight:500;">Surfit is where execution actually happens.</span>')


# ═══════════════════════════════════════════════════════════
# 4. GAP — title + punchline + summary
# ═══════════════════════════════════════════════════════════

safe_replace("4a. Gap title",
    '<div class="section-title brand-heading" style="">The agent has credentials.<br>Who decides what it does with them?</div>',
    '<div class="section-title brand-heading" style="">What can agents do through Surfit —<br>and what happens without it?</div>')

safe_replace("4b. Gap subtitle",
    '<p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;">Every existing tool says yes. Nobody asks whether it should happen.</p>',
    '')

safe_replace("4c. Gap punchline",
    'Guardrails AI and CTGT never saw the action — they only check the model\'s words, not what the agent does with them. IronClaw granted access because the agent needed it — but access control ends at the door. Once the agent was inside with live credentials, it merged directly to production. No layer evaluated whether it should. No one was in the path.',
    'Every layer said yes. Nothing evaluated business context. Nothing was in the execution path. The agent held the credentials and acted alone.')

safe_replace("4d. Gap summary line",
    'The agent never held the credentials. Surfit evaluated every action in business context.<br><br>Routine actions flowed instantly across five systems. Pre-defined high-risk actions were caught. The business stayed protected.',
    'The agent never held the credentials. Surfit evaluated every action in business context.<br><br>5 actions executed instantly across multiple systems. Zero friction on routine work. High-risk actions held by Surfit for business context. Full audit trail on everything.')


# ═══════════════════════════════════════════════════════════
# 5. NAV — rename The Gap to Why Surfit
# ═══════════════════════════════════════════════════════════

safe_replace("5. Nav — The Gap → Why Surfit",
    '<li><a href="#the-gap">The Gap</a></li>',
    '<li><a href="#the-gap">Why Surfit</a></li>')


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Part 1 done — {changes} changes applied")
print("If broken: git checkout index.html")
print("Run Part 2 next: python3 patch_v5_part2.py")
