#!/usr/bin/env python3
"""Fix remaining issues on surfit.ai"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".fix3backup")

with open(FILE, "r") as f:
    html = f.read()

# 1. Remove the "Works with OpenClaw..." line below the systems list
html = html.replace(
    '<p class="hero-saw-def">Works with OpenClaw and proprietary internal agents.</p>',
    ''
)

# 2. Add more spacing before "Surfit is the control layer" line
html = html.replace(
    '<p class="hero-saw-def" style="margin-top:16px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>',
    '<p class="hero-saw-def" style="margin-top:28px;margin-bottom:24px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>'
)

# 3. Fix NemoClaw — it's a sandbox plugin, not an orchestrator
# Also add descriptions under the left column
old_left_column = """      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Framework</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">OpenClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Orchestrator</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">NemoClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Internal</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">Custom Agents</div>
        </div>
      </div>"""

new_left_column = """      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;max-width:220px;">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:200px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Agent Framework</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">OpenClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:200px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Sandbox Runtime</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">NemoClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:200px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Proprietary</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">Custom Agents</div>
        </div>
        <div style="margin-top:6px;font-size:11px;color:var(--muted);text-align:center;line-height:1.5;max-width:200px;">Agents reason and act. Sandboxes control network egress. Neither governs business correctness.</div>
      </div>"""

html = html.replace(old_left_column, new_left_column)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Fixes applied")
print("Deploy: git add index.html && git commit -m 'Fix hero + diagram' && git push")
