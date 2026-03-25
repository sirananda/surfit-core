#!/usr/bin/env python3
import shutil
FILE = "index.html"
shutil.copy(FILE, FILE + ".v28f")
with open(FILE, "r") as f:
    html = f.read()

old = """    <div style="max-width:820px;margin:24px auto 28px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;margin-bottom:0;">
        <div style="padding:10px 18px;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--muted);font-weight:600;">What the agent did</div>
        <div style="padding:10px 18px;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:#ef4444;font-weight:600;">What actually happened</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Posted a message to #general in Slack</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Shared confidential revenue data with 500 employees</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Merged a passing PR to main on GitHub</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Broke the billing pipeline for 3 hours</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Published a post to the company X account</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Released an unapproved product announcement publicly</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Updated a Notion database entry</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Overwrote pricing data with incorrect values before a board meeting</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Provisioned a new EC2 instance on AWS</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Spun up a public-facing server with no security group in production</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--muted);">Sent a Slack DM to a team lead</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);">Sent an internal performance review to the wrong person</div>
        </div>
      </div>
    </div>"""

new = """    <div style="max-width:820px;margin:24px auto 28px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;margin-bottom:6px;padding:0 18px;">
        <div style="font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:#22c55e;font-weight:600;text-align:center;">What the agent did</div>
        <div style="font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:#ef4444;font-weight:600;text-align:center;">What actually happened</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Posted a message to #general in Slack</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Shared confidential revenue data with 500 employees</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Merged a passing PR to main on GitHub</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Broke the billing pipeline for 3 hours</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Published a post to the company X account</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Released an unapproved product announcement publicly</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Updated a Notion database entry</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Overwrote pricing data with incorrect values before a board meeting</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Provisioned a new EC2 instance on AWS</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Spun up a public-facing server with no security group in production</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Sent a Slack DM to a team lead</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">Sent an internal performance review to the wrong person</div>
        </div>
      </div>
    </div>"""

html = html.replace(old, new)

with open(FILE, "w") as f:
    f.write(html)
print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Fix failures readability' && git push")
