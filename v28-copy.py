#!/usr/bin/env python3
"""V2.8 website copy refinements — surgical, no layout changes"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".v28backup")

with open(FILE, "r") as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════
# 1. HERO — refine tagline and add supporting line
# ═══════════════════════════════════════════════════════════

html = html.replace(
    'Agents can act. Surfit makes sure those actions are correct.',
    'Agents can act. Surfit makes sure those actions are correct for your business.'
)

# Add supporting line after the control layer line
html = html.replace(
    '<p class="hero-saw-def" style="margin-top:32px;margin-bottom:32px;font-size:13px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>',
    '<p class="hero-saw-def" style="margin-top:20px;margin-bottom:8px;font-size:13px;">Control and route AI actions across your systems — before they execute.</p>\n    <p class="hero-saw-def" style="margin-bottom:32px;font-size:12px;">Low-risk actions run automatically. High-risk actions are checked or escalated.</p>'
)

# ═══════════════════════════════════════════════════════════
# 2. HERO BADGE — works with any agent framework
# ═══════════════════════════════════════════════════════════

html = html.replace(
    'Works with OpenClaw and proprietary internal agents',
    'Works with any agent framework'
)

# Also fix the bottom tagline
html = html.replace(
    'Works with OpenClaw and proprietary internal agents &nbsp;·&nbsp; Governed by Surfit',
    'Works with any agent framework &nbsp;·&nbsp; Governed by Surfit'
)

# ═══════════════════════════════════════════════════════════
# 3. ADD "WHERE AGENTS FAIL" section — right after hero, before thesis
# ═══════════════════════════════════════════════════════════

oh_shit_section = """
<!-- WHERE AGENTS FAIL -->
<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:60px 48px;">
  <div class="container" style="max-width:800px;text-align:center;">
    <div class="section-label">Where agents fail</div>
    <div style="display:flex;flex-direction:column;gap:12px;margin:24px auto 28px;max-width:600px;text-align:left;">
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent posts confidential data to a public Slack channel</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent merges valid code that breaks your business</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent triggers the wrong workflow across systems</div>
    </div>
    <p style="font-size:14px;color:var(--muted);margin-bottom:8px;">These actions are technically valid — but operationally wrong.</p>
    <p style="font-size:16px;color:var(--blue);font-weight:600;">Surfit prevents this.</p>
  </div>
</section>

"""

html = html.replace(
    '<!-- THESIS -->',
    oh_shit_section + '<!-- THESIS -->'
)

# ═══════════════════════════════════════════════════════════
# 4. THESIS — sharpen the problem statement, add correctness definition
# ═══════════════════════════════════════════════════════════

html = html.replace(
    "Agents don&#x27;t just think — they act.",
    "Agents don't just think — they act."
)

# Replace the thesis body with sharper copy + correctness definition
html = html.replace(
    """AI agents now post messages, publish content, modify systems, and trigger workflows with real business impact.
          
          
          
          <br><br>
          Most systems ensure agents run. Nothing ensures they act correctly for your business. Technically safe doesn't mean correct — an agent can take valid actions with bad business impact. Surfit evaluates every action before execution.""",
    """AI agents now post messages, publish content, modify systems, and trigger workflows with real business impact. Most systems ensure agents run. Nothing ensures they act correctly for your business.
          <br><br>
          <strong style="color:var(--text);">Correct means:</strong><br>
          → the right action<br>
          → in the right place<br>
          → under the right conditions<br>
          → for your business<br><br>
          Surfit evaluates every action before execution."""
)

# ═══════════════════════════════════════════════════════════
# 5. STRENGTHEN WAVE POSITIONING in the flow section
# ═══════════════════════════════════════════════════════════

html = html.replace(
    'Every action flows through the Wave system.',
    'Every action is assigned a risk level.'
)

html = html.replace(
    'Actions are classified into Waves 1-5 based on risk. Low waves execute automatically. High waves are checked or escalated. Every action produces a verifiable execution receipt.',
    'Low → runs automatically. Medium → runs with logging. High → requires checks. Critical → escalated. Execution is controlled dynamically — not blocked by default.'
)

# ═══════════════════════════════════════════════════════════
# 6. AGENT DIAGRAM — update text to "any framework"
# ═══════════════════════════════════════════════════════════

html = html.replace(
    'Any agent framework connects to Surfit. Surfit evaluates and controls execution across\n          all downstream systems.',
    'Agent → Surfit → Systems. Surfit evaluates every action before it reaches your systems.'
)

# Update the OpenClaw box subtitle
html = html.replace(
    'How agents connect through Surfit.',
    'How agents connect through Surfit.'  # keep as is, it's good
)

# Add "Including OpenClaw, LangGraph, and internal systems" under diagram description
html = html.replace(
    'Agent Framework + Sandbox</div>',
    'Agent Framework</div>'
)

html = html.replace(
    'Sandboxed agent execution with network egress control',
    'Including OpenClaw, LangGraph, and internal systems'
)

# ═══════════════════════════════════════════════════════════
# 7. ONE-LINE ARCHITECTURE REINFORCEMENT in the runtime model section
# ═══════════════════════════════════════════════════════════

html = html.replace(
    'Surfit sits between your agents and your systems. Every action is evaluated against your business rules and handled based on risk — from automatic execution to escalation.',
    'Agent → Surfit → Systems. Every action is evaluated against your business rules and handled based on risk — from automatic execution to escalation.'
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ V2.8 copy refinements applied")
print("Deploy: git add index.html && git commit -m 'V2.8 copy refinements' && git push")
