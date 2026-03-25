#!/usr/bin/env python3
"""Fix remaining website issues"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".fix4backup")

with open(FILE, "r") as f:
    html = f.read()

# 1. Remove the wordy systems line from hero
html = html.replace(
    '<p class="hero-substrate" style="max-width:900px;">Control and route AI actions across Slack, GitHub, X, Notion, AWS, internal APIs, and more — based on your business rules.</p>',
    ''
)

# 2. Fix diagram — merge OpenClaw + NemoClaw into one entity, remove Custom Agents
old_left = """      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;max-width:220px;">
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

new_left = """      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;max-width:240px;">
        <div style="background:var(--surface);border:1px solid rgba(255,115,30,0.3);border-radius:10px;padding:20px 24px;text-align:center;min-width:220px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:6px;">Agent Framework + Sandbox</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);margin-bottom:2px;">OpenClaw</div>
          <div style="font-size:12px;color:var(--muted);">powered by NemoClaw</div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);line-height:1.5;">Sandboxed agent execution with network egress control</div>
        </div>
        <div style="margin-top:8px;font-size:12px;text-align:center;line-height:1.6;max-width:220px;"><span style="color:var(--text);">Agents reason and act. Sandboxes control network egress.</span> <span style="color:var(--orange);font-weight:500;">Neither governs business correctness.</span></div>
      </div>"""

html = html.replace(old_left, new_left)

# 3. Add "and more" to enterprise systems in the "How Surfit Works" boxes
html = html.replace(
    'Slack, GitHub, X, Notion, AWS, internal APIs</div>',
    'Slack, GitHub, X, Notion, AWS, internal APIs, and more</div>'
)

# 4. Update Live Capabilities to be more comprehensive + white text
old_live = """        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:14px;">✓ Live</div>
        <p>• Wave runtime enforcement across Slack, GitHub, X<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live polling<br>• SQLite-backed persistence across restarts<br>• Tamper-evident execution receipts<br>• Approval DM notifications via Slack<br>• Adapter SDK for external agent frameworks</p>"""

new_live = """        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:14px;">✓ Live</div>
        <p style="color:var(--text);">• Wave runtime enforcement across Slack, GitHub, X<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with proof<br>• Approval DM notifications to operators via Slack<br>• Keyword + context-based content risk scoring<br>• GitHub webhook integration (pull_request events)<br>• X/Twitter post classification and gating<br>• Agent demo: 7 actions across 4 systems, all correct<br>• Always-on cloud deployment (Hetzner, systemd managed)<br>• Adapter SDK for external agent frameworks</p>"""

html = html.replace(old_live, new_live)

with open(FILE, "w") as f:
    f.write(html)

print("✅ All fixes applied")
print("Deploy: git add index.html && git commit -m 'Final fixes' && git push")
