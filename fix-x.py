#!/usr/bin/env python3
"""LAST FIX"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".xbackup")

with open(FILE, "r") as f:
    html = f.read()

# 1. Fix diagram — equal height columns, centered headers, white System text, Wave Risk label
old = """    <div style="display:flex;align-items:center;justify-content:center;gap:0;max-width:960px;margin:0 auto;">
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

new = """    <div style="display:flex;align-items:stretch;justify-content:center;gap:0;max-width:960px;margin:0 auto;">
      <div style="display:flex;flex-direction:column;align-items:center;width:220px;flex-shrink:0;justify-content:center;">
        <div style="background:var(--surface);border:1px solid rgba(255,115,30,0.3);border-radius:10px;padding:22px 20px;text-align:center;width:100%;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:6px;">Agent Framework + Sandbox</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);margin-bottom:2px;">OpenClaw</div>
          <div style="font-size:12px;color:var(--muted);">powered by NemoClaw</div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);line-height:1.5;">Sandboxed agent execution with network egress control</div>
        </div>
        <div style="margin-top:10px;font-size:12px;text-align:center;line-height:1.6;"><span style="color:var(--text);">Agents reason and act. Sandboxes control network egress.</span> <span style="color:var(--orange);font-weight:600;">Neither governs business correctness.</span></div>
      </div>
      <div style="color:var(--border);font-size:22px;padding:0 16px;flex-shrink:0;display:flex;align-items:center;">→</div>
      <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:12px;padding:28px 36px;text-align:center;width:240px;flex-shrink:0;display:flex;flex-direction:column;justify-content:center;">
        <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;">Control Layer</div>
        <div style="font-family:'Righteous',cursive;font-size:26px;color:var(--text);margin-bottom:12px;"><span style="color:var(--blue);">Surfit</span><span style="color:var(--muted);font-size:16px;">.</span><span style="color:var(--orange);">AI</span></div>
        <div style="display:flex;flex-direction:column;gap:6px;align-items:center;">
          <div style="font-size:12px;color:var(--text);font-weight:500;">Wave evaluation</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Policy enforcement</div>
          <div style="font-size:12px;color:var(--text);font-weight:500;">Execution control</div>
        </div>
      </div>
      <div style="color:var(--border);font-size:22px;padding:0 16px;flex-shrink:0;display:flex;align-items:center;">→</div>
      <div style="display:flex;flex-direction:column;gap:6px;align-items:center;width:160px;flex-shrink:0;">
        <div style="text-align:center;margin-bottom:4px;">
          <div style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;">Systems</div>
          <div style="font-size:8px;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-top:1px;">Wave Risk</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Slack</span><span style="font-size:10px;color:#38bdf8;font-weight:600;">2</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">GitHub</span><span style="font-size:10px;color:#ef4444;font-weight:600;">5</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">X</span><span style="font-size:10px;color:#eab308;font-weight:600;">3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">Notion</span><span style="font-size:10px;color:#eab308;font-weight:600;">3</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;justify-content:space-between;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;">5</span>
        </div>
      </div>
    </div>"""

html = html.replace(old, new)

# 2. Fix Live Capabilities spacing — add line breaks between items for breathing room
old_live = """<p style="color:var(--text);">• Wave runtime enforcement across Slack, GitHub, X, Notion<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• Always-on cloud deployment (systemd managed)<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with cryptographic proof<br>• Context-aware content risk scoring (keyword, length, destination)<br>• Deterministic action normalization across heterogeneous system APIs<br>• Unified pending queue with cross-system operator control<br>• Product demo and architecture visualization live on website<br>• Adapter SDK for external agent frameworks</p>"""

new_live = """<p style="color:var(--text);line-height:2.2;font-size:13px;">• Wave runtime enforcement across Slack, GitHub, X, Notion<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• Always-on cloud deployment (systemd managed)<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with cryptographic proof<br>• Context-aware content risk scoring (keyword, length, destination)<br>• Deterministic action normalization across heterogeneous APIs<br>• Unified pending queue with cross-system operator control<br>• Product demo and architecture visualization live on website<br>• Adapter SDK for external agent frameworks</p>"""

html = html.replace(old_live, new_live)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Final layout' && git push")
