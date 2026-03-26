"""
Replace landscape blog post with v2 (4-layer model, all competitors, SVG diagram).

Run from ~/Desktop/files/: python3 replace_landscape.py
"""

import os
import shutil

base = os.path.expanduser("~/Desktop/files")

src = os.path.join(base, "landscape-march-2026-v2.html")
dest = os.path.join(base, "blog", "landscape-march-2026", "index.html")

if os.path.exists(src):
    shutil.copy2(src, dest)
    print(f"✅ Replaced blog/landscape-march-2026/index.html with v2")
    print("If good: git add -A && git commit -m 'landscape blog v2: 4-layer model, 19 competitors, SVG diagram' && git push")
else:
    print(f"❌ Source file not found: {src}")
    print("   Make sure landscape-march-2026-v2.html is in ~/Desktop/files/")
