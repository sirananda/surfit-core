#!/usr/bin/env python3
"""Expand failure examples, add Action column, restructure landscape to 4 columns"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".v28c")

with open(FILE, "r") as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════
# 1. EXPAND "Where agents fail" — more examples
# ═══════════════════════════════════════════════════════════

old_failures = """    <div style="display:flex;flex-direction:column;gap:12px;margin:24px auto 28px;max-width:600px;text-align:left;">
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent posts confidential data to a public Slack channel</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent merges valid code that breaks your business</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:14px;color:var(--text);">An agent triggers the wrong workflow across systems</div>
    </div>"""

new_failures = """    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:24px auto 28px;max-width:700px;text-align:left;">
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent posts confidential data to a public Slack channel</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent merges valid code that breaks production</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent triggers the wrong workflow across systems</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent publishes an unapproved statement to your public timeline</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent updates a database with logically incorrect values</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent sends the right message to the wrong audience</div>
    </div>"""

html = html.replace(old_failures, new_failures)

# ═══════════════════════════════════════════════════════════
# 2. ADD ACTION COLUMN to agent integration diagram
# ═══════════════════════════════════════════════════════════

# Replace the systems column with systems + wave + action
old_systems_col = """      <div style="display:flex;flex-direction:column;gap:6px;width:160px;flex-shrink:0;">
        <div style="display:flex;justify-content:space-between;padding:0 14px;margin-bottom:2px;">
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;">Systems</span>
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;">Wave Risk</span>
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
      </div>"""

new_systems_col = """      <div style="display:flex;flex-direction:column;gap:6px;width:260px;flex-shrink:0;">
        <div style="display:flex;padding:0 14px;margin-bottom:2px;">
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;flex:1;">Systems</span>
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;width:36px;text-align:center;">Wave</span>
          <span style="font-size:9px;letter-spacing:0.12em;text-transform:uppercase;color:var(--text);font-weight:600;width:80px;text-align:right;">Action</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Slack</span><span style="font-size:10px;color:#38bdf8;font-weight:600;width:36px;text-align:center;">2</span><span style="font-size:10px;color:#22c55e;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">GitHub</span><span style="font-size:10px;color:#ef4444;font-weight:600;width:36px;text-align:center;">5</span><span style="font-size:10px;color:#ef4444;width:80px;text-align:right;">Approval</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">X</span><span style="font-size:10px;color:#eab308;font-weight:600;width:36px;text-align:center;">3</span><span style="font-size:10px;color:#eab308;width:80px;text-align:right;">Check</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Notion</span><span style="font-size:10px;color:#eab308;font-weight:600;width:36px;text-align:center;">3</span><span style="font-size:10px;color:#eab308;width:80px;text-align:right;">Check</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;width:36px;text-align:center;">5</span><span style="font-size:10px;color:#ef4444;width:80px;text-align:right;">Approval</span>
        </div>
      </div>"""

html = html.replace(old_systems_col, new_systems_col)

# ═══════════════════════════════════════════════════════════
# 3. RESTRUCTURE "Where Surfit fits" to 4 columns
# ═══════════════════════════════════════════════════════════

old_landscape = """    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
      <!-- Automation Tools -->
      <div style="background:var(--surface);padding:32px 28px;display:flex;flex-direction:column;gap:20px;">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Automation Tools</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);">Zapier, Make, n8n</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">Trigger → Transform → Action → Done</div>
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">Predefined logic. No uncertainty.</div>
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">No governance layer. No audit.</div>
        </div>
      </div>
      <!-- Agent Frameworks -->
      <div style="background:var(--surface);padding:32px 28px;display:flex;flex-direction:column;gap:20px;">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;">Agent Frameworks</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);">LangChain, AutoGen</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">Goal → LLM reasoning → Tool calls → More reasoning</div>
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">Dynamic reasoning. Open-ended behavior.</div>
          <div style="font-size:12px;font-weight:300;color:var(--muted);padding:10px 14px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">No write controls. No audit lineage.</div>
        </div>
      </div>
      <!-- Surfit Runtime -->
      <div style="background:#0d1a2e;padding:32px 28px;display:flex;flex-direction:column;gap:20px;border-left:1px solid rgba(38,192,255,0.2);">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;">Surfit Runtime</div>
          <div style="font-size:16px;font-weight:500;color:var(--text);">Controlled Execution</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div style="font-size:12px;font-weight:300;color:var(--text);padding:10px 14px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Agent → Action request → Wave evaluation → Decision → Execute or gate</div>
          <div style="font-size:12px;font-weight:300;color:var(--text);padding:10px 14px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Actions handled based on risk. Automatic, checked, or gated.</div>
          <div style="font-size:12px;font-weight:300;color:var(--text);padding:10px 14px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Every action receipted. Verifiable audit by default.</div>
        </div>
        <div style="font-size:11px;letter-spacing:0.08em;color:var(--blue);font-weight:500;margin-top:4px;">Surfit doesn't replace automation or agent frameworks. It decides how their actions are handled.</div>
      </div>
    </div>"""

new_landscape = """    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
      <!-- Automation Tools -->
      <div style="background:var(--surface);padding:28px 22px;display:flex;flex-direction:column;gap:16px;">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Automation Tools</div>
          <div style="font-size:15px;font-weight:500;color:var(--text);">Zapier, Make, n8n</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">Trigger → Transform → Action</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">Predefined logic. No uncertainty.</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(122,154,184,0.06);border-radius:6px;border-left:2px solid var(--muted);">No governance. No audit.</div>
        </div>
      </div>
      <!-- Agent Frameworks -->
      <div style="background:var(--surface);padding:28px 22px;display:flex;flex-direction:column;gap:16px;">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;">Agent Frameworks</div>
          <div style="font-size:15px;font-weight:500;color:var(--text);">OpenClaw, LangChain, AutoGen</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">Goal → LLM reasoning → Tool calls</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">Dynamic reasoning. Open-ended behavior.</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(255,115,30,0.06);border-radius:6px;border-left:2px solid var(--orange);">No business-level write controls.</div>
        </div>
      </div>
      <!-- Sandbox Runtimes -->
      <div style="background:var(--surface);padding:28px 22px;display:flex;flex-direction:column;gap:16px;">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:#a78bfa;margin-bottom:8px;">Sandbox Runtimes</div>
          <div style="font-size:15px;font-weight:500;color:var(--text);">NemoClaw, OpenShell</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(167,139,250,0.06);border-radius:6px;border-left:2px solid #a78bfa;">Isolated execution environment.</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(167,139,250,0.06);border-radius:6px;border-left:2px solid #a78bfa;">Network egress control. Operator approval for access.</div>
          <div style="font-size:11px;font-weight:300;color:var(--muted);padding:8px 12px;background:rgba(167,139,250,0.06);border-radius:6px;border-left:2px solid #a78bfa;">Controls what agents access — not whether actions are correct.</div>
        </div>
      </div>
      <!-- Surfit -->
      <div style="background:#0d1a2e;padding:28px 22px;display:flex;flex-direction:column;gap:16px;border-left:1px solid rgba(38,192,255,0.2);">
        <div>
          <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;">Surfit</div>
          <div style="font-size:15px;font-weight:500;color:var(--text);">Business Correctness</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="font-size:11px;font-weight:300;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Action → Risk classification → Decision → Execute or gate</div>
          <div style="font-size:11px;font-weight:300;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Policy-driven. Risk-aware. Business-aligned.</div>
          <div style="font-size:11px;font-weight:300;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Every action receipted. Verifiable audit by default.</div>
        </div>
        <div style="font-size:10px;letter-spacing:0.06em;color:var(--blue);font-weight:500;margin-top:4px;">Surfit doesn't replace frameworks or sandboxes. It ensures the actions they produce are correct.</div>
      </div>
    </div>"""

html = html.replace(old_landscape, new_landscape)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Expand failures + action column + 4-col landscape' && git push")
