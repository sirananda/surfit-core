#!/bin/bash
# Surfit V2.7 — Fix script v2
# Fixes: font targeting, hero systems list, box heights, FAQ
FILE="index.html"
cp "$FILE" "${FILE}.backup2"

# ── 1. Fix font: Only section headings get Outfit, NOT the wordmark ──
# The previous script changed --surfit-display-font which affects section-title AND wordmark
# We need to revert the display font variable and instead add Outfit directly to section-title only

# First, revert the display font back to Righteous for the wordmark
sed -i '' "s|:root { --surfit-display-font: 'Outfit', sans-serif; }|:root { --surfit-display-font: 'Righteous', cursive; }|" "$FILE"

# Now add a CSS override that makes section-title use Outfit but leaves wordmark alone
# Insert after the existing style block
sed -i '' 's|.section-title,|.section-title {font-family: "Outfit", sans-serif !important;} .UNUSED_section-title,|' "$FILE"

# Actually let's do this properly - add a new style block before </head>
sed -i '' 's|</head>|<style>\
.section-title, .thesis-statement, .brand-heading {\
  font-family: "Outfit", sans-serif !important;\
  font-weight: 700 !important;\
}\
</style>\
</head>|' "$FILE"

# Undo the broken sed above
sed -i '' 's|.section-title {font-family: "Outfit", sans-serif !important;} .UNUSED_section-title,|.section-title,|' "$FILE"

# ── 2. Fix hero systems list ──
sed -i '' 's|Control and route AI actions across Slack, GitHub, X, and more — based on your business rules.|Control and route AI actions across Slack, GitHub, X, Notion, AWS, internal APIs, and more — based on your business rules.|' "$FILE"

# ── 3. Remove "Low-risk actions run automatically..." line ──
sed -i '' 's|Low-risk actions run automatically. High-risk actions are checked or escalated. Every action is recorded with a full execution log.|Works with OpenClaw and proprietary internal agents.|' "$FILE"

# ── 4. Fix FAQ "What is Surfit" answer ──
sed -i '' 's|Surfit is a governance runtime for AI agents that enforces deterministic policy boundaries between agents and enterprise systems.|Surfit is a control layer for AI agent actions that evaluates every action against your business rules before execution — routing actions across Slack, GitHub, X, and more based on risk.|' "$FILE"

# ── 5. Fix Product Demo subtitle ──
sed -i '' 's|Surfit decides how agent actions are handled across your systems — before they execute.|Surfit controls how agent actions are handled across your systems — before they execute.|' "$FILE"

# ── 6. Make the three "How Surfit Works" boxes even height and highlight Surfit box more ──
# The Surfit box has border: 1px solid rgba(38,192,255,0.25) — make it more prominent
sed -i '' 's|border:1px solid rgba(38,192,255,0.25);border-radius:10px;padding:18px 16px|border:2px solid rgba(38,192,255,0.5);border-radius:10px;padding:18px 16px;background:rgba(38,192,255,0.06)|' "$FILE"

# Make all three boxes same min-height
sed -i '' 's|<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:left;align-items:start;">|<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:left;align-items:stretch;">|' "$FILE"

echo "✅ Fix v2 applied to $FILE"
echo "   Backup saved as ${FILE}.backup2"
echo ""
echo "Deploy:"
echo "  cd ~/Desktop/files && git add index.html && git commit -m 'Fix fonts + hero + box layout' && git push"
