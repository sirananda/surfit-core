"""
Blog credential language alignment.
Updates all 3 blog posts to shift from credential-first to decision-first.

Run from ~/Desktop/files/: python3 patch_blogs_v6.py
"""

import os

base = os.path.expanduser("~/Desktop/files")
changes = 0

def safe_replace_file(filepath, label, old, new):
    global changes
    with open(filepath, "r") as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(filepath, "w") as f:
            f.write(content)
        changes += 1
        print(f"✅ {label}")
    else:
        print(f"⚠️  {label} — not found, skipping")


# ═══════════════════════════════════════════════════════════
# BLOG 1: litellm-compromise
# ═══════════════════════════════════════════════════════════

litellm = os.path.join(base, "blog", "litellm-compromise", "index.html")

safe_replace_file(litellm, "LiteLLM 1: alternative architecture",
    '<p><strong class="blue">Agent environment</strong> contains: agent code + dependencies (no credentials)</p>\n      <p><strong class="blue">External decision layer</strong> contains: credentials + policy evaluation + execution authority</p>',
    '<p><strong class="orange">Agent environment</strong> contains: agent code + dependencies (no credentials)</p>\n      <p><strong class="blue">External execution layer</strong> contains: policy evaluation + execution authority + credential management</p>')

safe_replace_file(litellm, "LiteLLM 2: Surfit holds credentials",
    'Surfit holds the credentials. The agent doesn\'t.</strong>',
    'Surfit controls the execution path. The agent doesn\'t execute directly.</strong>')

safe_replace_file(litellm, "LiteLLM 3: executes using credentials",
    'Surfit evaluates the action in business context, and if approved, executes it using credentials only Surfit holds.',
    'Surfit evaluates the action in business context, and if approved, executes it using credentials the agent never touches — whether managed by Surfit directly or integrated with the customer\'s own credential vault.')


# ═══════════════════════════════════════════════════════════
# BLOG 2: landscape-march-2026
# ═══════════════════════════════════════════════════════════

landscape = os.path.join(base, "blog", "landscape-march-2026", "index.html")

safe_replace_file(landscape, "Landscape 1: intro credential line",
    'None of them hold the credentials. None of them evaluate whether a specific action should happen for the business right now.',
    'None of them sit in the execution path. None of them evaluate whether a specific action should happen for the business right now.')

safe_replace_file(landscape, "Landscape 2: Surfit card credential line",
    'Surfit holds the credentials. The agent doesn\'t.</strong> The agent calls Surfit\'s API, not the external system\'s API. Surfit evaluates the action and executes using credentials only Surfit holds. The agent never touches the external system directly.',
    'Surfit controls the execution path. The agent doesn\'t execute directly.</strong> The agent calls Surfit\'s API, not the external system\'s API. Surfit evaluates the action in business context and executes on behalf of the agent — using credentials the agent never touches.')

safe_replace_file(landscape, "Landscape 3: pattern section",
    'The agent never holds the credentials. The agent never touches the system directly.',
    'The agent never executes directly. The agent never touches the system without Surfit in the path.')


# ═══════════════════════════════════════════════════════════
# BLOG 3: introducing-surfit
# ═══════════════════════════════════════════════════════════

intro = os.path.join(base, "blog", "introducing-surfit", "index.html")

safe_replace_file(intro, "Intro 1: architectural distinction header",
    '<strong class="blue">Surfit holds the credentials. The agent doesn\'t.</strong>',
    '<strong class="blue">Surfit controls the execution path. The agent doesn\'t execute directly.</strong>')

safe_replace_file(intro, "Intro 2: architecture explanation",
    'Surfit evaluates the action, and if approved, executes it using credentials only Surfit holds. The agent never touches the external system\'s credentials.',
    'Surfit evaluates the action in business context, and if approved, executes it — using credentials the agent never touches, whether managed by Surfit or integrated with the customer\'s own vault.')

safe_replace_file(intro, "Intro 3: evals box - agent holds credentials",
    'But the agent still holds the credentials. It can bypass, remove, or reconfigure the eval. <strong>Governance is advisory.</strong>',
    'But the agent still controls execution. It can bypass, remove, or reconfigure the eval. <strong>Governance is advisory.</strong>')

safe_replace_file(intro, "Intro 4: surfit box - credentials",
    'The agent does not hold credentials. Every action must pass through Surfit. Surfit evaluates in business context and executes using its own credentials. <strong class="blue">Governance is enforceable.</strong>',
    'The agent does not execute directly. Every action must pass through Surfit. Surfit evaluates in business context and controls execution. <strong class="blue">Governance is enforceable.</strong>')

safe_replace_file(intro, "Intro 5: core distinction line",
    'if the agent holds the credentials, governance is advisory. If an external layer holds them, governance is enforceable.',
    'if the agent controls execution, governance is advisory. If an external layer controls execution, governance is enforceable.')

safe_replace_file(intro, "Intro 6: why cant existing tools",
    'rearchitect their entire product so the agent no longer holds credentials.',
    'rearchitect their entire product to sit in the execution path and evaluate business context for every action.')

safe_replace_file(intro, "Intro 7: closing line",
    'Credential separation isn\'t a feature — it\'s the foundation the entire product is built on.',
    'Execution authority isn\'t a feature — it\'s the foundation the entire product is built on.')


# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════

print(f"\n✅ Done — {changes} changes across 3 blog posts")
print("If good: git add -A && git commit -m 'blogs v6: credential language → execution path, business decisions' && git push")
