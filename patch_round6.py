"""
Round 6: Section reorder + text fixes.
Extracts each section by comment markers, reassembles in new order.
Also applies punchline fix, held actions fix, summary fix.

Run from ~/Desktop/files/: python3 patch_round6.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════
# STEP 1: Define section boundaries by markers
# ═══════════════════════════════════════════════════════════

markers = [
    '<!-- NAV -->',
    '<!-- HERO -->',
    '<!-- WHERE AGENTS FAIL -->',
    '<!-- THESIS -->',
    '<!-- AGENT INTEGRATION FLOW -->',
    '<!-- THE GAP DIAGRAM -->',
    '<!-- COMPARISON TABLE -->',
    '<!-- WHO NEEDS SURFIT -->',
    '<!-- PLATFORM CAPABILITIES -->',
    '<!-- TECHNICAL FAQ -->',
    '<!-- VISUALIZATION VIDEO -->',
    '<!-- PRODUCT DEMO -->',
    '<!-- DOMINANCE / OBJECTION KILLER -->',
    '<!-- CTA -->',
    '<!-- TECHNICAL DISCUSSION CTA -->',
    '<!-- FOOTER -->',
]

# Verify all markers exist
for m in markers:
    if m not in content:
        print(f"❌ Marker not found: {m}")
        print("NO CHANGES MADE.")
        exit(1)

print("✅ All section markers found")

# Extract everything before NAV (head/styles)
head = content[:content.index('<!-- NAV -->')]

# Extract each section (from its marker to the next marker)
sections = {}
for i, marker in enumerate(markers):
    start = content.index(marker)
    if i + 1 < len(markers):
        end = content.index(markers[i + 1])
    else:
        # FOOTER goes to end
        end = len(content)
    sections[marker] = content[start:end]

print("✅ All sections extracted")

# ═══════════════════════════════════════════════════════════
# STEP 2: Apply text fixes to individual sections
# ═══════════════════════════════════════════════════════════

changes = 0

# Fix 1: Punchline in THE GAP
gap = sections['<!-- THE GAP DIAGRAM -->']
old = 'Guardrails AI and CTGT validated the output. IronClaw and NemoClaw controlled the access. But the agent held the credentials — and no one evaluated whether the action was correct for the business.'
new = 'Guardrails AI and CTGT never saw the action — they only check the model\'s words, not what the agent does with them. IronClaw granted access because the agent needed it — but access control ends at the door. Once the agent was inside with live credentials, it merged directly to production. No layer evaluated whether it should. No one was in the path.'
if old in gap:
    gap = gap.replace(old, new)
    changes += 1
    print("✅ Fix 1: Punchline rewritten")

# Fix 2: Remove routing mentions from held actions
old = '<div style="font-size:10px;color:var(--muted);line-height:1.5;">PR merge to main → ⏸<br><span style="font-size:9px;">Financial system implications detected</span><br><br>Post to company X → ⏸<br><span style="font-size:9px;">External-facing, unapproved content</span></div>'
new = '<div style="font-size:10px;color:var(--muted);line-height:1.5;">PR merge to main → ⏸<br><span style="font-size:9px;">Production system. Financial implications.</span><br><br>Post to company X → ⏸<br><span style="font-size:9px;">External-facing. Unapproved content.</span></div>'
if old in gap:
    gap = gap.replace(old, new)
    changes += 1
    print("✅ Fix 2: Held actions — removed routing language")

# Fix 3: Summary line
old = 'The agent never held the credentials. Surfit evaluated every action in business context. Most executed instantly. The dangerous ones were caught.'
new = 'The agent never held the credentials. Surfit evaluated every action in business context.<br><br>Routine actions flowed instantly across five systems. Pre-defined high-risk actions were caught. The business stayed protected.'
if old in gap:
    gap = gap.replace(old, new)
    changes += 1
    print("✅ Fix 3: Summary line — added business outcome")

# Fix 4: Held actions summary inside the box
old = '2 actions held. Right teams notified.'
new = '2 actions held. Business protected.'
if old in gap:
    gap = gap.replace(old, new)
    changes += 1
    print("✅ Fix 4: Held box summary — removed teams notified")

sections['<!-- THE GAP DIAGRAM -->'] = gap

# ═══════════════════════════════════════════════════════════
# STEP 3: Reassemble in new order
# ═══════════════════════════════════════════════════════════

new_order = [
    '<!-- NAV -->',
    '<!-- HERO -->',
    '<!-- THESIS -->',
    '<!-- AGENT INTEGRATION FLOW -->',
    '<!-- THE GAP DIAGRAM -->',
    '<!-- COMPARISON TABLE -->',
    '<!-- WHO NEEDS SURFIT -->',
    '<!-- PLATFORM CAPABILITIES -->',
    '<!-- WHERE AGENTS FAIL -->',      # moved down
    '<!-- PRODUCT DEMO -->',
    '<!-- DOMINANCE / OBJECTION KILLER -->',
    '<!-- TECHNICAL FAQ -->',
    '<!-- CTA -->',
    '<!-- TECHNICAL DISCUSSION CTA -->',
    '<!-- FOOTER -->',
]

# VISUALIZATION VIDEO is removed (link still exists in demo)
# Verify we're not losing any section
removed = ['<!-- VISUALIZATION VIDEO -->']
for m in markers:
    if m not in new_order and m not in removed:
        print(f"❌ Section {m} is missing from new order and not intentionally removed")
        print("NO CHANGES MADE.")
        exit(1)

reassembled = head
for marker in new_order:
    reassembled += sections[marker]

print(f"✅ Sections reassembled in new order ({len(new_order)} sections)")
print(f"   Removed: {removed}")

# ═══════════════════════════════════════════════════════════
# STEP 4: Verify integrity
# ═══════════════════════════════════════════════════════════

# Check that key content exists in reassembled
checks = [
    ('Hero', 'Agents can act'),
    ('Thesis', 'The missing layer is correctness'),
    ('Agent Integration', 'How agents connect through Surfit'),
    ('The Gap', 'The agent has credentials'),
    ('Landscape', 'Every tool solves a different problem'),
    ('Who Needs', 'Who Needs Surfit'),
    ('Platform', 'What Surfit does today'),
    ('Where Agents Fail', 'Where agents fail'),
    ('Demo', 'See Surfit in Action'),
    ('Dominance', 'dedicated layer'),
    ('FAQ', 'Technical FAQ'),
    ('CTA', 'Decide what gets executed'),
    ('Footer', 'SURFIT'),
]

all_good = True
for label, text in checks:
    if text not in reassembled:
        print(f"❌ Integrity check failed: {label} — '{text}' not found")
        all_good = False

if not all_good:
    print("❌ Integrity checks failed. NO CHANGES MADE.")
    exit(1)

print("✅ All integrity checks passed")

# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(reassembled)

print(f"\n✅ Done — sections reordered + {changes} text fixes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'round 6: section reorder, punchline fix, held actions fix, visualization removed' && git push")
