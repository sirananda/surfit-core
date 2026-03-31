"""
Add Claude Code leak blog post.
1. Create directory and copy HTML
2. Add post card to blog index under Incidents column

Run from ~/Desktop/files/: python3 add_claude_code_leak.py
"""

import os
import shutil

base = os.path.expanduser("~/Desktop/files")

# 1. Create directory and copy
dest_dir = os.path.join(base, "blog", "claude-code-leak")
os.makedirs(dest_dir, exist_ok=True)

src = os.path.join(base, "claude-code-leak.html")
dest = os.path.join(dest_dir, "index.html")
if os.path.exists(src):
    shutil.copy2(src, dest)
    print("✅ blog/claude-code-leak/index.html created")
else:
    print("❌ claude-code-leak.html not found in ~/Desktop/files/")
    exit(1)

# 2. Add card to blog index — after the LiteLLM card in Incidents column
blog_index = os.path.join(base, "blog", "index.html")
with open(blog_index, "r") as f:
    content = f.read()

# Find the end of the LiteLLM card and add the new card after it
old = '''        <p>A malicious version of one of the most popular Python LLM libraries was pushed to PyPI. It stole every credential on the machine.</p>
      </a>
    </div>'''

new = '''        <p>A malicious version of one of the most popular Python LLM libraries was pushed to PyPI. It stole every credential on the machine.</p>
      </a>

      <a href="/blog/claude-code-leak" class="post-card">
        <div class="post-meta">
          <span class="post-tag incident">Incident</span>
          <span class="post-date">March 31, 2026</span>
        </div>
        <h2>Claude Code's Source Got Leaked Through a Build Pipeline.</h2>
        <p>Anthropic built Undercover Mode to stop their AI from leaking internal information. A source map in an npm package leaked everything.</p>
      </a>
    </div>'''

if old in content:
    content = content.replace(old, new)
    with open(blog_index, "w") as f:
        f.write(content)
    print("✅ Blog index updated — Claude Code leak card added to Incidents")
else:
    print("⚠️  Blog index — LiteLLM card end not found, skipping")

print("\nIf good: git add -A && git commit -m 'add claude code leak incident blog post' && git push")
