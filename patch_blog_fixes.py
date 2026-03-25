"""
Blog and site fixes:
1. Move Blog nav link to right side (before Visualization)
2. Fix blog index: 3-column layout, rename categories, reorder
3. Fix introducing-surfit: readability, remove waves, system count, remove Twitter
4. Fix litellm: orange header on agent environment

Run from ~/Desktop/files/: python3 patch_blog_fixes.py
"""

import os

base = os.path.expanduser("~/Desktop/files")
changes = 0

# ═══════════════════════════════════════════════════════════
# 1. MAIN SITE — Move Blog nav link before Visualization
# ═══════════════════════════════════════════════════════════

filepath = os.path.join(base, "index.html")
with open(filepath, "r") as f:
    content = f.read()

# Remove Blog from current position (before How It Works)
old = '    <li><a href="/blog/" style="color:var(--blue);font-weight:600;">Blog</a></li>\n    <li><a href="#how-it-works">How It Works</a></li>'
new = '    <li><a href="#how-it-works">How It Works</a></li>'

if old in content:
    content = content.replace(old, new)
    # Now add Blog before Visualization
    old2 = '    <li><a href="#visualization" class="nav-link-btn visualization">Visualization</a></li>'
    new2 = '    <li><a href="/blog/" style="color:var(--blue);font-weight:600;">Blog</a></li>\n    <li><a href="#visualization" class="nav-link-btn visualization">Visualization</a></li>'
    if old2 in content:
        content = content.replace(old2, new2)
        changes += 1
        print("✅ 1. Blog nav moved to right side (before Visualization)")
    else:
        print("⚠️  1. Could not find Visualization nav link")
else:
    print("⚠️  1. Blog nav link not found in expected position")

