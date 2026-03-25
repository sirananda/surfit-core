"""
Surfit Site Cleanup — Remove bloat, fix overstatements, align branding
Keeps "Control Layer" as tagline. "Decision infrastructure" as positioning.
Run from ~/Desktop/files/: python3 patch_cleanup.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. REMOVE "Where Surfit Fits" section entirely
# ═══════════════════════════════════════════════════════════

where_start = '<!-- WHERE SURFIT FITS -->'
where_end = '<!-- CTA -->'

if where_start in content and where_end in content:
    start_idx = content.index(where_start)
    end_idx = content.index(where_end)
    content = content[:start_idx] + '\n' + content[end_idx:]
    changes += 1
    print("✅ Removed 'Where Surfit Fits' section")
else:
    print("⚠️  Could not find 'Where Surfit Fits' section")


# ═══════════════════════════════════════════════════════════
# 2. REMOVE "Operational Signal" section entirely
# ═══════════════════════════════════════════════════════════

# Find the operational signal section
op_signal_marker = 'Operational Signal'
# It's between sections — find the section containing it
op_start_text = '<!-- OPERATIONAL -->'
if op_start_text not in content:
    # Try to find it by the heading
    op_start_text = 'Every Wave run is measurable.'
    
if op_start_text in content:
    # Find the section start (go back to find <section)
    op_idx = content.index(op_start_text)
    # Walk backward to find the <section tag
    section_start = content.rfind('<section', 0, op_idx)
    # Walk forward to find </section>
    section_end = content.find('</section>', op_idx) + len('</section>')
    if section_start > 0 and section_end > section_start:
        content = content[:section_start] + '\n' + content[section_end:]
        changes += 1
        print("✅ Removed 'Operational Signal' section")
    else:
        print("⚠️  Could not find Operational Signal section boundaries")
else:
    print("⚠️  Could not find Operational Signal section")


# ═══════════════════════════════════════════════════════════
# 3. FIX Architecture card 01 — remove "Graph-based"
# ═══════════════════════════════════════════════════════════

old_arch_01 = '<div class="arch-card-title">Policy-Governed Graph Executor</div>'
new_arch_01 = '<div class="arch-card-title">Policy-Governed Execution Engine</div>'

if old_arch_01 in content:
    content = content.replace(old_arch_01, new_arch_01)
    changes += 1
    print("✅ Architecture card 01 title fixed")

old_arch_01_body = 'Graph-based Wave execution with policy check before every tool invocation. Each node is evaluated at runtime. The execution structure is governed — the reasoning inside tool nodes is not constrained.'
new_arch_01_body = 'Every agent action passes through policy evaluation before execution. Each action is classified, risk-scored, and routed at runtime. The execution boundary is governed — the agent\'s internal reasoning is not constrained.'

if old_arch_01_body in content:
    content = content.replace(old_arch_01_body, new_arch_01_body)
    changes += 1
    print("✅ Architecture card 01 body fixed")


# ═══════════════════════════════════════════════════════════
# 4. FIX Architecture card 03 — rewrite "Governed LLM Integration"
# ═══════════════════════════════════════════════════════════

old_arch_03_title = '<div class="arch-card-title">Governed LLM Integration</div>'
new_arch_03_title = '<div class="arch-card-title">System-Level Action Control</div>'

if old_arch_03_title in content:
    content = content.replace(old_arch_03_title, new_arch_03_title)
    changes += 1
    print("✅ Architecture card 03 title fixed")

old_arch_03_body = 'LLM treated as a tool node — not a privileged actor. Provider, model, prompt boundary, raw input, sanitized input, and output all logged. Write actions are policy-evaluated, not manually reviewed.'
new_arch_03_body = 'Agent actions are evaluated at the system boundary — not at the model layer. Surfit governs what agents do to external systems, not how they reason internally. Every write action is policy-evaluated and classified by business context before execution.'

if old_arch_03_body in content:
    content = content.replace(old_arch_03_body, new_arch_03_body)
    changes += 1
    print("✅ Architecture card 03 body fixed")

# Also fix the tag from "Intelligence" to something accurate
old_arch_03_tag = '<div class="arch-card-tag tag-blue">Intelligence</div>'
new_arch_03_tag = '<div class="arch-card-tag tag-blue">Control</div>'

if old_arch_03_tag in content:
    content = content.replace(old_arch_03_tag, new_arch_03_tag)
    changes += 1
    print("✅ Architecture card 03 tag fixed")


# ═══════════════════════════════════════════════════════════
# 5. REMOVE Architecture card 07 "Wave Atlas" entirely
# ═══════════════════════════════════════════════════════════

wave_atlas_marker = 'Wave Atlas'
if wave_atlas_marker in content:
    # Find the arch-card containing it
    atlas_idx = content.index(wave_atlas_marker)
    card_start = content.rfind('<div class="arch-card">', 0, atlas_idx)
    card_end = content.find('</div>', atlas_idx)
    # arch-card has nested divs, need to find the right closing
    # Count from card_start
    if card_start > 0:
        # Find the matching closing </div> for the arch-card
        depth = 0
        i = card_start
        while i < len(content):
            if content[i:i+4] == '<div':
                depth += 1
            elif content[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    card_end = i + 6
                    break
            i += 1
        content = content[:card_start] + content[card_end:]
        changes += 1
        print("✅ Removed Architecture card 07 'Wave Atlas'")
    else:
        print("⚠️  Could not find Wave Atlas card boundaries")


# ═══════════════════════════════════════════════════════════
# 6. FIX CISOs card — remove "scoped mutation tokens"
# ═══════════════════════════════════════════════════════════

old_ciso = 'Surfit enforces deterministic boundaries using scoped mutation tokens, policy manifests, and runtime validation before actions are executed.'
new_ciso = 'Surfit enforces deterministic boundaries at the execution layer — every agent action is policy-evaluated, risk-classified, and either auto-executed or held for approval before reaching any system.'

if old_ciso in content:
    content = content.replace(old_ciso, new_ciso)
    changes += 1
    print("✅ CISOs card fixed — removed scoped mutation tokens")


# ═══════════════════════════════════════════════════════════
# 7. REMOVE "scoped mutation tokens" from Architecture description
# ═══════════════════════════════════════════════════════════

old_arch_desc = 'Surfit enforces policy checks before tool invocation, isolates workspace per Wave, anchors policy lineage with hashes, gates mutation paths with wave tokens, and exposes audit verification endpoints.'
new_arch_desc = 'Surfit evaluates every agent action against business policy before execution. Each action is classified by risk, routed to the right team when needed, and recorded with a hash-chained audit trail.'

if old_arch_desc in content:
    content = content.replace(old_arch_desc, new_arch_desc)
    changes += 1
    print("✅ Architecture description simplified")


# ═══════════════════════════════════════════════════════════
# 8. FIX "Why a Dedicated Layer" title — keep "decision layer" 
#    (aligns with positioning without breaking tagline)
# ═══════════════════════════════════════════════════════════

# Already says "dedicated decision layer" — leave it


# ═══════════════════════════════════════════════════════════
# 9. Clean up Enterprise Architecture Teams card
# ═══════════════════════════════════════════════════════════

old_enterprise = 'Surfit provides a neutral governance runtime that sits in the execution path without requiring framework lock-in.'
new_enterprise = 'Surfit provides a neutral decision layer that sits at the execution boundary — evaluating every agent action in business context regardless of which framework produced it.'

if old_enterprise in content:
    content = content.replace(old_enterprise, new_enterprise)
    changes += 1
    print("✅ Enterprise Architecture card updated")


# ═══════════════════════════════════════════════════════════
# 10. Remove "Adapter SDK" reference if still in Live list
# ═══════════════════════════════════════════════════════════

if 'Adapter SDK for external agent frameworks' in content:
    content = content.replace('<br>• Adapter SDK for external agent frameworks', '')
    changes += 1
    print("✅ Removed 'Adapter SDK' from Live list")


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("Now: git add index.html && git commit -m 'site cleanup — remove bloat, fix overstatements, align branding' && git push")
