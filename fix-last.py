#!/usr/bin/env python3
"""LAST fix - SOC 2 + diagram centering + systems headers"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".lastbackup")

with open(FILE, "r") as f:
    html = f.read()

# 1. SOC 2 — the & got escaped. Find the actual text
if 'SOC 2' not in html:
    # Add SOC 2 before closing </p> of In Progress section
    html = html.replace(
        """Execution Replay & Forensics</strong>""",
        """Execution Replay &amp; Forensics</strong>"""
    )
    html = html.replace(
        '''counterfactual analysis: "What would have happened under different policies?"</p>''',
        '''counterfactual analysis: "What would have happened under different policies?"<br><br>• <strong style="color:var(--text);">SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria</p>'''
    )

# 2. Fix diagram — properly centered, systems with two-column header
old_diagram = """    <div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;max-width:1060px;margin:0 auto;">
      <div style="display:flex;flex-direction:column;gap:0;align-items:center;max-width:240px;">
        <div style="background:var(--surface);border:1px solid rgba(255,115,30,0.3);border-radius:10px;padding:22px 24px;text-align:center;min-width:220px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:6px;">Agent Framework + Sandbox</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);margin-bottom:2px;">OpenClaw</div>
          <div style="font-size:12px;color:var(--muted);">powered by NemoClaw</div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);line-height:1.5;">Sandboxed agent execution with network egress control</div>
        </div>
        <div style="margin-top:10px;font-size:12px;text-align:center;line-height:1.6;max-width:220px;"><span style="color:var(--text);">Agents reason and act. Sandboxes control network egress.</span> <span style="color:var(--orange);font-weight:600;">Neither governs business correctness.</span></div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 18px;">→</div>
      <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:12px;padding:28px 40px;text-align:center;min-width:240px;align-self:flex-start;">
        <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;">Control Layer</div>
        <div style="font-family:'Righteous',cursive;font-size:26px;color:var(--text);margin-bottom:12px;"><span style="color:var(--blue);">Surfit</span><span style="color:var(--muted);font-size:16px;">.</span><span style="color:var(--orange);">AI</span></div>
        <div style="display:flex;flex-direction:column;gap:6px;align-items:center;">
          <div style="font-size:12px;color:var(--text);font-weight:500;">Wave evaluation</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Policy enforcement</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Execution control</div>
        </div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 18px;">→</div>
      <div style="display:flex;flex-direction:column;gap:6px;align-items:center;">
        <div style="font-size:9px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Systems</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;min-width:120px;display:flex;align-items:center;justify-content:space-between;gap:12px;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Slack</span><span style="font-size:10px;color:#38bdf8;font-weight:600;">W2</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;min-width:120px;display:flex;align-items:center;justify-content:space-between;gap:12px;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">GitHub</span><span style="font-size:10px;color:#ef4444;font-weight:600;">W5</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;min-width:120px;display:flex;align-items:center;justify-content:space-between;gap:12px;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">X</span><span style="font-size:10px;color:#eab308;font-weight:600;">W3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;min-width:120px;display:flex;align-items:center;justify-content:space-between;gap:12px;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Notion</span><span style="font-size:10px;color:#eab308;font-weight:600;">W3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;min-width:120px;display:flex;align-items:center;justify-content:space-between;gap:12px;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;">W5</span>
        </div>
        <div style="font-size:9px;color:var(--muted);margin-top:2px;letter-spacing:0.05em;">AVG WAVE RISK</div>
      </div>
    </div>"""

new_diagram = """    <div style="display:flex;align-items:center;justify-content:center;gap:0;max-width:960px;margin:0 auto;">
      <div style="display:flex;flex-direction:column;gap:0;align-items:center;width:220px;flex-shrink:0;">
        <div style="background:var(--surface);border:1px solid rgba(255,115,30,0.3);border-radius:10px;padding:22px 20px;text-align:center;width:100%;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:6px;">Agent Framework + Sandbox</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);margin-bottom:2px;">OpenClaw</div>
          <div style="font-size:12px;color:var(--muted);">powered by NemoClaw</div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);line-height:1.5;">Sandboxed agent execution with network egress control</div>
        </div>
        <div style="margin-top:10px;font-size:12px;text-align:center;line-height:1.6;"><span style="color:var(--text);">Agents reason and act. Sandboxes control network egress.</span> <span style="color:var(--orange);font-weight:600;">Neither governs business correctness.</span></div>
      </div>
      <div style="color:var(--border);font-size:22px;padding:0 16px;flex-shrink:0;">→</div>
      <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:12px;padding:28px 36px;text-align:center;width:240px;flex-shrink:0;">
        <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;">Control Layer</div>
        <div style="font-family:'Righteous',cursive;font-size:26px;color:var(--text);margin-bottom:12px;"><span style="color:var(--blue);">Surfit</span><span style="color:var(--muted);font-size:16px;">.</span><span style="color:var(--orange);">AI</span></div>
        <div style="display:flex;flex-direction:column;gap:6px;align-items:center;">
          <div style="font-size:12px;color:var(--text);font-weight:500;">Wave evaluation</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Policy enforcement</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Execution control</div>
        </div>
      </div>
      <div style="color:var(--border);font-size:22px;padding:0 16px;flex-shrink:0;">→</div>
      <div style="display:flex;flex-direction:column;gap:6px;align-items:stretch;width:160px;flex-shrink:0;">
        <div style="display:flex;justify-content:space-between;margin-bottom:2px;padding:0 4px;">
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);">System</span>
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);">Wave</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Slack</span><span style="font-size:10px;color:#38bdf8;font-weight:600;">2</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">GitHub</span><span style="font-size:10px;color:#ef4444;font-weight:600;">5</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">X</span><span style="font-size:10px;color:#eab308;font-weight:600;">3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Notion</span><span style="font-size:10px;color:#eab308;font-weight:600;">3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;">5</span>
        </div>
      </div>
    </div>"""

html = html.replace(old_diagram, new_diagram)

# 3. SOC 2 — check if it was added, if not force it
if 'SOC 2' not in html:
    # Find the In Progress section and add before closing </p>
    html = html.replace(
        'under different policies?"</p>',
        'under different policies?"<br><br>• <strong style="color:var(--text);">SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria</p>'
    )

with open(FILE, "w") as f:
    f.write(html)

# Verify SOC 2 was added
with open(FILE, "r") as f:
    content = f.read()
    if 'SOC 2' in content:
        print("✅ SOC 2 confirmed in file")
    else:
        print("⚠️  SOC 2 NOT found — manual check needed")

print("✅ ALL fixes applied")
print("Deploy: git add index.html && git commit -m 'Final' && git push")
