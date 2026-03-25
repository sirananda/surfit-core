"""
Fixes:
1. Blog index: remove top category row, center column headers with boxes, spacing, font
2. Fix Architecture nav link → #how-it-works
3. Hero: remove line 5 (redundant)

Run from ~/Desktop/files/: python3 patch_blog_fixes2.py
"""

import os

base = os.path.expanduser("~/Desktop/files")
changes = 0

# ═══════════════════════════════════════════════════════════
# 1. BLOG INDEX — remove top categories, fix column headers, spacing, font
# ═══════════════════════════════════════════════════════════

blog_index = os.path.join(base, "blog", "index.html")
with open(blog_index, "r") as f:
    content = f.read()

# Remove the top category row entirely
old = '''  <div class="blog-categories">
    <span class="blog-cat landscape">Surfit Updates</span>
    <span class="blog-cat update">Landscape</span>
    <span class="blog-cat incident">Incidents</span>
  </div>'''
new = ''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1a. Removed top category row")

# Fix column header styles — centered with box styling + gap between columns
old = '''  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding:40px 0;">

    <!-- Column 1: Surfit Updates -->
    <div>
      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(38,192,255,0.2);">Surfit Updates</div>'''
new = '''  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:32px;padding:40px 0;">

    <!-- Column 1: Surfit Updates -->
    <div>
      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:16px;padding:6px 14px;border:1px solid rgba(38,192,255,0.3);border-radius:6px;text-align:center;">Surfit Updates</div>'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1b. Column 1 header — centered with box, wider gap")

# Column 2
old = '''      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--orange);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(255,115,30,0.2);">Landscape</div>'''
new = '''      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--orange);font-weight:600;margin-bottom:16px;padding:6px 14px;border:1px solid rgba(255,115,30,0.3);border-radius:6px;text-align:center;">Landscape</div>'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1c. Column 2 header — centered with box")

# Column 3
old = '''      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(239,68,68,0.2);">Incidents</div>'''
new = '''      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:16px;padding:6px 14px;border:1px solid rgba(239,68,68,0.3);border-radius:6px;text-align:center;">Incidents</div>'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1d. Column 3 header — centered with box")

# Fix blog header font to match main site
old = '''  font-family:'Righteous',cursive; font-size:42px; color:var(--text);'''
new = '''  font-family:'Righteous',cursive; font-size:42px; color:var(--text); letter-spacing:0.02em;'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1e. Blog header font — added letter spacing to match site")

with open(blog_index, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# 2. MAIN SITE — Fix Architecture nav link
# ═══════════════════════════════════════════════════════════

filepath = os.path.join(base, "index.html")
with open(filepath, "r") as f:
    content = f.read()

old = '<li><a href="#architecture">Architecture</a></li>'
new = '<li><a href="#how-it-works">Architecture</a></li>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. Architecture nav → #how-it-works")

# ═══════════════════════════════════════════════════════════
# 3. HERO — Remove redundant line 5
# ═══════════════════════════════════════════════════════════

old = '<p class="hero-sub">Control and route AI actions across your systems — before they execute.</p>'
new = ''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3. Hero — removed redundant 'Control and route' line")
else:
    # Try alternative format
    old2 = 'Control and route AI actions across your systems — before they execute.'
    if old2 in content:
        # Find the full line
        idx = content.index(old2)
        # Get surrounding context
        before = content[max(0,idx-100):idx]
        print(f"⚠️  3. Hero line found but in different wrapper. Context: ...{before[-40:]}")
    else:
        print("⚠️  3. Hero 'Control and route' line — not found, skipping")

with open(filepath, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════

print(f"\n✅ Done — {changes} changes applied")
print("If broken on main site: git checkout index.html")
print("If good: git add -A && git commit -m 'blog fixes round 2: column headers, spacing, nav, hero cleanup' && git push")
