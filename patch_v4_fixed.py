"""
SURFIT SITE PATCH — V4 Positioning (FIXED)
Uses exact strings from the actual index.html file.

Run from ~/Desktop/files/: python3 patch_v4_fixed.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. HERO — Add category-defining line above tagline
# ═══════════════════════════════════════════════════════════

old = '<p class="hero-tagline">Agents can act. Surfit makes sure those actions are correct for your business.</p>'
new = '<p style="font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;font-weight:600;">Evals don\'t control execution. Surfit does.</p>\n    <p class="hero-tagline">Agents can act. Surfit makes sure those actions are correct for your business.</p>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 1. Hero — category line added")
else:
    print("⚠️  1. Hero — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 2. THESIS — Add evals ≠ control block + credential line + PR flow
#    Insert after the "Correctness is defined" line
# ═══════════════════════════════════════════════════════════

old = '          Correctness is defined by your policies — not the agent. Surfit evaluates every action before execution.'
new = '''          Correctness is defined by your policies — not the agent. Surfit evaluates every action before execution.
        </p>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:28px 0;max-width:800px;">
          <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25);border-radius:10px;padding:18px;">
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--red);margin-bottom:10px;font-weight:600;">Evals ≠ Control</div>
            <div style="font-size:13px;line-height:1.7;color:var(--text);">Evals run inside the agent.<br>They can flag, warn, or suggest.<br><strong style="color:var(--red);">But the agent still executes.</strong></div>
          </div>
          <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.25);border-radius:10px;padding:18px;">
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Surfit = Control</div>
            <div style="font-size:13px;line-height:1.7;color:var(--text);">Agent does not hold credentials.<br>Every action must pass through Surfit.<br><strong style="color:var(--blue);">Surfit decides, then executes.</strong></div>
          </div>
        </div>

        <p style="font-size:14px;font-style:italic;color:var(--text);border-left:3px solid var(--blue);padding-left:14px;margin:20px 0;">If the agent holds the credentials, governance is advisory.<br>If an external layer holds them, governance is enforceable.</p>

        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;padding:18px;margin:24px 0;max-width:800px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:var(--muted);margin-bottom:12px;">Example: Agent wants to merge a PR</div>
          <div style="font-size:13px;line-height:1.8;color:var(--muted);">
            Guardrails → output is fine ✓<br>
            CTGT → model is compliant ✓<br>
            IronClaw → permissions are safe ✓<br>
            <span style="color:var(--red);font-weight:600;">So it goes through… into production. Payments break.</span>
          </div>
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);font-size:13px;line-height:1.8;color:var(--muted);">
            <strong style="color:var(--blue);">With Surfit:</strong><br>
            → Intercepts before execution<br>
            → Evaluates business context (production branch, payment code, no review)<br>
            → <strong style="color:var(--blue);">Holds the action. Business protected.</strong>
          </div>
        </div>

        <p style="display:none;">'''

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 2. Thesis — evals vs control block + credential line + PR flow added")
else:
    print("⚠️  2. Thesis — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 3. GAP — Change "Nobody evaluates" to enforcement language
# ═══════════════════════════════════════════════════════════

old = '<div style="font-size:9px;color:var(--muted);margin-top:2px;">Nobody evaluates<br>business impact</div>'
new = '<div style="font-size:9px;color:var(--muted);margin-top:2px;">Nobody controls whether<br>the action happens</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 3. Gap — evaluates → controls")
else:
    print("⚠️  3. Gap — not found, skipping")


# ═══════════════════════════════════════════════════════════
# 4. GAP — Add brutal one-liner after punchline
# ═══════════════════════════════════════════════════════════

old = 'No layer evaluated whether it should. No one was in the path.</div>'
new = 'No layer evaluated whether it should. No one was in the path.</div>\n      <div style="text-align:center;margin-top:14px;font-size:14px;font-weight:600;color:var(--red);">Everything passed checks. It still went through.</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 4. Gap — brutal one-liner added")
else:
    print("⚠️  4. Gap — punchline not found, skipping")


# ═══════════════════════════════════════════════════════════
# 5. LANDSCAPE — Add bypass line to Guardrails card
# ═══════════════════════════════════════════════════════════

old = '<div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Does not govern what the agent does to real systems</div>\n      </div>\n\n      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">\n        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">02</span>Model Behavior Control</div>'
new = '<div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Runs inside the agent — agent can bypass, remove, or reconfigure</div>\n      </div>\n\n      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">\n        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;"><span style="color:var(--orange);margin-right:6px;">02</span>Model Behavior Control</div>'

if old in content:
    content = content.replace(old, new)
    changes += 1
    print("✅ 5. Landscape — Guardrails bypass line replaced")
else:
    print("⚠️  5. Landscape — Guardrails card not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes}/5 changes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'v4 positioning sharpening — evals vs control, credential line, PR flow' && git push")
