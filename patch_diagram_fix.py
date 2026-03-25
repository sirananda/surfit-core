"""
Surfit Site Patch — Fix FAQ nesting + Redesign positioning diagram
Run from ~/Desktop/files/: python3 patch_diagram_fix.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. REPLACE THE ENTIRE "WHERE SURFIT FITS" SECTION
#    - Number the layers (1, 2)
#    - De-emphasize Business Systems (it's a destination, not a layer)
#    - Make Surfit MUCH more assertive
#    - Infrastructure layer gets its own number (separate lane)
# ═══════════════════════════════════════════════════════════

old_section_start = '''<!-- WHERE SURFIT FITS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">'''

# Find the end of this section (next section start)
old_section_end = '''<!-- CTA -->'''

if old_section_start in content and old_section_end in content:
    start_idx = content.index(old_section_start)
    end_idx = content.index(old_section_end)
    old_section = content[start_idx:end_idx]
    
    new_section = '''<!-- WHERE SURFIT FITS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:1000px;">
    <div class="section-label">Where Surfit Fits</div>
    <div class="section-title brand-heading" style="">Three layers. Three different questions.</div>
    <p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;max-width:720px;">Agent runtimes, business decision infrastructure, and security platforms each solve a fundamentally different problem. They don't overlap. They can't replace each other. Surfit is the final authority between the agent's intent and the real world.</p>

    <div style="margin-top:36px;">

      <!-- LAYER 1: AGENT RUNTIME -->
      <div style="display:grid;grid-template-columns:44px 1fr;gap:16px;align-items:start;margin-bottom:16px;">
        <div style="width:44px;height:44px;border-radius:50%;background:var(--orange);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#000;margin-top:18px;">1</div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:22px 28px;">
          <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;font-weight:600;">Layer 1 — Agent Runtime</div>
          <div style="font-size:16px;font-weight:600;color:var(--text);margin-bottom:4px;">Decides what to do</div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:10px;">OpenClaw · LangChain · CrewAI · AutoGen · Custom agents</div>
          <div style="font-size:13px;color:var(--muted);line-height:1.7;">The agent plans, reasons, and selects tools. It determines intent. But intent is not execution — the agent proposes an action. It does not get to decide whether that action is correct for the business, nor does it get to execute it directly.</div>
        </div>
      </div>

      <!-- ARROW -->
      <div style="display:flex;align-items:center;padding-left:22px;margin-bottom:16px;">
        <div style="width:2px;height:32px;background:var(--blue);opacity:0.4;margin-left:0;"></div>
        <div style="color:var(--blue);font-size:13px;margin-left:16px;opacity:0.6;">Agent proposes action ↓</div>
      </div>

      <!-- LAYER 2: SURFIT -->
      <div style="display:grid;grid-template-columns:44px 1fr;gap:16px;align-items:start;margin-bottom:16px;">
        <div style="width:44px;height:44px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#000;margin-top:18px;">2</div>
        <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.35);border-radius:12px;padding:22px 28px;position:relative;">
          <div style="position:absolute;top:-10px;right:20px;background:var(--blue);color:#000;font-size:9px;font-weight:700;padding:2px 12px;border-radius:10px;letter-spacing:.1em;">SURFIT</div>
          <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:8px;font-weight:600;">Layer 2 — Decision Infrastructure</div>
          <div style="font-size:16px;font-weight:600;color:var(--blue);margin-bottom:4px;">Decides what should happen</div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:10px;">Business context · Team routing · Cross-system consistency · Execution authority</div>
          <div style="font-size:13px;color:var(--text);line-height:1.7;margin-bottom:12px;">Every action the agent proposes is intercepted here — before it touches any system. Surfit evaluates the action in business context: Is this the right action for the organization? Does the right team know? Should this proceed automatically or does a human need to decide?</div>
          <div style="font-size:13px;color:var(--text);line-height:1.7;margin-bottom:12px;">This layer <strong style="color:var(--blue);">cannot be replicated by agent runtimes</strong> — they control their own behavior, which is self-regulation, not enforcement. It <strong style="color:var(--blue);">cannot be replicated by security tools</strong> — they enforce access policies, not business correctness. And it <strong style="color:var(--blue);">cannot be built internally without rebuilding it for every agent, every framework, and every system</strong>.</div>
          <div style="font-size:13px;color:var(--blue);font-weight:600;line-height:1.7;">Surfit holds the execution credentials. The agent doesn't. Nothing reaches production systems without passing through this layer.</div>
          <div style="display:flex;gap:16px;margin-top:14px;padding-top:14px;border-top:1px solid rgba(38,192,255,0.15);flex-wrap:wrap;">
            <span style="font-size:11px;color:var(--muted);">→ Framework-agnostic</span>
            <span style="font-size:11px;color:var(--muted);">→ Vendor-neutral</span>
            <span style="font-size:11px;color:var(--muted);">→ Architecturally independent</span>
            <span style="font-size:11px;color:var(--muted);">→ Hash-chained audit trail</span>
          </div>
        </div>
      </div>

      <!-- ARROW -->
      <div style="display:flex;align-items:center;padding-left:22px;margin-bottom:16px;">
        <div style="width:2px;height:32px;background:var(--green);opacity:0.4;margin-left:0;"></div>
        <div style="color:var(--green);font-size:13px;margin-left:16px;opacity:0.6;">Approved action executes ↓</div>
      </div>

      <!-- DESTINATION: BUSINESS SYSTEMS (not a layer — de-emphasized) -->
      <div style="display:grid;grid-template-columns:44px 1fr;gap:16px;align-items:start;margin-bottom:28px;">
        <div style="width:44px;height:44px;border-radius:50%;background:rgba(34,197,94,0.15);display:flex;align-items:center;justify-content:center;margin-top:12px;">
          <span style="color:var(--green);font-size:16px;">✓</span>
        </div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:8px;padding:14px 20px;opacity:0.7;">
          <div style="font-size:11px;color:var(--green);font-weight:600;margin-bottom:4px;">DESTINATION — Where approved actions execute</div>
          <div style="font-size:12px;color:var(--muted);">Slack · GitHub · Notion · Gmail · Outlook · AWS · CRMs · ERPs · Any API-based system</div>
        </div>
      </div>

      <!-- DIVIDER -->
      <div style="border-top:1px dashed var(--border);margin:20px 0;opacity:0.5;"></div>

      <!-- SEPARATE CONCERN: INFRASTRUCTURE / SECURITY -->
      <div style="display:grid;grid-template-columns:44px 1fr;gap:16px;align-items:start;">
        <div style="width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;margin-top:14px;">
          <span style="color:var(--muted);font-size:14px;">◆</span>
        </div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:8px;padding:18px 24px;">
          <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;font-weight:600;">Separate Concern — Infrastructure Layer</div>
          <div style="display:flex;align-items:start;justify-content:space-between;flex-wrap:wrap;gap:12px;">
            <div>
              <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px;">Security &amp; Endpoint Platforms</div>
              <div style="font-size:12px;color:var(--muted);">CrowdStrike · Palo Alto · Okta · Endpoint protection · Identity management</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:12px;color:var(--muted);font-weight:600;">Decides what is allowed</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Network, process, identity, access control</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;font-style:italic;">Does not evaluate business context or correctness</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div style="display:flex;justify-content:center;gap:32px;margin-top:24px;">
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

'''
    
    content = content[:start_idx] + new_section + content[end_idx:]
    changes += 1
    print("✅ 'Where Surfit Fits' section completely redesigned")
else:
    print("⚠️  Could not find Where Surfit Fits section boundaries")


# ═══════════════════════════════════════════════════════════
# 2. FIX FAQ NESTING — Move CrowdStrike + OpenClaw FAQs to proper level
# ═══════════════════════════════════════════════════════════

# The issue is these were inserted INSIDE another FAQ card.
# We need to find them and make sure they're at the same level as siblings.

# Find the nested ones and check if they're inside a parent runtime-card
# The fix: find the CrowdStrike FAQ block and ensure it's at the right level.
# Let's look for the pattern that shows nesting:

nested_faq = '''
      <div class="runtime-card">
        <h4>How is Surfit different from security tools like CrowdStrike?</h4>
        <p>Security platforms decide what is <strong>allowed</strong> — they enforce access policies, protect endpoints, and block threats at the infrastructure layer. Surfit decides what <strong>should happen</strong> — it evaluates agent actions in business context and routes decisions to the right teams. Security says "this process can run." Surfit says "this action is correct for the business." Different layer, different purpose. They work together, not in competition.</p>
      </div>

      <div class="runtime-card">
        <h4>How is Surfit different from agent runtime governance (like OpenClaw)?</h4>
        <p>Agent runtimes decide what to <strong>do</strong> — they plan, reason, and select tools. Some runtimes add internal governance features like approvals or sandboxing. But when governance lives inside the agent runtime, it's controlled by the same system it's supposed to constrain. Surfit sits outside the agent entirely — at the execution boundary. It's framework-agnostic, vendor-neutral, and architecturally independent. The agent can't override Surfit because Surfit holds the execution credentials, not the agent.</p>
      </div>'''

# Count occurrences — if it appears we need to check context
count = content.count("How is Surfit different from security tools like CrowdStrike?")
print(f"ℹ️  CrowdStrike FAQ appears {count} time(s)")

# If the nesting issue is that these are inside another runtime-card's closing tag,
# we need to find the parent pattern. Let's check what comes right before our FAQ entries.
if nested_faq in content:
    idx = content.index(nested_faq)
    # Check the 200 chars before to see if we're nested
    before = content[max(0,idx-200):idx]
    print(f"ℹ️  Context before CrowdStrike FAQ:\n{before[-100:]}")
    
    # If the FAQs are nested inside the "What happens when a policy violation occurs?" card,
    # we need to move them out. The fix: find the parent </div> that should close before these
    # and add it, then let these be siblings.
    
    # Look for the pattern: the violation FAQ answer followed by our new FAQs
    # The issue is likely missing </div> before the new FAQs
    violation_answer = "Surfit denies the action and records a tamper-evident governance artifact explaining the rejection reason.</p>"
    if violation_answer in content:
        violation_idx = content.index(violation_answer) + len(violation_answer)
        # Check if there's a </div> closing the runtime-card before our new FAQs
        between = content[violation_idx:idx]
        print(f"ℹ️  Between violation answer and CrowdStrike FAQ:\n'{between.strip()}'")
        
        # If there's no </div> closing the parent card, add one
        if '</div>' not in between.strip():
            content = content[:violation_idx] + '\n      </div>' + content[violation_idx:]
            changes += 1
            print("✅ Fixed FAQ nesting — added missing </div> before CrowdStrike FAQ")
        elif between.strip() == '</div>':
            print("ℹ️  FAQ nesting looks correct already")
        else:
            # The </div> might be there but in wrong position
            print("ℹ️  FAQ structure needs manual check")
else:
    print("⚠️  Could not find CrowdStrike FAQ block")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("Now: git add index.html && git commit -m 'redesigned positioning diagram + FAQ fix' && git push")
