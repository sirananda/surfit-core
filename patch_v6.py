"""
V6 POSITIONING — Surgical updates
1. Hero: Smart. Safe. Correct.
2. Thesis evals block: Policy Enforcement vs Business Decisions
3. Credential line: demote, add "but credential separation only determines access"
4. Landscape Surfit badge: WHERE BUSINESS DECISIONS HAPPEN
5. Landscape Surfit card body: decision-first, credentials supporting
6. Dominance point 1: add IronCurtain acknowledgment
7. FAQ: reframe What is Surfit
8. Credential line in thesis: add the "but" line

Run from ~/Desktop/files/: python3 patch_v6.py
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
# 1. HERO — Smart. Safe. Correct.
# ═══════════════════════════════════════════════════════════

safe_replace("1. Hero category line",
    '<p style="font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;font-weight:600;">Evals don\'t control execution. Surfit does.</p>',
    '<p style="font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);margin-bottom:8px;font-weight:600;"><span style="color:var(--orange);">Smart.</span> <span style="color:var(--orange);">Safe.</span> <span style="color:var(--blue);">Correct.</span> — Everyone builds the first two. <span style="color:var(--blue);">Surfit is the third.</span></p>')


# ═══════════════════════════════════════════════════════════
# 2. THESIS — Evals block: Policy Enforcement vs Business Decisions
# ═══════════════════════════════════════════════════════════

safe_replace("2a. Evals block left title",
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--red);margin-bottom:10px;font-weight:600;">Evals ≠ Control</div>',
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--orange);margin-bottom:10px;font-weight:600;">Policy Enforcement</div>')

safe_replace("2b. Evals block left body",
    'Evals run inside the agent.<br>They can flag, warn, or suggest.<br><strong style="color:var(--red);">But the agent still executes.</strong>',
    'Rules-based. Static. Runs inside the runtime.<br>Checks permissions. Agent passes policy.<br><strong style="color:var(--orange);">But was it the right action right now?</strong>')

safe_replace("2c. Evals block left border",
    'background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25)',
    'background:rgba(255,115,30,0.06);border:1px solid rgba(255,115,30,0.25)')

safe_replace("2d. Evals block right title",
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Surfit = Execution Authority</div>',
    '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Business Decisions</div>')

safe_replace("2e. Evals block right body",
    'The agent does not hold credentials.<br>Every action flows through Surfit.<br>Surfit evaluates in business context and executes on behalf of the agent.<br><strong style="color:var(--blue);">The agent proposes. Surfit acts.</strong>',
    'Evaluates context, timing, risk, impact.<br>Routes to the right person when needed.<br>Executes or holds based on business context.<br><strong style="color:var(--blue);">Not rules — decisions. That\'s Surfit.</strong>')


# ═══════════════════════════════════════════════════════════
# 3. CREDENTIAL LINE — demote, add "but" clause
# ═══════════════════════════════════════════════════════════

safe_replace("3. Credential line — add context limitation",
    'If the agent holds the credentials, it governs itself.<br><strong style="color:var(--blue);">If Surfit holds them, the business governs the agent.</strong>',
    'If the agent holds the credentials, it governs itself.<br><strong style="color:var(--blue);">If Surfit holds them, the business governs the agent.</strong><br><span style="font-size:12px;color:var(--muted);font-style:normal;">Credential separation determines access. Business correctness requires context that no policy file can encode.</span>')


# ═══════════════════════════════════════════════════════════
# 4. LANDSCAPE — Surfit badge
# ═══════════════════════════════════════════════════════════

safe_replace("4. Landscape Surfit badge",
    'WHERE EXECUTION HAPPENS',
    'WHERE BUSINESS DECISIONS HAPPEN')


# ═══════════════════════════════════════════════════════════
# 5. LANDSCAPE — Surfit card body: decision-first
# ═══════════════════════════════════════════════════════════

safe_replace("5. Landscape Surfit card body",
    'Every tool above feeds into the agent. Surfit is where the agent\'s output becomes real. The agent proposes. Surfit evaluates in business context. Surfit holds the credentials. Surfit executes. This is not another layer in the stack — this is the layer the stack was missing.',
    'Every tool above makes agents smarter or safer to run. Surfit is where those agents go when they need to actually do something. The agent proposes. Surfit evaluates business context — timing, risk, impact, organizational rules. This is not another policy engine. This is the decision layer the stack was missing.')

safe_replace("5b. Landscape Surfit answer",
    'Answers: "Is this the right action for the business right now?"',
    'Answers: "Should this action happen right now — given what\'s at stake for the business?"')


# ═══════════════════════════════════════════════════════════
# 6. DOMINANCE — Point 1: acknowledge IronCurtain, add distinction
# ═══════════════════════════════════════════════════════════

safe_replace("6. Dominance point 1 — credential + context",
    '• <strong style="color:var(--blue);">Credential separation is architectural, not optional.</strong> If the agent holds the credentials, governance is advisory. If an external layer holds them, governance is enforceable.<br>',
    '• <strong style="color:var(--blue);">Credential separation is necessary but not sufficient.</strong> Multiple tools now separate credentials from agents — that pattern is becoming standard. But credential separation only determines what the agent can access. It does not evaluate whether a specific action is correct for the business right now. Access control is Layer 2. Business decisions are Layer 3.<br>')


# ═══════════════════════════════════════════════════════════
# 7. FAQ — reframe What is Surfit (decision-first, not credential-first)
# ═══════════════════════════════════════════════════════════

safe_replace("7. FAQ — What is Surfit",
    'Surfit is the execution layer for AI agent actions. Agents propose actions. Surfit evaluates each one in business context, executes low-risk actions instantly, holds high-risk actions for routing, and produces a full audit trail. Surfit holds the credentials — the agent never executes directly on business systems.',
    'Surfit is the decision layer for AI agent actions. Agents propose actions. Surfit evaluates each one in business context — not just whether it\'s permitted, but whether it\'s the right action for the organization right now. Low-risk actions execute instantly. High-risk actions are routed for context. Everything produces a receipt. Surfit sits externally, holds credentials, and enforces decisions architecturally — the agent cannot bypass what it cannot reach.')


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ V6 done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If good: git add -A && git commit -m 'V6: Smart Safe Correct, business decisions framing, credential demotion' && git push")
