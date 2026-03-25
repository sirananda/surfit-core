"""
Round 5: Final polish.
1. Better punchline metaphor
2. Replace 💥 with ✕ CATASTROPHE
3. Remove Architecture section (Built in layers)
4. Remove 9 capability cards, keep Live/In Progress only under "Platform Capabilities"
5. Brighten Pre-built Agent Logic and Internal Builds labels
6. Beef up "Why This Requires a Dedicated Layer" — not about human approval

Run from ~/Desktop/files/: python3 patch_round5.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. BETTER PUNCHLINE
# ═══════════════════════════════════════════════════════════

old = 'Guardrails AI and CTGT checked the words. IronClaw and NemoClaw checked the door. The agent had the keys the entire time.'
new = 'Guardrails AI and CTGT validated the output. IronClaw and NemoClaw controlled the access. But the agent held the credentials — and no one evaluated whether the action was correct for the business.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1. Punchline rewritten")
else:
    print("⚠️  1. Punchline — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 2. REPLACE 💥 WITH ✕ CATASTROPHE
# ═══════════════════════════════════════════════════════════

old = '<div style="font-size:18px;margin-bottom:4px;">💥</div>\n          <div style="font-size:10px;color:var(--red);font-weight:700;margin-bottom:4px;">PRODUCTION</div>'
new = '<div style="font-size:28px;font-weight:900;color:var(--red);margin-bottom:4px;">✕</div>\n          <div style="font-size:10px;color:var(--red);font-weight:700;margin-bottom:4px;letter-spacing:.1em;">CATASTROPHE</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. 💥 replaced with ✕ CATASTROPHE")
else:
    print("⚠️  2. 💥 icon — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 3. REMOVE ARCHITECTURE SECTION entirely
# ═══════════════════════════════════════════════════════════

arch_start = '<!-- ARCHITECTURE -->'
arch_end = '<!-- WHO NEEDS SURFIT -->'

if arch_start in content and arch_end in content:
    s = content.index(arch_start)
    e = content.index(arch_end)
    content = content[:s] + '\n' + content[e:]
    changes += 1
    print("✅ 3. Removed Architecture section")
else:
    print("⚠️  3. Architecture section — markers not found, skipping")


# ═══════════════════════════════════════════════════════════
# 4. REMOVE 9 capability cards, restructure section
#    Keep "What Surfit does today." as title
#    Remove the runtime-grid of 9 cards
#    Keep the Live/In Progress below it
# ═══════════════════════════════════════════════════════════

old_caps = '''    <div class="section-title brand-heading" style="">What Surfit does today.</div>

    <div class="runtime-grid" style="margin-top:26px;">
      <div class="runtime-card"><h4>Runtime Execution Enforcement</h4><p>Every agent action is evaluated against business policy before execution. Actions are classified, risk-scored, and routed — automatically or to human approval.</p></div>
      <div class="runtime-card"><h4>Wave Risk Classification</h4><p>Deterministic risk scoring across five levels. Wave 1–3 execute automatically with full logging. Wave 4–5 require operator approval. Risk is computed per action, not per system.</p></div>
      <div class="runtime-card"><h4>Cross-System Governance</h4><p>Single engine evaluates actions across Slack, GitHub, X, Notion, Gmail, Outlook, and AWS. Same classification pattern, same enforcement boundary, every system.</p></div>
      <div class="runtime-card"><h4>Customer Isolation</h4><p>Tenant-scoped data, actions, and pending queues. Each customer sees only their own workspace. Operator admin view spans all customers.</p></div>
      <div class="runtime-card"><h4>Tamper-Evident Audit Logs</h4><p>Every decision produces a hash-chained execution receipt. Event hash linked to previous hash. Full audit trail with integrity verification.</p></div>
      <div class="runtime-card"><h4>Approval Workflow</h4><p>Held actions surface in a pending queue with full context. Operators approve or reject with confirmation. Receipts generated on resolution. Slack DM notifications on hold.</p></div>
      <div class="runtime-card"><h4>Context-Aware Classification</h4><p>Actions are classified by content, destination, and context — not just type. A Slack message to #eng-platform differs from one to #company-announcements. A PR to dev differs from one to main.</p></div>
      <div class="runtime-card"><h4>Real-Time Dashboard</h4><p>Live-polling operator dashboard with pending queue, activity feed, execution receipts, policy view, and integration status. Client-facing and admin views.</p></div>
      <div class="runtime-card"><h4>Connector Architecture</h4><p>Standardized ingest → classify → evaluate → route pattern. Each system connector handles normalization. New systems follow the same integration pattern.</p></div>
    </div>

    <div style="margin-top:48px;">
      <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:20px;">Current status and roadmap</div>'''

new_caps = '''    <div class="section-title brand-heading" style="">What Surfit does today.</div>
    <p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;max-width:720px;">Current capabilities and roadmap.</p>

    <div style="margin-top:26px;">'''

if old_caps in content:
    content = content.replace(old_caps, new_caps)
    changes += 1
    print("✅ 4. Removed 9 capability cards, kept Live/In Progress")
else:
    print("⚠️  4. Capability cards — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 5. BRIGHTEN Pre-built Agent Logic and Internal Builds labels
# ═══════════════════════════════════════════════════════════

old = '<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Pre-built Agent Logic</div>'
new = '<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;font-weight:600;">Pre-built Agent Logic</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 5a. Pre-built Agent Logic label brightened")

old = '<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Internal Builds</div>'
new = '<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;font-weight:600;">Internal Builds</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 5b. Internal Builds label brightened")


# ═══════════════════════════════════════════════════════════
# 6. BEEF UP "Why This Requires a Dedicated Layer"
#    Not about human approval — about architectural necessity
# ═══════════════════════════════════════════════════════════

old_why = '''<h4 style="color:var(--blue);font-size:14px;margin-bottom:16px;">Why This Requires a Dedicated Layer</h4>
        <div style="color:var(--text);font-size:13px;line-height:2.2;">
          • Agent actions require real-time decisioning across every system they touch<br>
          • Each system has different APIs, actions, and risk profiles — this cannot be unified ad hoc<br>
          • Decisions must happen at runtime, not inside static or prebuilt agent logic<br>
          • Approval routing, logging, and enforcement must be consistent across all systems<br>
          • Control must exist outside the agent to remain neutral and enforceable
        </div>'''

new_why = '''<h4 style="color:var(--blue);font-size:16px;margin-bottom:16px;">Why This Requires a Dedicated Layer</h4>
        <div style="color:var(--text);font-size:14px;line-height:2.2;">
          • <strong style="color:var(--blue);">Credential separation is architectural, not optional.</strong> If the agent holds the credentials, governance is advisory. If an external layer holds them, governance is enforceable.<br>
          • <strong style="color:var(--blue);">Business context cannot live inside the agent.</strong> The agent knows what it wants to do. It does not know whether this is the right action for the organization right now.<br>
          • <strong style="color:var(--blue);">Cross-system consistency requires a neutral layer.</strong> Slack, GitHub, AWS, Gmail — each has different APIs, risk profiles, and decision owners. Only an external layer can enforce one decision model across all of them.<br>
          • <strong style="color:var(--blue);">Self-regulation is not enforcement.</strong> When governance lives inside the agent framework, it is controlled by the same system it is supposed to constrain. Independent control requires architectural separation.<br>
          • <strong style="color:var(--blue);">Every action needs a verifiable record.</strong> Not just logging — a hash-chained audit trail that proves every action was evaluated against policy before execution, independent of the agent's own reporting.
        </div>'''

if old_why in content:
    content = content.replace(old_why, new_why)
    changes += 1
    print("✅ 6. Why Dedicated Layer — beefed up with architectural arguments")
else:
    print("⚠️  6. Why Dedicated Layer — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 7. ADD SPACING to In Progress bullets (line breaks between items)
# ═══════════════════════════════════════════════════════════

old_progress = '''• <strong style="color:var(--text);">Predictive Risk Scoring</strong> — ML-augmented wave classification that learns from approval patterns to auto-calibrate risk thresholds per organization<br><br>• <strong style="color:var(--text);">Cross-System Policy Chaining</strong> — Actions in one system trigger policy evaluation in dependent systems (e.g., GitHub merge → Slack announcement → Notion update, all governed as one chain)<br><br>• <strong style="color:var(--text);">Real-Time Policy Simulation</strong> — Test policy changes against historical action data before deploying, with impact analysis showing which past actions would have been reclassified<br><br>• <strong style="color:var(--text);">Autonomous Escalation Routing</strong> — Dynamic approver selection based on action context, organizational hierarchy, and availability — not static hardcoded approvers<br><br>• <strong style="color:var(--text);">Execution Replay &amp; Forensics</strong> — Full action replay with counterfactual analysis: "What would have happened under different policies?"<br><br>• <strong style="color:var(--text);">SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria'''

new_progress = '''<div style="margin-bottom:14px;">• <strong style="color:var(--text);">Predictive Risk Scoring</strong><br><span style="color:var(--muted);">ML-augmented wave classification that learns from approval patterns to auto-calibrate risk thresholds per organization</span></div><div style="margin-bottom:14px;">• <strong style="color:var(--text);">Cross-System Policy Chaining</strong><br><span style="color:var(--muted);">Actions in one system trigger policy evaluation in dependent systems (e.g., GitHub merge → Slack announcement → Notion update)</span></div><div style="margin-bottom:14px;">• <strong style="color:var(--text);">Real-Time Policy Simulation</strong><br><span style="color:var(--muted);">Test policy changes against historical action data before deploying, with impact analysis</span></div><div style="margin-bottom:14px;">• <strong style="color:var(--text);">Autonomous Escalation Routing</strong><br><span style="color:var(--muted);">Dynamic approver selection based on action context, organizational hierarchy, and availability</span></div><div style="margin-bottom:14px;">• <strong style="color:var(--text);">Execution Replay &amp; Forensics</strong><br><span style="color:var(--muted);">Full action replay with counterfactual analysis: "What would have happened under different policies?"</span></div><div style="margin-bottom:0;">• <strong style="color:var(--text);">SOC 2 Type II Compliance</strong><br><span style="color:var(--muted);">Audit-ready governance artifacts, access controls, and tamper-evident logging</span></div>'''

if old_progress in content:
    content = content.replace(old_progress, new_progress)
    changes += 1
    print("✅ 7. In Progress bullets — spaced and styled")
else:
    print("⚠️  7. In Progress bullets — not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'round 5: catastrophe icon, remove architecture, beef up dedicated layer, clean platform section' && git push")
