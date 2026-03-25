"""
Add the Landscape blog post:
1. Create directory and copy the HTML file
2. Add the post card to the blog index under the Landscape column

Run from ~/Desktop/files/: python3 add_landscape_post.py
"""

import os
import shutil

base = os.path.expanduser("~/Desktop/files")

# 1. Create directory
dest_dir = os.path.join(base, "blog", "landscape-march-2026")
os.makedirs(dest_dir, exist_ok=True)
print(f"✅ Directory: {dest_dir}")

# 2. Copy file
src = os.path.join(base, "landscape-march-2026.html")
dest = os.path.join(dest_dir, "index.html")
if os.path.exists(src):
    shutil.copy2(src, dest)
    print(f"✅ Copied landscape-march-2026.html → blog/landscape-march-2026/index.html")
else:
    print(f"❌ Source file not found: {src}")
    print("   Make sure landscape-march-2026.html is in ~/Desktop/files/")
    exit(1)

# 3. Update blog index — add post card to Landscape column
blog_index = os.path.join(base, "blog", "index.html")
with open(blog_index, "r") as f:
    content = f.read()

old = '''      <div style="font-size:13px;color:var(--muted);font-style:italic;padding:20px 0;">Coming soon — industry analysis and competitive landscape.</div>'''

new = '''      <a href="/blog/landscape-march-2026" class="post-card">
        <div class="post-meta">
          <span class="post-tag update">Landscape</span>
          <span class="post-date">March 26, 2026</span>
        </div>
        <h2>The AI Agent Control Landscape — March 2026</h2>
        <p>Every major tool in the stack — what layer they operate at, what they do well, and why execution authority remains unsolved.</p>
      </a>'''

if old in content:
    content = content.replace(old, new)
    print("✅ Blog index updated — Landscape post card added")
else:
    print("⚠️  Blog index — placeholder text not found, skipping")

with open(blog_index, "w") as f:
    f.write(content)

print("\n✅ Done")
print("If good: git add -A && git commit -m 'add landscape march 2026 blog post' && git push")
