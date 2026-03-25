"""
Replace Landscape section with expanded competitive positioning.
Names Guardrails AI, CTGT, IronClaw, CrowdStrike, OpenClaw.
Surfit as the dominant final card spanning full width.

Run from ~/Desktop/files/: python3 patch_landscape.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

# The exact old section - from <section to </section> before <!-- METRICS -->
old_start = '<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:80px 48px;">\n  <div class="container">\n    <div style="text-align:center;margin-bottom:48px;">\n      <div class="section-label">Landscape</div>\n      <div class="section-title brand-heading" style="">Where Surfit fits.</div>\n    </div>'

# Find start
if old_start not in content:
    print("❌ Could not find Landscape section start. Aborting. NO CHANGES MADE.")
    exit(1)

start_idx = content.index(old_start)

# Find the </section> that closes this section (before <!-- METRICS -->)
end_marker = '</section>\n\n<!-- METRICS -->'
if end_marker not in content:
    print("❌ Could not find Landscape section end. Aborting. NO CHANGES MADE.")
    exit(1)

end_idx = content.index(end_marker, start_idx) + len('</section>')

old_section = content[start_idx:end_idx]
print(f"Found Landscape section: {len(old_section)} chars, lines ~1005-1063")

new_section = '''<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div style="text-align:center;margin-bottom:48px;">
      <div class="section-label">Landscape</div>
      <div class="section-title brand-heading" style="">Every tool solves a different problem.<br>None of them solve this one.</div>
      <p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;max-width:720px;margin-left:auto;margin-right:auto;">The AI control stack has five layers. Each answers a different question. Only one governs whether an agent's action is correct for your business.</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;max-width:900px;margin:0 auto;">

      <!-- Card 1: Output Validation -->
      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Output Validation</div>
            <div style="font-size:14px;font-weight:600;color:var(--text);">Guardrails AI · NeMo Guardrails</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;">Validates LLM text outputs — checks for toxicity, PII, hallucinations, prompt injection, and schema compliance. A library of validators applied to what the model says.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;">Answers: "Is this output safe?"</div>
        <div style="font-size:11px;color:var(--red);margin-top:6px;">✗ Does not govern what the agent does to real systems</div>
      </div>

      <!-- Card 2: Model Behavior Control -->
      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Model Behavior Control</div>
            <div style="font-size:14px;font-weight:600;color:var(--text);">CTGT · Mentat</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;">Modifies model behavior at the representation level using activation steering. Enforces compliance policies inside the model's inference — deterministic output control without retraining.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;">Answers: "Is this model compliant?"</div>
        <div style="font-size:11px;color:var(--red);margin-top:6px;">✗ Does not sit at the execution boundary of real systems</div>
      </div>

      <!-- Card 3: Sandbox / Environment Security -->
      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Sandbox &amp; Environment Security</div>
            <div style="font-size:14px;font-weight:600;color:var(--text);">IronClaw · NemoClaw · OpenShell</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;">Container-level isolation using Rust-based permissions. Controls network egress and what the agent can access. Environment-level security, not action-level evaluation.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;">Answers: "Can this agent access this resource?"</div>
        <div style="font-size:11px;color:var(--red);margin-top:6px;">✗ Once access is granted, no business-level decision control</div>
      </div>

      <!-- Card 4: Infrastructure Security -->
      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Infrastructure &amp; Endpoint Security</div>
            <div style="font-size:14px;font-weight:600;color:var(--text);">CrowdStrike · Palo Alto · Okta</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;">Protects endpoints, networks, and identity at the infrastructure layer. Enforces access policies and blocks threats. Operates below the application layer entirely.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;">Answers: "Is this process allowed to run?"</div>
        <div style="font-size:11px;color:var(--red);margin-top:6px;">✗ No concept of business context or action correctness</div>
      </div>

      <!-- Card 5: Agent Runtimes -->
      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);grid-column:1/-1;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Agent Runtimes</div>
            <div style="font-size:14px;font-weight:600;color:var(--text);">OpenClaw · LangChain · CrewAI · AutoGen</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;">Frameworks that plan, reason, and select tools. Some add internal governance features — approvals, policies, fail-closed execution. But internal governance is controlled by the same system it's supposed to constrain.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;">Answers: "What should the agent do?"</div>
        <div style="font-size:11px;color:var(--red);margin-top:6px;">✗ Self-regulation is not enforcement — internal controls are optional and framework-bound</div>
      </div>

    </div>

    <!-- SURFIT — dominant, full width, visually separated -->
    <div style="max-width:900px;margin:24px auto 0;">
      <div class="runtime-card" style="border-color:rgba(38,192,255,0.4);border-width:2px;background:rgba(38,192,255,0.04);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--blue);margin-bottom:4px;">Execution Boundary — Decision Infrastructure</div>
            <div style="font-size:18px;font-weight:700;color:var(--blue);">Surfit</div>
          </div>
          <div style="background:var(--blue);color:#000;font-size:9px;font-weight:700;padding:3px 12px;border-radius:10px;letter-spacing:.1em;">DIFFERENT LAYER</div>
        </div>
        <div style="font-size:13px;color:var(--text);line-height:1.7;margin-bottom:14px;">Surfit sits at the execution boundary — between the agent and every system it touches. Every action is intercepted, evaluated in business context, and either auto-executed or routed to the right team for approval. The agent proposes. Surfit decides whether it should happen.</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;">
          <div style="font-size:11px;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Holds credentials — agent cannot bypass</div>
          <div style="font-size:11px;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Cross-system consistency — one decision model everywhere</div>
          <div style="font-size:11px;color:var(--text);padding:8px 12px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Routes decisions to the right team — not generic allow/deny</div>
        </div>
        <div style="font-size:12px;font-weight:600;color:var(--blue);">Answers: "Is this the right action for the business right now — and does the right person know?"</div>
        <div style="font-size:11px;color:var(--muted);margin-top:10px;font-style:italic;">Every tool above solves a real problem. None of them answer this question. Surfit is the only layer that governs agent actions on real systems in business context.</div>
      </div>
    </div>

  </div>
</section>'''

content = content[:start_idx] + new_section + content[end_idx:]

with open(filepath, "w") as f:
    f.write(content)

print("✅ Landscape section replaced successfully")
print("Verify: open surfit.ai and check the Landscape section")
print("If broken, revert: git checkout index.html")
print("If good: git add index.html && git commit -m 'landscape: competitive positioning with named competitors' && git push")
