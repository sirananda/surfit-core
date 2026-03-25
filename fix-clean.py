#!/usr/bin/env python3
"""Remove redundant section + center Who Needs Surfit"""
import shutil, re

FILE = "index.html"
shutil.copy(FILE, FILE + ".v28b")

with open(FILE, "r") as f:
    html = f.read()

# 1. Remove the "How Surfit Works" three-box section entirely
# It starts with <!-- RUNTIME MODEL --> and ends before <!-- COMPARISON TABLE -->
start_marker = '<!-- RUNTIME MODEL -->'
end_marker = '<!-- COMPARISON TABLE -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    html = html[:start_idx] + '\n' + html[end_idx:]
    print("✓ Removed 'How Surfit Works' three-box section")
else:
    print("⚠ Could not find RUNTIME MODEL section markers")

# 2. Center the Who Needs Surfit teams grid
html = html.replace(
    '<div class="teams-grid" style="margin-top:26px;max-width:980px;">',
    '<div class="teams-grid" style="margin-top:26px;max-width:980px;margin-left:auto;margin-right:auto;">'
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Done")
print("Deploy: git add index.html && git commit -m 'Remove redundant section + center cards' && git push")
