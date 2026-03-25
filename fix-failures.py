#!/usr/bin/env python3
"""Expand Where agents fail — 2 columns, 6 examples, all systems"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".v28e")

with open(FILE, "r") as f:
    html = f.read()

old_section = """    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:24px auto 28px;max-width:700px;text-align:left;">
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent posts confidential data to a public Slack channel</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent merges valid code that breaks production</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent triggers the wrong workflow across systems</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent publishes an unapproved statement to your public timeline</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent updates a database with logically incorrect values</div>
      <div style="padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-left:3px solid #ef4444;border-radius:6px;font-size:13px;color:var(--text);">An agent sends the right message to the wrong audience</div>
    </div>
    <p style="font-size:14px;color:var(--muted);margin-bottom:8px;">These actions are technically valid — but operationally wrong.</p>
    <p style="font-size:16px;color:var(--blue);font-weight:600;">Surfit prevents this.</p>"""

new_section = """    <div style="max-width:820px;margin:24px auto 28px;">
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
    </div>
    <p style="font-size:14px;color:var(--muted);margin-bottom:8px;">Every action above was technically valid — but operationally wrong.</p>
    <p style="font-size:16px;color:var(--blue);font-weight:600;">Surfit prevents this.</p>"""

html = html.replace(old_section, new_section)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Expand agent failures' && git push")
