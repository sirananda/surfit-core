"""
Patch: Update demo video link and copy on surfit.ai
Run from ~/Desktop/files/: python3 patch_demo.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

# 1. Replace Loom embed URL
old_loom = "https://www.loom.com/embed/fc96615026364af89a84a15667dc25f3"
new_loom = "https://www.loom.com/embed/13572a5d0d754e9fa0162d51dbc07064"

if old_loom in content:
    content = content.replace(old_loom, new_loom)
    print("✅ Loom embed URL updated")
else:
    print("⚠️  Old Loom URL not found — may already be updated")

# 2. Replace demo description copy
old_copy = '<p class="section-body" style="max-width:640px;">Surfit controls how agent actions are handled across your systems — before they execute.</p>'
new_copy = '<p class="section-body" style="max-width:640px;">Surfit evaluates and controls every agent action across your systems... before it executes.<br>Lower-risk actions flow automatically... higher-risk actions are held for approval.<br>Every decision is logged, traceable, and enforced in real time.</p>'

if old_copy in content:
    content = content.replace(old_copy, new_copy)
    print("✅ Demo description updated")
else:
    print("⚠️  Old demo copy not found — may already be updated")

# 3. Fix title tag if it says "Agent Actions" instead of control layer
old_title = "Control Layer for Agent Actions"
new_title = "Control Layer for AI Agents"
if old_title in content:
    content = content.replace(old_title, new_title)
    print("✅ Title tag updated")

with open(filepath, "w") as f:
    f.write(content)

print("✅ Done. Now: git add index.html && git commit -m 'update demo video + copy' && git push")
