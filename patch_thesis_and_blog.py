"""
Two changes:
1. Move evals/credential/PR block from thesis left column to below thesis grid
2. Add Blog nav link to navigation

Run from ~/Desktop/files/: python3 patch_thesis_and_blog.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. REMOVE evals block from inside thesis left column
# ═══════════════════════════════════════════════════════════

remove_block = '''
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

if remove_block in content:
    content = content.replace(remove_block, '')
    changes += 1
    print("✅ 1. Removed evals block from thesis left column")
else:
    print("❌ 1. Could not find evals block. NO CHANGES MADE.")
    exit(1)


# ═══════════════════════════════════════════════════════════
# 2. INSERT evals block below thesis grid, full width
# ═══════════════════════════════════════════════════════════

old_section_end = '''    </div>
  </div>
</section>


<!-- AGENT INTEGRATION FLOW -->'''

new_section_end = '''    </div>

    <!-- EVALS VS CONTROL — full width below grid -->
    <div style="max-width:800px;margin:40px auto 0;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px;">
        <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25);border-radius:10px;padding:18px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--red);margin-bottom:10px;font-weight:600;">Evals ≠ Control</div>
          <div style="font-size:13px;line-height:1.7;color:var(--text);">Evals run inside the agent.<br>They can flag, warn, or suggest.<br><strong style="color:var(--red);">But the agent still executes.</strong></div>
        </div>
        <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.25);border-radius:10px;padding:18px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--blue);margin-bottom:10px;font-weight:600;">Surfit = Control</div>
          <div style="font-size:13px;line-height:1.7;color:var(--text);">Agent does not hold credentials.<br>Every action must pass through Surfit.<br><strong style="color:var(--blue);">Surfit decides, then executes.</strong></div>
        </div>
      </div>

      <p style="font-size:14px;font-style:italic;color:var(--text);border-left:3px solid var(--blue);padding-left:14px;margin:0 0 24px 0;">If the agent holds the credentials, governance is advisory.<br>If an external layer holds them, governance is enforceable.</p>

      <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;padding:18px;">
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
    </div>

  </div>
</section>


<!-- AGENT INTEGRATION FLOW -->'''

if old_section_end in content:
    content = content.replace(old_section_end, new_section_end)
    changes += 1
    print("✅ 2. Inserted evals block below thesis grid — full width")
else:
    print("❌ 2. Could not find thesis section end. Run: git checkout index.html")
    exit(1)


# ═══════════════════════════════════════════════════════════
# 3. ADD Blog nav link
# ═══════════════════════════════════════════════════════════

old_nav = '    <li><a href="#how-it-works">How It Works</a></li>'
new_nav = '    <li><a href="/blog/" style="color:var(--blue);font-weight:600;">Blog</a></li>\n    <li><a href="#how-it-works">How It Works</a></li>'

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    changes += 1
    print("✅ 3. Blog nav link added")
else:
    print("⚠️  3. Nav link — not found, skipping")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied to index.html")
print("If broken: git checkout index.html")
print("")
print("NEXT: Run the blog page creation script (patch_blog_pages.py)")
