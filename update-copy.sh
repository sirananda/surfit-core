#!/bin/bash
# Surfit V2.7 — Copy-only updates to index.html
# Run from ~/Desktop/files/
# This script updates ONLY text content, not design/layout/CSS

FILE="index.html"
cp "$FILE" "${FILE}.backup"

# ── 1. Update page title and meta ──
sed -i '' 's|Surfit.AI — The Decision Layer for Agent Actions|Surfit.AI — Control Layer for Agent Actions|' "$FILE"
sed -i '' 's|Surfit decides how agent actions are handled across your systems — before they execute. One decision layer for Slack, Notion, GitHub, and every system your agents touch.|Agents can act. Surfit makes sure those actions are correct, controlled, and aligned with your business. Control and route AI actions across Slack, GitHub, X, and more.|' "$FILE"

# ── 2. Update hero tagline ──
sed -i '' 's|Surfit decides how agent actions happen across your systems.|Agents can act. Surfit makes sure those actions are correct.|' "$FILE"

# ── 3. Update hero substrate ──
sed -i '' 's|One decision layer for every agent action.|Control and route AI actions across Slack, GitHub, X, and more — based on your business rules.|' "$FILE"

# ── 4. Update hero description paragraphs ──
sed -i '' 's|Agents take actions across tools like Slack, Notion, and GitHub. Surfit applies decision logic to all of them — automatically executing, checking, or gating based on risk.|Low-risk actions run automatically. High-risk actions are checked or escalated. Every action is recorded with a full execution log.|' "$FILE"
sed -i '' 's|Surfit is the decision layer for agent actions. Independent of any single model provider or agent framework.|Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.|' "$FILE"

# ── 5. Update thesis section - "The Problem" ──
sed -i '' 's|As agents move from text to actions,|Agents don'\''t just think — they act.|' "$FILE"
sed -i '' 's| decisions about those actions need to happen before execution.| The missing layer is correctness.|' "$FILE"

sed -i '' 's|Three risks emerge when agents act across systems:|AI agents now post messages, publish content, modify systems, and trigger workflows with real business impact.|' "$FILE"
sed -i '' 's|<br>1) Actions execute without consistent rules||' "$FILE"
sed -i '' 's|<br>2) No single layer decides how actions are handled||' "$FILE"
sed -i '' 's|<br>3) No verifiable record of what happened and why||' "$FILE"
sed -i '' 's|Surfit introduces Waves — bounded execution missions that define both the risk level of an action and how it should be handled. Every action is evaluated, decided, and receipted.|Most systems ensure agents run. Nothing ensures they act correctly for your business. Technically safe doesn'\''t mean correct — an agent can take valid actions with bad business impact. Surfit evaluates every action before execution.|' "$FILE"

# ── 6. Update thesis points ──
sed -i '' 's|Action-Level Decision Logic|Policy-Driven Execution|' "$FILE"
sed -i '' 's|Every action is evaluated before it executes. Surfit determines whether it runs automatically, gets checked, or requires approval — based on your rules.|Every action is classified by risk and handled according to your business rules. Low-risk actions execute automatically. High-risk actions are checked or escalated.|' "$FILE"

sed -i '' 's|Cross-System Consistency|Cross-System Control|' "$FILE"
sed -i '' 's|The same decision layer applies across Slack, Notion, GitHub, and every other system your agents touch. One set of rules, enforced everywhere.|The same control layer applies across Slack, GitHub, X, and every system your agents touch. One set of rules, enforced everywhere.|' "$FILE"

# ── 7. Update "How Surfit Works" section ──
sed -i '' 's|Your agent decides what to do. Surfit decides how it happens.|Your agents propose actions. Surfit ensures they are correct.|' "$FILE"
sed -i '' 's|Surfit sits between your agents and enterprise systems. Every action is evaluated and handled based on its risk — automatically, or with the right level of oversight.|Surfit sits between your agents and your systems. Every action is evaluated against your business rules and handled based on risk — from automatic execution to escalation.|' "$FILE"

# ── 8. Update enterprise systems list ──
sed -i '' 's|Slack, Notion, GitHub, AWS, internal APIs|Slack, GitHub, X, Notion, AWS, internal APIs|' "$FILE"

# ── 9. Update comparison section ──
# Keep as-is, just update Surfit description
sed -i '' 's|Governed Autonomy|Controlled Execution|' "$FILE"

# ── 10. Update flow section ──
sed -i '' 's|Every action flows through a Wave.|Every action flows through the Wave system.|' "$FILE"
sed -i '' 's|A Wave defines both the risk level of an action and how it should be handled — from autonomous execution to critical approval gates.|Actions are classified into Waves 1-5 based on risk. Low waves execute automatically. High waves are checked or escalated. Every action produces a verifiable execution receipt.|' "$FILE"

# ── 11. Update CTA section ──
sed -i '' 's|Surfit is the decision layer<br>for agent actions.|Decide what gets executed —<br>before it happens.|' "$FILE"
sed -i '' 's|Every action evaluated. Every decision explained. Every outcome receipted — across every system your agents touch.|Surfit is the control layer for agent actions. Every action evaluated, every decision explained, every outcome recorded — across every system your agents touch.|' "$FILE"

# ── 12. Update hero badge ──
sed -i '' 's|Works with OpenClaw and proprietary internal agents|Control layer for AI agent actions|' "$FILE"

# ── 13. Update bottom tagline ──
sed -i '' 's|Works with OpenClaw and proprietary internal agents .*.Governed by Surfit|Live with Slack, GitHub, and X · Governed by Surfit|' "$FILE"

# ── 14. Change subsection heading font to Outfit (cleaner, more modern) ──
# Add Outfit font import
sed -i '' 's|family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300|family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300\&family=Outfit:wght@400;500;600;700;800|' "$FILE"

# Override the display font for section titles
sed -i '' "s|:root { --surfit-display-font: 'Righteous', cursive; }|:root { --surfit-display-font: 'Outfit', sans-serif; }|" "$FILE"

echo "✅ Copy updates applied to $FILE"
echo "   Backup saved as ${FILE}.backup"
echo ""
echo "Review changes, then deploy:"
echo "  cd ~/Desktop/files && git add index.html && git commit -m 'V2.7 copy update - control layer positioning' && git push"
