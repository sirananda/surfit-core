#!/usr/bin/env python3
"""Reframe wave system + add summary line to diagram"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".v28d")

with open(FILE, "r") as f:
    html = f.read()

# 1. Update systems column — new wave numbers + action labels
old_sys = """        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
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
        </div>"""

new_sys = """        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Slack</span><span style="font-size:10px;color:#22c55e;font-weight:600;width:36px;text-align:center;">1</span><span style="font-size:10px;color:#22c55e;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Notion</span><span style="font-size:10px;color:#38bdf8;font-weight:600;width:36px;text-align:center;">2</span><span style="font-size:10px;color:#38bdf8;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">X</span><span style="font-size:10px;color:#eab308;font-weight:600;width:36px;text-align:center;">3</span><span style="font-size:10px;color:#eab308;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">GitHub</span><span style="font-size:10px;color:#f97316;font-weight:600;width:36px;text-align:center;">4</span><span style="font-size:10px;color:#f97316;width:80px;text-align:right;">Approval</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;width:36px;text-align:center;">5</span><span style="font-size:10px;color:#ef4444;width:80px;text-align:right;">Approval</span>
        </div>"""

html = html.replace(old_sys, new_sys)

# 2. Add summary line below the diagram
html = html.replace(
    """    </div>
  </div>
</section>


<!-- COMPARISON TABLE -->""",
    """    </div>
    <p style="text-align:center;margin-top:32px;font-size:14px;color:var(--text);max-width:700px;margin-left:auto;margin-right:auto;line-height:1.7;">Frameworks decide <span style="color:var(--orange);font-weight:500;">what</span> to do. Sandboxes control <span style="color:#a78bfa;font-weight:500;">where</span> agents run. Surfit controls <span style="color:var(--blue);font-weight:500;">whether the action is correct.</span></p>
  </div>
</section>


<!-- COMPARISON TABLE -->"""
)

# 3. Update the flow section wave descriptions to match new framing
html = html.replace(
    'Low → runs automatically. Medium → runs with logging. High → requires checks. Critical → escalated. Execution is controlled dynamically — not blocked by default.',
    'Wave 1–3: execute automatically with logging. Wave 4–5: require approval. Most actions never need a human. Execution is controlled dynamically — not blocked by default.'
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Reframe waves + summary line' && git push")
