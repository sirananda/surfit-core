"""
Round 3: Visual polish and content tightening.
All exact string replacements. No structural changes.

Run from ~/Desktop/files/: python3 patch_round3.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. GAP DIAGRAM — brighten text in top row boxes
# ═══════════════════════════════════════════════════════════

# Output Validation box - description text
old = '<div style="font-size:9px;color:var(--muted);margin-top:2px;font-style:italic;">Checks words, not actions</div>'
new = '<div style="font-size:9px;color:var(--text);margin-top:2px;font-style:italic;opacity:0.7;">Checks words, not actions</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1a. Gap box 'Checks words' brightened")

# Sandbox box - description text
old = '<div style="font-size:9px;color:var(--muted);margin-top:2px;font-style:italic;">Checks the door, not the decision</div>'
new = '<div style="font-size:9px;color:var(--text);margin-top:2px;font-style:italic;opacity:0.7;">Checks the door, not the decision</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1b. Gap box 'Checks the door' brightened")

# Output Validation names
old = '<div style="font-size:10px;color:var(--muted);">Guardrails AI · CTGT</div>'
new = '<div style="font-size:10px;color:var(--text);opacity:0.8;">Guardrails AI · CTGT</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1c. Gap box names brightened")

# Sandbox names
old = '<div style="font-size:10px;color:var(--muted);">IronClaw · NemoClaw</div>'
new = '<div style="font-size:10px;color:var(--text);opacity:0.8;">IronClaw · NemoClaw</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1d. Gap sandbox names brightened")


# ═══════════════════════════════════════════════════════════
# 2. AGENT INTEGRATION — brighten arrows
# ═══════════════════════════════════════════════════════════

# The arrows are likely styled with opacity or muted color
# Find the arrow elements between the boxes
old = '<div class="integration-arrow">→</div>'
new = '<div class="integration-arrow" style="color:var(--blue);opacity:0.8;font-size:24px;">→</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. Agent Integration arrows brightened")
else:
    # Try alternative arrow format
    old = 'class="integration-arrow"'
    if old in content:
        content = content.replace(old, 'class="integration-arrow" style="color:var(--blue);opacity:0.9;"')
        changes += 1
        print("✅ 2. Agent Integration arrows brightened (alt)")
    else:
        print("⚠️  2. Agent Integration arrows — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 3. INTERNAL BUILDS — beef up the content
# ═══════════════════════════════════════════════════════════

old_internal = '''<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Internal Builds</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Requires rebuilding decision infrastructure for every new integration<br>
            • Quickly becomes brittle, inconsistent, and expensive to maintain<br>
            • No unified enforcement — decisions vary across systems and teams
          </div>'''

new_internal = '''<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Internal Builds</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Every new system requires new decision logic — Slack rules don't apply to GitHub, GitHub rules don't apply to AWS<br>
            • The team that builds the agent is the team that builds the governance — that's self-regulation, not enforcement<br>
            • Credentials stay inside the agent — governance is advisory, not architectural<br>
            • Breaks the moment you add a second agent, a new framework, or a third-party system<br>
            • No cross-system consistency — every integration is a one-off
          </div>'''

if old_internal in content:
    content = content.replace(old_internal, new_internal)
    changes += 1
    print("✅ 3. Internal Builds section beefed up")
else:
    print("⚠️  3. Internal Builds — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# 4. PRE-BUILT AGENT LOGIC — beef up too
# ═══════════════════════════════════════════════════════════

old_prebuilt = '''<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Pre-built Agent Logic</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Breaks under real-world variability — cannot reliably assess risk across systems<br>
            • Logic becomes fragmented across agents with no consistent control layer
          </div>'''

new_prebuilt = '''<div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Pre-built Agent Logic</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Hardcoded rules break when context changes — a safe action in staging is dangerous in production<br>
            • Cannot evaluate business context — doesn't know if it's Monday morning or earnings week<br>
            • Logic is embedded inside the agent — a model update or prompt change can silently alter what's "allowed"
          </div>'''

if old_prebuilt in content:
    content = content.replace(old_prebuilt, new_prebuilt)
    changes += 1
    print("✅ 4. Pre-built Agent Logic section beefed up")
else:
    print("⚠️  4. Pre-built Agent Logic — string not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'round 3: visual polish, brighter text, stronger internal builds' && git push")
