"""
Creates blog directory structure in ~/Desktop/files/
Copies blog pages into the right locations for Vercel.

Run from ~/Desktop/files/: python3 setup_blog.py
"""

import os
import shutil

base = os.path.expanduser("~/Desktop/files")

# Create directories
dirs = [
    os.path.join(base, "blog"),
    os.path.join(base, "blog", "introducing-surfit"),
    os.path.join(base, "blog", "litellm-compromise"),
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✅ Directory: {d}")

# The blog files should already be downloaded to ~/Desktop/files/
# Move them to the right locations

files_to_move = {
    "blog_index.html": "blog/index.html",
    "introducing-surfit.html": "blog/introducing-surfit/index.html",
    "litellm-compromise.html": "blog/litellm-compromise/index.html",
}

for src_name, dest_path in files_to_move.items():
    src = os.path.join(base, src_name)
    dest = os.path.join(base, dest_path)
    if os.path.exists(src):
        shutil.copy2(src, dest)
        print(f"✅ Copied {src_name} → {dest_path}")
    else:
        print(f"❌ Source file not found: {src}")
        print(f"   Make sure {src_name} is downloaded to ~/Desktop/files/")

print("\n✅ Blog structure created")
print("Next: run patch_thesis_and_blog.py to add nav link + fix thesis")
print("Then: git add -A && git commit -m 'add blog with two launch posts' && git push")
