#!/usr/bin/env python3
"""
Surfit Website V2.7 — Complete copy + layout update script.
Run from ~/Desktop/files/
Makes all changes in one pass to index.html
"""
import re, shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".fullbackup")

with open(FILE, "r") as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════
# 1. FIX FONTS — Remove broken overrides, add clean one
# ═══════════════════════════════════════════════════════════

# Remove the broken extra style blocks that were added by previous scripts
html = html.replace("""<style>
.section-title, .thesis-statement, .brand-heading {
  font-family: "Outfit", sans-serif !important;
  font-weight: 700 !important;
}
</style>
</head>""", "</head>")

# Fix the font override block — keep Righteous for wordmark, Outfit for headings
html = html.replace(
    """<style id="surfit-display-font-override">
:root { --surfit-display-font: 'Righteous', cursive; }
.section-title,
.thesis-statement,
.brand-heading {
  font-family: var(--surfit-display-font, 'Righteous', cursive) !important;
}
</style>""",
    """<style id="surfit-display-font-override">
:root { --surfit-display-font: 'Righteous', cursive; }
/* Wordmark uses Righteous via --surfit-display-font */
/* Section headings use Outfit for cleaner readability */
.section-title,
.thesis-statement,
.brand-heading {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em !important;
}
/* Keep wordmark explicitly on Righteous */
.hero-wordmark,
.nav-wordmark,
.arch-card-num {
  font-family: 'Righteous', cursive !important;
}
</style>"""
)

# Remove all inline font-family:'Righteous' overrides on section-titles/brand-headings
# These were fighting the stylesheet
html = html.replace("font-family:'Righteous',cursive !important;", "")

# ═══════════════════════════════════════════════════════════
# 2. HERO — Badge, systems list, spacing, OpenClaw
# ═══════════════════════════════════════════════════════════

# Badge text
html = html.replace(
    "Control layer for AI agent actions",
    "Works with OpenClaw and proprietary internal agents"
)

# Systems line — make it wider and on one line
html = html.replace(
    '<p class="hero-substrate">Control and route AI actions across Slack, GitHub, X, Notion, AWS, internal APIs, and more — based on your business rules.</p>',
    '<p class="hero-substrate" style="max-width:900px;">Control and route AI actions across Slack, GitHub, X, Notion, AWS, internal APIs, and more — based on your business rules.</p>'
)

# Add more spacing before the "Surfit is the control layer" line
html = html.replace(
    '<p class="hero-saw-def">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>',
    '<p class="hero-saw-def" style="margin-top:16px;">Surfit is the control layer for agent actions. Independent of any single model provider or agent framework.</p>'
)

# ═══════════════════════════════════════════════════════════
# 3. ADD AGENT FLOW DIAGRAM — OpenClaw → NemoClaw → Surfit → Systems
#    Insert before the "How Surfit Works" section
# ═══════════════════════════════════════════════════════════

agent_diagram = """
<!-- AGENT INTEGRATION FLOW -->
<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div style="text-align:center;margin-bottom:40px;">
      <div class="section-label">Agent Integration</div>
      <div class="section-title brand-heading">How agents connect through Surfit.</div>
      <p style="font-size:15px;font-weight:300;color:var(--muted);line-height:1.8;max-width:600px;margin:12px auto 0;">Any agent framework connects to Surfit. Surfit evaluates and controls execution across all downstream systems.</p>
    </div>
    <div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;max-width:1000px;margin:0 auto;">
      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Framework</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">OpenClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--orange);margin-bottom:4px;">Orchestrator</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">NemoClaw</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px;text-align:center;min-width:130px;">
          <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Internal</div>
          <div style="font-size:14px;font-weight:500;color:var(--text);">Custom Agents</div>
        </div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 20px;">→</div>
      <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:12px;padding:24px 32px;text-align:center;min-width:180px;">
        <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue);margin-bottom:6px;">Control Layer</div>
        <div style="font-family:'Righteous',cursive;font-size:22px;color:var(--text);margin-bottom:6px;"><span style="color:var(--blue);">Surfit</span><span style="color:var(--muted);font-size:14px;">.</span><span style="color:var(--orange);">AI</span></div>
        <div style="font-size:11px;color:var(--muted);">Wave evaluation · Policy enforcement · Execution control</div>
      </div>
      <div style="color:var(--border);font-size:24px;padding:0 20px;">→</div>
      <div style="display:flex;flex-direction:column;gap:8px;align-items:center;">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">Slack</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">GitHub</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">X</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">Notion</div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:110px;">
          <div style="font-size:13px;font-weight:500;color:var(--text);">AWS</div>
        </div>
      </div>
    </div>
  </div>
</section>

"""

