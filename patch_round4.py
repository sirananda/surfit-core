"""
Round 4: Multiple fixes.
1. Change "babysitters" punchline - identify who's who
2. Orange outlines on Without Surfit boxes
3. Brighter category labels in gap diagram
4. Blue outline on Agent box in With Surfit
5. Numbered landscape cards
6. Remove "Execution Boundary Model" section
7. Merge Platform Capabilities + Platform Progress into one section

Run from ~/Desktop/files/: python3 patch_round4.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. PUNCHLINE — replace babysitters/guards with named refs
# ═══════════════════════════════════════════════════════════

old = 'The babysitters checked the words. The guards checked the door. The agent had the keys the entire time.'
new = 'Guardrails AI and CTGT checked the words. IronClaw and NemoClaw checked the door. The agent had the keys the entire time.'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1. Punchline — named competitors instead of babysitters/guards")
else:
    print("⚠️  1. Punchline — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 2. ORANGE OUTLINES on Without Surfit boxes
# ═══════════════════════════════════════════════════════════

# Output Validation box
old = '<div style="font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;">Output Validation</div>'
new = '<div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Output Validation</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2a. Output Validation label brightened to orange")

# Sandbox & Access box
old = '<div style="font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;">Sandbox &amp; Access</div>'
new = '<div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Sandbox &amp; Access</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2b. Sandbox & Access label brightened to orange")

# Orange borders on the Without Surfit boxes
old = '<div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Output Validation</div>'
new = '<div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(249,115,22,0.3);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Output Validation</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2c. Output Validation box orange border")

old = '<div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Sandbox &amp; Access</div>'
new = '<div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(249,115,22,0.3);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:9px;color:var(--orange);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;font-weight:600;">Sandbox &amp; Access</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2d. Sandbox box orange border")


# ═══════════════════════════════════════════════════════════
# 3. BLUE OUTLINE on Agent box in With Surfit flow
# ═══════════════════════════════════════════════════════════

old = '<div style="flex:0.7;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:14px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:18px;margin-bottom:4px;">🤖</div>\n          <div style="font-size:11px;font-weight:600;color:var(--text);">Agent</div>\n          <div style="font-size:10px;color:var(--muted);margin-top:2px;">Proposes action</div>\n          <div style="font-size:9px;color:var(--blue);margin-top:2px;font-style:italic;">No credentials</div>'
new = '<div style="flex:0.7;background:rgba(38,192,255,0.03);border:1px solid rgba(38,192,255,0.3);border-radius:8px;padding:14px;text-align:center;display:flex;flex-direction:column;justify-content:center;">\n          <div style="font-size:18px;margin-bottom:4px;">🤖</div>\n          <div style="font-size:11px;font-weight:600;color:var(--text);">Agent</div>\n          <div style="font-size:10px;color:var(--muted);margin-top:2px;">Proposes action</div>\n          <div style="font-size:9px;color:var(--blue);margin-top:2px;font-style:italic;">No credentials</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3. Agent box in With Surfit — blue outline")
else:
    print("⚠️  3. Agent box blue outline — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 4. NUMBERED LANDSCAPE CARDS
# ═══════════════════════════════════════════════════════════

# Card 1: Output Validation
old = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Output Validation</div>'
new = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">01</span>Output Validation</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4a. Landscape card 01 numbered")

# Card 2: Model Behavior Control
old = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Model Behavior Control</div>'
new = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">02</span>Model Behavior Control</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4b. Landscape card 02 numbered")

# Card 3: Sandbox & Environment Security
old = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Sandbox &amp; Environment Security</div>'
new = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">03</span>Sandbox &amp; Environment Security</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4c. Landscape card 03 numbered")

# Card 4: Infrastructure & Endpoint Security
old = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Infrastructure &amp; Endpoint Security</div>'
new = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">04</span>Infrastructure &amp; Endpoint Security</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4d. Landscape card 04 numbered")

# Card 5: Agent Runtimes
old = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Agent Runtimes</div>'
new = '<div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">05</span>Agent Runtimes</div>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4e. Landscape card 05 numbered")


# ═══════════════════════════════════════════════════════════
# 5. REMOVE "Execution Boundary Model" section
# ═══════════════════════════════════════════════════════════

ebm_start = '<!-- FLOW DIAGRAM -->'
ebm_end = '<!-- ARCHITECTURE -->'

if ebm_start in content and ebm_end in content:
    s = content.index(ebm_start)
    e = content.index(ebm_end)
    content = content[:s] + '\n' + content[e:]
    changes += 1
    print("✅ 5. Removed Execution Boundary Model section")
else:
    print("⚠️  5. Execution Boundary Model — markers not found, skipping")


# ═══════════════════════════════════════════════════════════
# 6. MERGE Platform Progress INTO Platform Capabilities
#    Remove Platform Progress as separate section,
#    append Live/In Progress cards into Capabilities section
# ═══════════════════════════════════════════════════════════

# Remove the Platform Progress section header and make it part of Capabilities
# Find Platform Capabilities closing </section> and Platform Progress opening
old_cap_end = '''    </div>
  </div>
</section>

<!-- PLATFORM PROGRESS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div class="section-label">Platform Progress</div>
    <div class="section-title brand-heading" style="">Current capabilities and roadmap focus.</div>'''

new_cap_end = '''    </div>

    <div style="margin-top:48px;">
      <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:20px;">Current status and roadmap</div>'''

if old_cap_end in content:
    content = content.replace(old_cap_end, new_cap_end)
    changes += 1
    print("✅ 6. Merged Platform Progress into Platform Capabilities")
else:
    print("⚠️  6. Platform sections merge — not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'round 4: named competitors, orange outlines, numbered landscape, merged platform sections' && git push")
