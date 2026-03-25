"""
Surfit Site Patch — V3.1 Alignment
Updates: Platform Capabilities, Platform Progress, new dominance section, architecture accuracy.
Run from ~/Desktop/files/: python3 patch_site_v31.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ═══════════════════════════════════════════════════════════
# 1. PLATFORM CAPABILITIES — rewrite to reflect what's built
# ═══════════════════════════════════════════════════════════

old_capabilities = '''    <div class="runtime-grid" style="margin-top:26px;">
      <div class="runtime-card"><h4>Runtime Execution Enforcement</h4><p>AI agent actions pass through deterministic runtime boundaries before interacting with enterprise systems.</p></div>
      <div class="runtime-card"><h4>Policy Manifest Integrity</h4><p>Each Wave execution pins a policy manifest whose SHA256 hash is recorded and verified.</p></div>
      <div class="runtime-card"><h4>Scoped Mutation Tokens</h4><p>Short-lived tokens restrict agent authority to specific actions within defined policy scope.</p></div>
      <div class="runtime-card"><h4>Tool Allowlist Enforcement</h4><p>Agents may only invoke tools explicitly allowed by the policy manifest.</p></div>
      <div class="runtime-card"><h4>Tenant Isolation</h4><p>Surfit enforces tenant-scoped governance boundaries across execution runs and audit records.</p></div>
      <div class="runtime-card"><h4>Tamper-Evident Audit Logs</h4><p>Every decision produces verifiable governance artifacts with integrity checks.</p></div>
      <div class="runtime-card"><h4>Offline Governance Proof Verification</h4><p>Exported Wave bundles can be verified independently without the Surfit runtime.</p></div>
      <div class="runtime-card"><h4>Adapter SDK</h4><p>Neutral integration layer enabling governance enforcement across multiple agent frameworks.</p></div>
      <div class="runtime-card"><h4>Ocean Proxy Deployment Mode</h4><p>Optional proxy enforcement layer that intercepts and validates agent execution requests.</p></div>
    </div>'''

new_capabilities = '''    <div class="runtime-grid" style="margin-top:26px;">
      <div class="runtime-card"><h4>Runtime Execution Enforcement</h4><p>Every agent action is evaluated against business policy before execution. Actions are classified, risk-scored, and routed — automatically or to human approval.</p></div>
      <div class="runtime-card"><h4>Wave Risk Classification</h4><p>Deterministic risk scoring across five levels. Wave 1–3 execute automatically with full logging. Wave 4–5 require operator approval. Risk is computed per action, not per system.</p></div>
      <div class="runtime-card"><h4>Cross-System Governance</h4><p>Single engine evaluates actions across Slack, GitHub, X, Notion, Gmail, Outlook, and AWS. Same classification pattern, same enforcement boundary, every system.</p></div>
      <div class="runtime-card"><h4>Customer Isolation</h4><p>Tenant-scoped data, actions, and pending queues. Each customer sees only their own workspace. Operator admin view spans all customers.</p></div>
      <div class="runtime-card"><h4>Tamper-Evident Audit Logs</h4><p>Every decision produces a hash-chained execution receipt. Event hash linked to previous hash. Full audit trail with integrity verification.</p></div>
      <div class="runtime-card"><h4>Approval Workflow</h4><p>Held actions surface in a pending queue with full context. Operators approve or reject with confirmation. Receipts generated on resolution. Slack DM notifications on hold.</p></div>
      <div class="runtime-card"><h4>Context-Aware Classification</h4><p>Actions are classified by content, destination, and context — not just type. A Slack message to #eng-platform differs from one to #company-announcements. A PR to dev differs from one to main.</p></div>
      <div class="runtime-card"><h4>Real-Time Dashboard</h4><p>Live-polling operator dashboard with pending queue, activity feed, execution receipts, policy view, and integration status. Client-facing and admin views.</p></div>
      <div class="runtime-card"><h4>Connector Architecture</h4><p>Standardized ingest → classify → evaluate → route pattern. Each system connector handles normalization. New systems follow the same integration pattern.</p></div>
    </div>'''

if old_capabilities in content:
    content = content.replace(old_capabilities, new_capabilities)
    changes += 1
    print("✅ Platform Capabilities rewritten")
else:
    print("⚠️  Platform Capabilities — old block not found")

# ═══════════════════════════════════════════════════════════
# 2. PLATFORM PROGRESS LIVE — update with current state
# ═══════════════════════════════════════════════════════════

old_live = '''<p style="color:var(--text);line-height:2.2;font-size:13px;">• Wave runtime enforcement across Slack, GitHub, X, Notion<br>• Deterministic risk classification (Wave 1–5)<br>• Real-time execution gating with approve/reject/block<br>• Policy manifest verification (SHA256)<br>• Cross-system action evaluation from single engine<br>• Cloud-hosted dashboard with live action polling<br>• Always-on cloud deployment (systemd managed)<br>• SQLite-backed persistence across server restarts<br>• Tamper-evident execution receipts with cryptographic proof<br>• Context-aware content risk scoring (keyword, length, destination)<br>• Deterministic action normalization across heterogeneous APIs<br>• Unified pending queue with cross-system operator control<br>• Product demo and architecture visualization live on website<br>• Adapter SDK for external agent frameworks</p>'''

new_live = '''<p style="color:var(--text);line-height:2.2;font-size:13px;">• Wave runtime enforcement across Slack, GitHub, X, Notion, Gmail, Outlook, AWS<br>• Deterministic risk classification (Wave 1–5) with context-aware scoring<br>• Real-time execution gating with approve/reject/block<br>• Cross-system action evaluation from single governance engine<br>• Cloud-hosted dashboard with live action polling (client + admin views)<br>• Customer isolation — tenant-scoped data, actions, and pending queues<br>• Client-facing dashboard with SSL and authentication (client.surfit.ai)<br>• Internal admin view with cross-customer visibility and pending queue<br>• Always-on cloud deployment (systemd managed, Hetzner)<br>• SQLite-backed persistence across server restarts<br>• Hash-chained execution receipts with integrity verification<br>• Context-aware content risk scoring (keyword, destination, sensitivity)<br>• Role-based approver mapping with per-system access control<br>• Slack DM notifications on held actions<br>• Deterministic action normalization across heterogeneous APIs<br>• Unified pending queue with cross-system operator control<br>• Product demo and architecture visualization live on website</p>'''

if old_live in content:
    content = content.replace(old_live, new_live)
    changes += 1
    print("✅ Platform Progress LIVE updated")
else:
    print("⚠️  Platform Progress LIVE — old block not found")

# ═══════════════════════════════════════════════════════════
# 3. NEW DOMINANCE SECTION — after demo, before CTA
# ═══════════════════════════════════════════════════════════

# Insert after demo section closing tag, before CTA section
old_after_demo = '''</section>

<!-- CTA -->
<section class="cta-section">'''

new_after_demo = '''</section>

<!-- DOMINANCE / OBJECTION KILLER -->
<section style="background:var(--darker);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:980px;">
    <div class="section-label">Why a Dedicated Layer</div>
    <div class="section-title brand-heading" style="">Agent control requires a dedicated layer.</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:32px;">

      <div class="runtime-card" style="border-color:rgba(38,192,255,0.25);">
        <h4 style="color:var(--blue);font-size:14px;margin-bottom:16px;">Why This Requires a Dedicated Layer</h4>
        <div style="color:var(--text);font-size:13px;line-height:2.2;">
          • Agent actions require real-time decisioning across every system they touch<br>
          • Each system has different APIs, actions, and risk profiles — this cannot be unified ad hoc<br>
          • Decisions must happen at runtime, not inside static or prebuilt agent logic<br>
          • Approval routing, logging, and enforcement must be consistent across all systems<br>
          • Control must exist outside the agent to remain neutral and enforceable
        </div>
      </div>

      <div class="runtime-card" style="border-color:rgba(255,115,30,0.25);">
        <h4 style="color:var(--orange);font-size:14px;margin-bottom:16px;">What Happens Without a Dedicated Layer</h4>

        <div style="margin-bottom:16px;">
          <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Pre-built Agent Logic</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Breaks under real-world variability — cannot reliably assess risk across systems<br>
            • Logic becomes fragmented across agents with no consistent control layer
          </div>
        </div>

        <div>
          <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">Internal Builds</div>
          <div style="color:var(--text);font-size:13px;line-height:2;">
            • Requires rebuilding decision infrastructure for every new integration<br>
            • Quickly becomes brittle, inconsistent, and expensive to maintain<br>
            • No unified enforcement — decisions vary across systems and teams
          </div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- CTA -->
<section class="cta-section">'''

if old_after_demo in content:
    content = content.replace(old_after_demo, new_after_demo)
    changes += 1
    print("✅ Dominance section added after demo")
else:
    print("⚠️  Could not find demo→CTA boundary for dominance section")

# ═══════════════════════════════════════════════════════════
# 4. ARCHITECTURE — soften overstatements
# ═══════════════════════════════════════════════════════════

# Fix "Policy Lineage Anchoring" — we have hashes but not canonical SHA256 policy snapshots
old_arch_02 = '''<div class="arch-card-body">Canonical SHA256 policy hash computed at Wave initiation. Policy snapshot is persisted per Wave with lineage traceability. Run status and governance provenance are written to DB.</div>'''
new_arch_02 = '''<div class="arch-card-body">Policy configuration drives Wave assignment at evaluation time. Each action's risk factors, wave score, and decision rationale are persisted with the execution record for lineage traceability.</div>'''

if old_arch_02 in content:
    content = content.replace(old_arch_02, new_arch_02)
    changes += 1
    print("✅ Architecture card 02 softened")

# Fix "Automated Tamper Testing"
old_arch_05 = '''<div class="arch-card-body">CLI tamper simulation with automated pytest validation. Demonstrates integrity failure on mutated rows. DB-backed, cryptographically anchored execution lineage — not UI-level logging.</div>'''
new_arch_05 = '''<div class="arch-card-body">Hash-chained execution receipts with event_hash → prev_hash linkage. Integrity verification detects mutations in the action log. DB-backed execution lineage — not UI-level logging.</div>'''

if old_arch_05 in content:
    content = content.replace(old_arch_05, new_arch_05)
    changes += 1
    print("✅ Architecture card 05 softened")

# Fix capabilities section title to be more grounded
old_cap_title = '''<div class="section-title brand-heading" style="">Core runtime enforcement capabilities currently implemented in Surfit.</div>'''
new_cap_title = '''<div class="section-title brand-heading" style="">What Surfit does today.</div>'''

if old_cap_title in content:
    content = content.replace(old_cap_title, new_cap_title)
    changes += 1
    print("✅ Capabilities section title updated")

# ═══════════════════════════════════════════════════════════
# 5. FAQ — update "What is Surfit" to include all systems
# ═══════════════════════════════════════════════════════════

old_faq = '''<p>Surfit is a control layer for AI agent actions that evaluates every action against your business rules before execution — routing actions across Slack, GitHub, X, and more based on risk.</p>'''
new_faq = '''<p>Surfit is a control layer for AI agents that evaluates every action against your business rules before execution — governing actions across Slack, GitHub, X, Notion, Gmail, Outlook, AWS, and more based on risk.</p>'''

if old_faq in content:
    content = content.replace(old_faq, new_faq)
    changes += 1
    print("✅ FAQ updated with all systems")

# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("Now: git add index.html && git commit -m 'v3.1 site alignment — capabilities, progress, dominance section' && git push")