# Insert before "How Surfit Works" section
html = html.replace(
    '<!-- RUNTIME MODEL -->',
    agent_diagram + '<!-- RUNTIME MODEL -->'
)

# ═══════════════════════════════════════════════════════════
# 4. PLATFORM PROGRESS — 2 columns, strategic In Progress goals
# ═══════════════════════════════════════════════════════════

old_progress = """<!-- PLATFORM PROGRESS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div class="section-label">Platform Progress</div>
    <div class="section-title brand-heading" style="">Current capabilities and roadmap focus.</div>

    <div class="progress-grid">
      <div class="runtime-card">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:10px;">Live Capabilities</div>
        <p>• Wave runtime enforcement<br>• Token-scoped execution control<br>• Policy manifest verification<br>• Tamper-evident governance artifacts<br>• Tenant isolation<br>• Ocean proxy deployment mode<br>• Adapter SDK for external agent frameworks<br>• Cross-agent execution governance<br>• Policy escalation for sensitive operations<br>• Execution path governance</p>
      </div>
      <div class="runtime-card">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--orange);margin-bottom:10px;">In Progress (Near Term)</div>
        <p>• Approval-policy variants<br>• Role-based approver constraints<br>• Expiry-aware approval artifacts<br>• Dual-approval support<br>• Policy grammar standardization<br>• Additional enterprise connectors</p>
      </div>
      <div class="runtime-card">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin-bottom:10px;">Longer Term</div>
        <p>• Multi-region governance infrastructure<br>• Advanced policy simulation tooling<br>• Governance analytics layer<br>• Deeper enterprise system integrations</p>
      </div>
    </div>
  </div>
</section>"""

new_progress = """<!-- PLATFORM PROGRESS -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div class="section-label">Platform Progress</div>
    <div class="section-title brand-heading" style="">Current capabilities and roadmap focus.</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:26px;">
      <div class="runtime-card" style="border-color:rgba(38,192,255,0.25);">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);margin-bottom:14px;">✓ Live</div>
        <p>• Wave runtime enforcement across Slack, GitHub, X<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live polling<br>• SQLite-backed persistence across restarts<br>• Tamper-evident execution receipts<br>• Approval DM notifications via Slack<br>• Adapter SDK for external agent frameworks</p>
      </div>
      <div class="runtime-card" style="border-color:rgba(255,115,30,0.25);">
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--orange);margin-bottom:14px;">◐ In Progress</div>
        <p>• <strong style="color:var(--text);">Predictive Risk Scoring</strong> — ML-augmented wave classification that learns from approval patterns to auto-calibrate risk thresholds per organization<br><br>• <strong style="color:var(--text);">Cross-System Policy Chaining</strong> — Actions in one system trigger policy evaluation in dependent systems (e.g., GitHub merge → Slack announcement → Notion update, all governed as one chain)<br><br>• <strong style="color:var(--text);">Real-Time Policy Simulation</strong> — Test policy changes against historical action data before deploying, with impact analysis showing which past actions would have been reclassified<br><br>• <strong style="color:var(--text);">Autonomous Escalation Routing</strong> — Dynamic approver selection based on action context, organizational hierarchy, and availability — not static hardcoded approvers<br><br>• <strong style="color:var(--text);">Execution Replay & Forensics</strong> — Full action replay with counterfactual analysis: "What would have happened under different policies?"</p>
      </div>
    </div>
  </div>
</section>"""

html = html.replace(old_progress, new_progress)

# ═══════════════════════════════════════════════════════════
# 5. Fix bottom tagline
# ═══════════════════════════════════════════════════════════
html = html.replace(
    "Control layer for AI agent actions &nbsp;·&nbsp; Governed by Surfit",
    "Works with OpenClaw and proprietary internal agents &nbsp;·&nbsp; Governed by Surfit"
)

# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(FILE, "w") as f:
    f.write(html)

print("✅ All changes applied to index.html")
print("   Backup: index.html.fullbackup")
print()
print("Deploy:")
print("  git add index.html && git commit -m 'V2.7 complete update' && git push")
