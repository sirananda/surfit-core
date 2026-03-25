#!/usr/bin/env python3
import shutil
FILE = "index.html"
shutil.copy(FILE, FILE + ".arrow")
with open(FILE, "r") as f:
    html = f.read()

# Add a small arrow column between the two content columns in each row
# Replace each row's 2-column grid with a 3-column grid (content | arrow | content)

rows = [
    ("Posted a message to #general in Slack", "Shared confidential revenue data with 500 employees"),
    ("Merged a passing PR to main on GitHub", "Broke the billing pipeline for 3 hours"),
    ("Published a post to the company X account", "Released an unapproved product announcement publicly"),
    ("Updated a Notion database entry", "Overwrote pricing data with incorrect values before a board meeting"),
    ("Provisioned a new EC2 instance on AWS", "Spun up a public-facing server with no security group in production"),
    ("Sent a Slack DM to a team lead", "Sent an internal performance review to the wrong person"),
]

for left, right in rows:
    old_row = f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">{left}</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">{right}</div>
        </div>'''
    
    new_row = f'''<div style="display:grid;grid-template-columns:1fr 30px 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;">
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">{left}</div>
          <div style="background:var(--surface);display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:14px;">→</div>
          <div style="padding:14px 18px;background:var(--surface);font-size:13px;color:var(--text);text-align:left;">{right}</div>
        </div>'''
    
    html = html.replace(old_row, new_row)

with open(FILE, "w") as f:
    f.write(html)
print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Add arrows' && git push")
