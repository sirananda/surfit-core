"""
Site updates - all exact string replacements.
1. Move Ripple to Live, add new Live capabilities
2. IronClaw → IronCurtain (3 instances)
3. Add Gmail + Outlook to systems table
4. Demo intro text update
5. New FAQ entries
6. Update What is Surfit FAQ
7. CTA update with @SurfitAI

Run from ~/Desktop/files/: python3 patch_site_updates.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

def safe_replace(label, old, new):
    global content, changes
    count = content.count(old)
    if count == 0:
        print(f"⚠️  {label} — not found, skipping")
        return
    content = content.replace(old, new)
    changes += 1
    print(f"✅ {label} ({count} instance{'s' if count > 1 else ''})")


# ═══════════════════════════════════════════════════════════
# 1. PLATFORM CAPABILITIES — Move Ripple to Live, add new items
# ═══════════════════════════════════════════════════════════

# Remove Ripple from In Progress
safe_replace("1a. Remove Ripple from In Progress",
    '<div style="margin-bottom:0;">• <strong style="color:var(--text);">Ripple Workflows</strong><br><span style="color:var(--muted);">When a pre-defined action completes in one system, Surfit initiates the next action in the next system. One agent action cascades across systems under defined conditions, each step evaluated and executed by Surfit</span></div>',
    '')

# Add new items to Live section (append before closing </p>)
safe_replace("1b. Add new Live capabilities",
    '• Product demo and architecture visualization live on website</p>',
    '''• Product demo and architecture visualization live on website<br>• Ripple Workflows — when an action completes in one system, Surfit triggers the next action in another. Each step evaluated through Wave classification. Workflow builder in dashboard<br>• Agent Intelligence — per-agent trust scoring (approval rate, longevity, volume), budget gates (hourly/daily limits), session tracking (24h activity, systems touched, rate)<br>• Cross-system threat detection — preset correlation rules running continuously, incident logging when patterns fire, incident flags surfaced on pending action cards<br>• Wave Metrics dashboard — ocean-themed operational metrics (Length, Height, Depth, Frequency, Drift, Splash)<br>• Natural language policy parser — write policies in plain English, Surfit converts to enforceable rules<br>• Anomaly detection — burst activity, unusual hours, cross-system spread, high rejection rate<br>• Kill switch and shadow mode — global execution halt and per-tenant evaluate-only mode<br>• TOTP 2FA on admin write endpoints<br>• Compliance report generator — exportable audit report with actions, receipts, credential access, agent trust</p>''')


# ═══════════════════════════════════════════════════════════
# 2. IRONCLAW → IRONCURTAIN (3 instances)
# ═══════════════════════════════════════════════════════════

safe_replace("2a. IronClaw in PR example",
    'IronClaw → permissions are safe ✓',
    'IronCurtain → permissions are safe ✓')

safe_replace("2b. IronClaw in Gap diagram",
    'IronClaw · NemoClaw',
    'IronCurtain · NemoClaw')

safe_replace("2c. IronClaw in Landscape",
    'IronClaw · NemoClaw · OpenShell',
    'IronCurtain · NemoClaw · OpenShell')


# ═══════════════════════════════════════════════════════════
# 3. ADD GMAIL + OUTLOOK to systems table
# ═══════════════════════════════════════════════════════════

safe_replace("3. Add Gmail + Outlook to systems table",
    '''        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">GitHub</span><span style="font-size:10px;color:#f97316;font-weight:600;width:36px;text-align:center;">4</span><span style="font-size:10px;color:#f97316;width:80px;text-align:right;">Approval</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;width:36px;text-align:center;">5</span><span style="font-size:10px;color:#ef4444;width:80px;text-align:right;">Approval</span>
        </div>''',
    '''        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Gmail</span><span style="font-size:10px;color:#38bdf8;font-weight:600;width:36px;text-align:center;">2</span><span style="font-size:10px;color:#38bdf8;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">Outlook</span><span style="font-size:10px;color:#38bdf8;font-weight:600;width:36px;text-align:center;">2</span><span style="font-size:10px;color:#38bdf8;width:80px;text-align:right;">Automatic</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">GitHub</span><span style="font-size:10px;color:#f97316;font-weight:600;width:36px;text-align:center;">4</span><span style="font-size:10px;color:#f97316;width:80px;text-align:right;">Approval</span>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 14px;display:flex;align-items:center;width:100%;">
          <span style="font-size:13px;font-weight:500;color:var(--text);flex:1;">AWS</span><span style="font-size:10px;color:#ef4444;font-weight:600;width:36px;text-align:center;">5</span><span style="font-size:10px;color:#ef4444;width:80px;text-align:right;">Approval</span>
        </div>''')


# ═══════════════════════════════════════════════════════════
# 4. DEMO INTRO TEXT
# ═══════════════════════════════════════════════════════════

safe_replace("4. Demo intro text",
    'Surfit evaluates and controls every agent action across your systems — before it executes.<br>Lower-risk actions flow automatically. Higher-risk actions are held for context.<br>Every decision is logged, traceable, and enforced in real time.',
    'Demo 1: How Surfit Works — core product walkthrough.<br>Demo 2: Agent Intelligence &amp; Threat Detection — advanced capabilities.<br>Every decision is logged, traceable, and enforced in real time.')


# ═══════════════════════════════════════════════════════════
# 5. NEW FAQ ENTRIES (add after OpenClaw FAQ)
# ═══════════════════════════════════════════════════════════

safe_replace("5. New FAQ entries",
    'The agent can\'t override Surfit because Surfit holds the execution credentials, not the agent.</p></div>\n      <div class="faq-item"><h4>Does Surfit slow down agents?</h4>',
    '''The agent can\'t override Surfit because Surfit holds the execution credentials, not the agent.</p></div>
      <div class="faq-item"><h4>What are Ripple Workflows?</h4><p>When an action completes in one system, Surfit can automatically trigger the next action in another system. Each step in the chain is evaluated through Wave classification. If any step hits Wave 4 or 5, the flow pauses for review. You define the workflows, Surfit governs every step.</p></div>
      <div class="faq-item"><h4>What is Agent Intelligence?</h4><p>Surfit tracks every agent individually with trust scores, budget gates, and session monitoring. Trust scores adapt based on approval history — agents that behave well earn lower wave modifiers, agents that get rejected face higher scrutiny. Budget gates enforce hourly and daily action limits. If an agent exceeds its budget, Surfit blocks all actions until the next window.</p></div>
      <div class="faq-item"><h4>What is cross-system threat detection?</h4><p>Surfit runs correlation rules across all connected systems continuously. When an agent\'s actions match a suspicious pattern — like a code change followed by an IAM modification, or sensitive data access followed by external communication — Surfit escalates the actions regardless of their individual wave scores. The pattern overrides the label.</p></div>
      <div class="faq-item"><h4>Does Surfit slow down agents?</h4>''')


# ═══════════════════════════════════════════════════════════
# 6. UPDATE "What is Surfit?" FAQ
# ═══════════════════════════════════════════════════════════

safe_replace("6. What is Surfit FAQ — add new capabilities",
    'the agent cannot bypass what it cannot reach.</p></div>',
    'the agent cannot bypass what it cannot reach. Surfit also provides per-agent trust scoring, cross-system threat detection, and Ripple Workflows for governed multi-system automation.</p></div>')


# ═══════════════════════════════════════════════════════════
# 7. CTA — add @SurfitAI reference
# ═══════════════════════════════════════════════════════════

safe_replace("7. CTA — add @SurfitAI",
    'Start with one system. Route your agent\'s actions through Surfit. See what flows instantly, what gets held for context, and what gets receipted. Every system you connect makes the next one stronger.',
    'Start with one system. Route your agent\'s actions through Surfit. See what flows instantly, what gets held for context, and what gets receipted. Every system you connect makes the next one stronger.<br><br>Surfit is customer zero — a live AI agent posts to <a href="https://x.com/SurfitAI" target="_blank" style="color:var(--blue);">@SurfitAI</a> through Surfit every day.')


# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'site updates: new capabilities live, IronCurtain, Gmail/Outlook, demos, FAQs, X link' && git push")
