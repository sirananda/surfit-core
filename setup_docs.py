"""
1. Create docs directory and copy docs page
2. Add Docs nav link to main site

Run from ~/Desktop/files/: python3 setup_docs.py
"""

import os
import shutil

base = os.path.expanduser("~/Desktop/files")

# 1. Create docs directory
docs_dir = os.path.join(base, "docs")
os.makedirs(docs_dir, exist_ok=True)

# 2. Copy docs file
src = os.path.join(base, "docs-index.html")
dest = os.path.join(docs_dir, "index.html")
if os.path.exists(src):
    shutil.copy2(src, dest)
    print("✅ docs/index.html created")
else:
    print("❌ docs-index.html not found in ~/Desktop/files/")
    exit(1)

# 3. Add Docs nav link to main site
index_path = os.path.join(base, "index.html")
with open(index_path, "r") as f:
    content = f.read()

old = '    <li><a href="/blog/" style="color:var(--blue);font-weight:600;">Blog</a></li>'
new = '    <li><a href="/blog/" style="color:var(--blue);font-weight:600;">Blog</a></li>\n    <li><a href="/docs/" style="color:var(--blue);font-weight:600;">Docs</a></li>'

if '/docs/' not in content:
    if old in content:
        content = content.replace(old, new)
        with open(index_path, "w") as f:
            f.write(content)
        print("✅ Docs nav link added to main site")
    else:
        print("⚠️  Blog nav link not found — add Docs manually")
else:
    print("✅ Docs link already exists in nav")

print("\n✅ Done")
print("git add -A && git commit -m 'add technical documentation page' && git push")
