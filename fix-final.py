#!/usr/bin/env python3
"""FINAL website fixes - everything in one pass"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".finalbackup")

with open(FILE, "r") as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════
# 1. Center the "Surfit is the control layer" text with more breathing room
# ═══════════════════════════════════════════════════════════
html = html.replace(
    '<p class="hero-saw-def" style="margin-top:28px;margin-bottom:24px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>',
    '<p class="hero-saw-def" style="margin-top:32px;margin-bottom:32px;font-size:13px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>'
)

# ═══════════════════════════════════════════════════════════
# 2. Fix the agent diagram — bigger Surfit box, vertical features, 
#    left column centered against Surfit, system labels with wave ratings
# ═══════════════════════════════════════════════════════════
old_diagram_inner = """    <div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;max-width:1000px;margin:0 auto;">
      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;max-width:240px;">
        <div style="background:var(--surface);border:1px solid rgba(255,115,30,0.3);border-radius:10px;padding:20px 24px;text-align:center;min-width:220px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:6px;">Agent Framework + Sandbox</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);margin-bottom:2px;">OpenClaw</div>
          <div style="font-size:12px;color:var(--muted);">powered by NemoClaw</div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);line-height:1.5;">Sandboxed agent execution with network egress control</div>
        </div>
        <div style="margin-top:8px;font-size:12px;text-align:center;line-height:1.6;max-width:220px;"><span style="color:var(--text);">Agents reason and act. Sandboxes control network egress.</span> <span style="color:var(--orange);font-weight:500;">Neither governs business correctness.</span></div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 20px;">→</div>
      <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:12px;padding:24px 32px;text-align:center;min-width:180px;">
        <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:6px;">Control Layer</div>
        <div style="font-family:'Righteous',cursive;font-size:22px;color:var(--text);margin-bottom:6px;"><span style="color:var(--blue);">Surfit</span><span style="color:var(--muted);font-size:14px;">.</span><span style="color:var(--orange);">AI</span></div>
        <div style="font-size:11px;color:var(--muted);">Wave evaluation · Policy enforcement · Execution control</div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 20px;">→</div>
      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">Slack</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">GitHub</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">X</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">Notion</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">AWS</div>
        </div>
      </div>
    </div>"""

new_diagram_inner = """    <div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;max-width:1060px;margin:0 auto;">
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

html = html.replace(old_diagram_inner, new_diagram_inner)

# ═══════════════════════════════════════════════════════════
# 3. Fix Live Capabilities — add Notion, remove Hetzner, remove 
#    system-specific items, add deep innovations, move cloud deploy up
# ═══════════════════════════════════════════════════════════
old_live = """        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:14px;">✓ Live</div>
        <p style="color:var(--text);">• Wave runtime enforcement across Slack, GitHub, X<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with proof<br>• Approval DM notifications to operators via Slack<br>• Keyword + context-based content risk scoring<br>• GitHub webhook integration (pull_request events)<br>• X/Twitter post classification and gating<br>• Agent demo: 7 actions across 4 systems, all correct<br>• Always-on cloud deployment (Hetzner, systemd managed)<br>• Adapter SDK for external agent frameworks</p>"""

new_live = """        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:14px;">✓ Live</div>
        <p style="color:var(--text);">• Wave runtime enforcement across Slack, GitHub, X, Notion<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• Always-on cloud deployment (systemd managed)<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with cryptographic proof<br>• Context-aware content risk scoring (keyword, length, destination)<br>• Deterministic action normalization across heterogeneous system APIs<br>• Unified pending queue with cross-system operator control<br>• Product demo and architecture visualization live on website<br>• Adapter SDK for external agent frameworks</p>"""

html = html.replace(old_live, new_live)

# ═══════════════════════════════════════════════════════════
# 4. Add SOC 2 compliance to In Progress
# ═══════════════════════════════════════════════════════════
html = html.replace(
    """• <strong style="color:var(--text);">Execution Replay &amp; Forensics</strong> — Full action replay with counterfactual analysis: "What would have happened under different policies?"</p>""",
    """• <strong style="color:var(--text);">Execution Replay &amp; Forensics</strong> — Full action replay with counterfactual analysis: "What would have happened under different policies?"<br><br>• <strong style="color:var(--text);">SOC 2 Type II Compliance</strong> — Audit-ready governance artifacts, access controls, and tamper-evident logging aligned with SOC 2 trust service criteria</p>"""
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ FINAL fixes applied")
print("Deploy: git add index.html && git commit -m 'Final website update' && git push")