with open(filepath, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# 2. BLOG INDEX — 3-column layout, rename categories, reorder
# ═══════════════════════════════════════════════════════════

blog_index = os.path.join(base, "blog", "index.html")
with open(blog_index, "r") as f:
    content = f.read()

# Fix category names and order
old = '''    <span class="blog-cat incident">Incidents</span>
    <span class="blog-cat landscape">Landscape</span>
    <span class="blog-cat update">Updates</span>'''
new = '''    <span class="blog-cat landscape">Surfit Updates</span>
    <span class="blog-cat update">Landscape</span>
    <span class="blog-cat incident">Incidents</span>'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2a. Blog categories renamed and reordered")

# Replace post list with 3-column layout
old_posts = '''  <div class="post-list">

    <a href="/blog/introducing-surfit" class="post-card">
      <div class="post-meta">
        <span class="post-tag landscape">Landscape</span>
        <span class="post-date">March 25, 2026</span>
      </div>
      <h2>Introducing Surfit — The Decision Layer for AI Agent Actions</h2>
      <p>Evals check what the model says. Sandboxes control where agents run. Nobody controls what actually happens when an agent acts on a real system. That's the layer Surfit builds.</p>
    </a>

    <a href="/blog/litellm-compromise" class="post-card">
      <div class="post-meta">
        <span class="post-tag incident">Incident</span>
        <span class="post-date">March 25, 2026</span>
      </div>
      <h2>LiteLLM Got Compromised. Here's Why Your Agent's Credentials Shouldn't Live Where They Can Be Stolen.</h2>
      <p>A malicious version of one of the most popular Python LLM libraries was pushed to PyPI. It stole every credential on the machine. This is exactly why credentials shouldn't live in the agent's environment.</p>
    </a>

  </div>'''

new_posts = '''  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding:40px 0;">

    <!-- Column 1: Surfit Updates -->
    <div>
      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(38,192,255,0.2);">Surfit Updates</div>
      <a href="/blog/introducing-surfit" class="post-card">
        <div class="post-meta">
          <span class="post-tag landscape">Surfit Updates</span>
          <span class="post-date">March 25, 2026</span>
        </div>
        <h2>Introducing Surfit — The Decision Layer for AI Agent Actions</h2>
        <p>Evals check what the model says. Sandboxes control where agents run. Nobody controls what actually happens when an agent acts on a real system.</p>
      </a>
    </div>

    <!-- Column 2: Landscape -->
    <div>
      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--orange);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(255,115,30,0.2);">Landscape</div>
      <div style="font-size:13px;color:var(--muted);font-style:italic;padding:20px 0;">Coming soon — industry analysis and competitive landscape.</div>
    </div>

    <!-- Column 3: Incidents -->
    <div>
      <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(239,68,68,0.2);">Incidents</div>
      <a href="/blog/litellm-compromise" class="post-card">
        <div class="post-meta">
          <span class="post-tag incident">Incident</span>
          <span class="post-date">March 25, 2026</span>
        </div>
        <h2>LiteLLM Got Compromised. Here's Why Your Agent's Credentials Shouldn't Live Where They Can Be Stolen.</h2>
        <p>A malicious version of one of the most popular Python LLM libraries was pushed to PyPI. It stole every credential on the machine.</p>
      </a>
    </div>

  </div>'''

if old_posts in content:
    content = content.replace(old_posts, new_posts)
    changes += 1
    print("✅ 2b. Blog index — 3-column layout with category headers")

# Update the subtitle
old = '<p>Incidents, landscape analysis, and the case for decision infrastructure.</p>'
new = '<p>Product updates, industry landscape, and incident analysis.</p>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2c. Blog subtitle updated")

# Fix container width for 3 columns
old = '<div class="container">'
new = '<div class="container" style="max-width:1000px;">'
if old in content:
    content = content.replace(old, new, 1)  # Only first occurrence
    changes += 1
    print("✅ 2d. Blog container widened for 3 columns")

with open(blog_index, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# 3. INTRODUCING SURFIT — readability, remove waves, systems, Twitter
# ═══════════════════════════════════════════════════════════

intro_path = os.path.join(base, "blog", "introducing-surfit", "index.html")
with open(intro_path, "r") as f:
    content = f.read()

# Make body text brighter (muted → lighter)
old = "color:var(--muted);\n  margin-bottom:16px; font-weight:300;"
new = "color:rgba(226,232,240,0.75);\n  margin-bottom:16px; font-weight:300;"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3a. Introducing Surfit — body text brightened")

# Remove Wave references under "What Surfit Does"
old = '''<div class="highlight">
      <p><strong>Wave 1–3:</strong> Low-risk actions execute automatically with full logging. A Slack update to #eng-platform, a Notion log entry, a PR to a dev branch — these flow through instantly. No friction.</p>
      <p><strong>Wave 4–5:</strong> High-risk actions are held. A PR merge to main that touches payment code. A post to the company X account. An AWS infrastructure change. These are intercepted before execution and surfaced with full context.</p>
    </div>

    <p>Most actions never need a human. Surfit's risk classification determines what flows and what's caught — based on content, destination, and context, not static rules.</p>'''
new = '''<div class="highlight">
      <p><strong>Low-risk actions</strong> execute automatically with full logging. A Slack update to #eng-platform, a Notion log entry, a PR to a dev branch — these flow through instantly. No friction.</p>
      <p><strong>High-risk actions</strong> are held before execution. A PR merge to main that touches payment code. A post to the company X account. An AWS infrastructure change. These are intercepted and surfaced with full context.</p>
    </div>

    <p>Most actions never need a human. Surfit's risk classification determines what flows and what's caught — based on content, destination, and context, not static rules.</p>'''
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3b. Introducing Surfit — removed Wave references")

# Fix system count and remove (Twitter)
old = 'Surfit currently governs agent actions across seven system categories: <strong>Slack, GitHub, X (Twitter), Notion, Gmail, Outlook, and AWS</strong>.'
new = 'Surfit currently governs agent actions across ten system categories, including <strong>Slack, GitHub, X, Notion, Gmail, Outlook, and AWS</strong>.'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3c. Introducing Surfit — system count + removed Twitter")

# Fix the landscape tag on the post
old = '<span class="post-tag landscape">Landscape</span>'
new = '<span class="post-tag landscape">Surfit Updates</span>'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3d. Introducing Surfit — tag renamed to Surfit Updates")

with open(intro_path, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# 4. LITELLM POST — orange header on agent environment in alternative arch
# ═══════════════════════════════════════════════════════════

litellm_path = os.path.join(base, "blog", "litellm-compromise", "index.html")
with open(litellm_path, "r") as f:
    content = f.read()

# The "alternative architecture" section has Agent Environment in blue, should be orange for first one
old = '''<p><strong class="blue">Agent environment</strong> contains: agent code + dependencies (no credentials)</p>'''
new = '''<p><strong class="orange">Agent environment</strong> contains: agent code + dependencies (no credentials)</p>'''
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4. LiteLLM post — Agent Environment header changed to orange")

with open(litellm_path, "w") as f:
    f.write(content)


# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════

print(f"\n✅ Done — {changes} changes applied")
print("If broken: git checkout index.html (main site only)")
print("If good: git add -A && git commit -m 'blog fixes: 3-col layout, nav position, readability, categories' && git push")
