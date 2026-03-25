"""
Surfit Site Patch — Landscape Positioning
Adds: "Where Surfit fits" section, FAQ update, names CrowdStrike + OpenClaw
Run from ~/Desktop/files/: python3 patch_positioning.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. NEW SECTION: "Where Surfit Fits" — after dominance section, before CTA
# ═══════════════════════════════════════════════════════════

old_before_cta = '''<!-- CTA -->
<section class="cta-section">'''

new_positioning_section = '''<!-- WHERE SURFIT FITS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:1000px;">
    <div class="section-label">Where Surfit Fits</div>
    <div class="section-title brand-heading" style="">Three layers. Three different questions.</div>
    <p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;max-width:720px;">Agent runtimes, decision infrastructure, and security platforms each solve a different problem. They don't compete — they complement. Surfit is the layer between the agent's intent and the real world.</p>

    <!-- Two-lane diagram -->
    <div style="margin-top:36px;">

      <!-- ACTION PATH (top lane) -->
      <div style="background:rgba(38,192,255,0.04);border:1px solid rgba(38,192,255,0.15);border-radius:12px;padding:24px 28px;margin-bottom:16px;">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:18px;font-weight:600;">Action Path — What happens when an agent acts</div>

        <div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:0;align-items:center;">

          <!-- Agent Runtime -->
          <div style="background:var(--darker);border:1px solid var(--border);border-radius:8px;padding:18px 16px;text-align:center;">
            <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px;">Agent Runtime</div>
            <div style="font-size:11px;color:var(--muted);line-height:1.5;">OpenClaw · LangChain · CrewAI<br>AutoGen · Custom agents</div>
            <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);">
              <div style="font-size:11px;color:var(--orange);font-weight:600;">Decides what to do</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Plans, reasons, selects tools</div>
            </div>
          </div>

          <!-- Arrow -->
          <div style="color:var(--blue);font-size:20px;padding:0 12px;opacity:0.6;">→</div>

          <!-- Surfit -->
          <div style="background:rgba(38,192,255,0.08);border:2px solid rgba(38,192,255,0.35);border-radius:8px;padding:18px 16px;text-align:center;position:relative;">
            <div style="position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:var(--blue);color:#000;font-size:9px;font-weight:700;padding:2px 10px;border-radius:10px;letter-spacing:.1em;">SURFIT</div>
            <div style="font-size:13px;font-weight:600;color:var(--blue);margin-bottom:6px;margin-top:4px;">Decision Infrastructure</div>
            <div style="font-size:11px;color:var(--muted);line-height:1.5;">Evaluates in business context<br>Routes to the right team</div>
            <div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(38,192,255,0.2);">
              <div style="font-size:11px;color:var(--blue);font-weight:600;">Decides what should happen</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Business logic, not security logic</div>
            </div>
          </div>

          <!-- Arrow -->
          <div style="color:var(--blue);font-size:20px;padding:0 12px;opacity:0.6;">→</div>

          <!-- Business Systems -->
          <div style="background:var(--darker);border:1px solid var(--border);border-radius:8px;padding:18px 16px;text-align:center;">
            <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px;">Business Systems</div>
            <div style="font-size:11px;color:var(--muted);line-height:1.5;">Slack · GitHub · Notion<br>Gmail · AWS · CRMs · ERPs</div>
            <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);">
              <div style="font-size:11px;color:var(--green);font-weight:600;">Where actions execute</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Real systems, real consequences</div>
            </div>
          </div>

        </div>
      </div>

      <!-- INFRASTRUCTURE LAYER (bottom lane) -->
      <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px 28px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;font-weight:600;">Infrastructure Layer — Separate concern</div>
            <div style="font-size:13px;font-weight:600;color:var(--text);">Security &amp; Endpoint Platforms</div>
            <div style="font-size:11px;color:var(--muted);margin-top:4px;">CrowdStrike · Palo Alto · Okta · Endpoint protection · Identity management</div>
          </div>
          <div style="text-align:right;min-width:220px;">
            <div style="font-size:11px;color:var(--muted);font-weight:600;">Decides what is allowed</div>
            <div style="font-size:11px;color:var(--muted);margin-top:3px;">Network, process, identity, access control</div>
            <div style="font-size:11px;color:var(--muted);margin-top:3px;font-style:italic;">Does not evaluate business context</div>
          </div>
        </div>
      </div>

      <!-- Caption -->
      <div style="display:flex;justify-content:center;gap:32px;margin-top:20px;">
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--orange);"></span>
          Agent runtimes decide what to do
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--blue);">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--blue);"></span>
          Surfit decides what should happen
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--muted);"></span>
          Security platforms decide what is allowed
        </div>
      </div>

    </div>
  </div>
</section>

<!-- CTA -->
<section class="cta-section">'''

if old_before_cta in content:
    content = content.replace(old_before_cta, new_positioning_section)
    changes += 1
    print("✅ 'Where Surfit Fits' section added")
else:
    print("⚠️  Could not find CTA boundary")


# ═══════════════════════════════════════════════════════════
# 2. UPDATE FAQ — Add CrowdStrike differentiation question
# ═══════════════════════════════════════════════════════════

# Find the FAQ section and add a new question
old_faq_end = '''<p>Surfit is a control layer for AI agents that evaluates every action against your business rules before execution — governing actions across Slack, GitHub, X, Notion, Gmail, Outlook, AWS, and more based on risk.</p>'''

new_faq_end = '''<p>Surfit is decision infrastructure for AI agent actions. It evaluates every action in business context before execution — routing decisions to the right teams across Slack, GitHub, X, Notion, Gmail, Outlook, AWS, and more.</p>'''

if old_faq_end in content:
    content = content.replace(old_faq_end, new_faq_end)
    changes += 1
    print("✅ FAQ 'What is Surfit' updated")

# Add new FAQ entry about CrowdStrike — find the last FAQ item and add after it
# Look for a pattern that indicates the FAQ section
crowdstrike_faq = '''
      <div class="runtime-card">
        <h4>How is Surfit different from security tools like CrowdStrike?</h4>
        <p>Security platforms decide what is <strong>allowed</strong> — they enforce access policies, protect endpoints, and block threats at the infrastructure layer. Surfit decides what <strong>should happen</strong> — it evaluates agent actions in business context and routes decisions to the right teams. Security says "this process can run." Surfit says "this action is correct for the business." Different layer, different purpose. They work together, not in competition.</p>
      </div>

      <div class="runtime-card">
        <h4>How is Surfit different from agent runtime governance (like OpenClaw)?</h4>
        <p>Agent runtimes decide what to <strong>do</strong> — they plan, reason, and select tools. Some runtimes add internal governance features like approvals or sandboxing. But when governance lives inside the agent runtime, it's controlled by the same system it's supposed to constrain. Surfit sits outside the agent entirely — at the execution boundary. It's framework-agnostic, vendor-neutral, and architecturally independent. The agent can't override Surfit because Surfit holds the execution credentials, not the agent.</p>
      </div>'''

# Find where to insert — look for the last FAQ runtime-card closing tag before the section close
# We'll insert before the closing </div> of the runtime-grid in the FAQ section
faq_marker = '<!-- TECHNICAL FAQ -->'
if faq_marker in content:
    # Find the last </div> of the FAQ grid
    faq_start = content.index(faq_marker)
    # Find the runtime-grid div in the FAQ section
    faq_grid_end = content.find('</div>\n  </div>\n</section>', faq_start)
    if faq_grid_end > 0:
        # Insert before the grid closing
        insert_point = content.rfind('</div>', faq_start, faq_grid_end)
        if insert_point > 0:
            content = content[:insert_point] + crowdstrike_faq + '\n' + content[insert_point:]
            changes += 1
            print("✅ CrowdStrike + OpenClaw FAQ entries added")
        else:
            print("⚠️  Could not find FAQ grid insert point")
    else:
        print("⚠️  Could not find FAQ grid end")
else:
    print("⚠️  Could not find FAQ section marker")


# ═══════════════════════════════════════════════════════════
# 3. UPDATE "Adapter SDK" → "Connector Architecture" in Platform Capabilities
# ═══════════════════════════════════════════════════════════

old_adapter = '''<div class="runtime-card"><h4>Connector Architecture</h4><p>Standardized ingest → classify → evaluate → route pattern. Each system connector handles normalization. New systems follow the same integration pattern.</p></div>'''

# Check if it's still "Adapter SDK" (from an older version)
old_adapter_sdk = '''<div class="runtime-card"><h4>Adapter SDK</h4>'''
if old_adapter_sdk in content:
    content = content.replace(old_adapter_sdk, '''<div class="runtime-card"><h4>Connector Architecture</h4>''')
    changes += 1
    print("✅ Adapter SDK → Connector Architecture")
elif old_adapter in content:
    print("ℹ️  Already says 'Connector Architecture'")
else:
    print("ℹ️  Adapter SDK / Connector Architecture — no change needed")


# ═══════════════════════════════════════════════════════════
# 4. UPDATE the "Why a Dedicated Layer" section to reference three-layer model
# ═══════════════════════════════════════════════════════════

old_dominance_title = '''<div class="section-title brand-heading" style="">Agent control requires a dedicated layer.</div>'''
new_dominance_title = '''<div class="section-title brand-heading" style="">Agent control requires a dedicated decision layer.</div>'''

if old_dominance_title in content:
    content = content.replace(old_dominance_title, new_dominance_title)
    changes += 1
    print("✅ Dominance section title updated")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("Now: git add index.html && git commit -m 'positioning: where surfit fits, CrowdStrike/OpenClaw differentiation' && git push")
