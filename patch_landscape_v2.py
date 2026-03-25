"""
Replace Landscape section - tighter 3-col grid, compressed cards,
brighter headers, blue ✗ lines, orange answers.
Run from ~/Desktop/files/: python3 patch_landscape_v2.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

old_start = '<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:80px 48px;">\n  <div class="container">\n    <div style="text-align:center;margin-bottom:48px;">\n      <div class="section-label">Landscape</div>\n      <div class="section-title brand-heading" style="">Every tool solves a different problem.'

if old_start not in content:
    print("❌ Could not find Landscape section start. Aborting. NO CHANGES MADE.")
    exit(1)

start_idx = content.index(old_start)

end_marker = '</section>\n\n<!-- METRICS -->'
if end_marker not in content:
    print("❌ Could not find Landscape section end. Aborting. NO CHANGES MADE.")
    exit(1)

end_idx = content.index(end_marker, start_idx) + len('</section>')

new_section = '''<section style="background:var(--darker);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:80px 48px;">
  <div class="container">
    <div style="text-align:center;margin-bottom:36px;">
      <div class="section-label">Landscape</div>
      <div class="section-title brand-heading" style="">Every tool solves a different problem.<br>None of them solve this one.</div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;max-width:920px;margin:0 auto;">

      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">
        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Output Validation</div>
        <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;">Guardrails AI · NeMo Guardrails</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px;">Validates LLM text outputs — toxicity, PII, hallucinations, schema compliance.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;margin-bottom:4px;">Answers: "Is this output safe?"</div>
        <div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Does not govern what the agent does to real systems</div>
      </div>

      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">
        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Model Behavior Control</div>
        <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;">CTGT · Mentat</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px;">Modifies model behavior at the representation level. Deterministic output control without retraining.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;margin-bottom:4px;">Answers: "Is this model compliant?"</div>
        <div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Does not sit at the execution boundary of real systems</div>
      </div>

      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">
        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Sandbox &amp; Environment Security</div>
        <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;">IronClaw · NemoClaw · OpenShell</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px;">Container-level isolation. Controls network egress and what the agent can access.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;margin-bottom:4px;">Answers: "Can this agent access this?"</div>
        <div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Once access is granted, no business-level decision control</div>
      </div>

      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;">
        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Infrastructure &amp; Endpoint Security</div>
        <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;">CrowdStrike · Palo Alto · Okta</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px;">Protects endpoints, networks, and identity. Operates below the application layer.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;margin-bottom:4px;">Answers: "Is this process allowed to run?"</div>
        <div style="font-size:11px;color:var(--blue);font-weight:500;">✗ No concept of business context or action correctness</div>
      </div>

      <div class="runtime-card" style="border-color:rgba(255,255,255,0.08);padding:16px 18px;grid-column:2/4;">
        <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text);margin-bottom:6px;font-weight:600;">Agent Runtimes</div>
        <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;">OpenClaw · LangChain · CrewAI · AutoGen</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px;">Frameworks that plan, reason, and select tools. Internal governance is controlled by the same system it constrains.</div>
        <div style="font-size:11px;color:var(--orange);font-weight:600;margin-bottom:4px;">Answers: "What should the agent do?"</div>
        <div style="font-size:11px;color:var(--blue);font-weight:500;">✗ Self-regulation is not enforcement — internal controls are optional and framework-bound</div>
      </div>

    </div>

    <div style="max-width:920px;margin:14px auto 0;">
      <div class="runtime-card" style="border-color:rgba(38,192,255,0.4);border-width:2px;background:rgba(38,192,255,0.04);padding:20px 24px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div>
            <div style="font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--blue);margin-bottom:4px;">Execution Boundary — Decision Infrastructure</div>
            <div style="font-size:18px;font-weight:700;color:var(--blue);">Surfit</div>
          </div>
          <div style="background:var(--blue);color:#000;font-size:9px;font-weight:700;padding:3px 12px;border-radius:10px;letter-spacing:.1em;">DIFFERENT LAYER</div>
        </div>
        <div style="font-size:12px;color:var(--text);line-height:1.7;margin-bottom:12px;">Surfit sits at the execution boundary — between the agent and every system it touches. Every action is intercepted, evaluated in business context, and either auto-executed or routed to the right team. The agent proposes. Surfit decides whether it should happen.</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px;">
          <div style="font-size:11px;color:var(--text);padding:6px 10px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Holds credentials — agent cannot bypass</div>
          <div style="font-size:11px;color:var(--text);padding:6px 10px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Cross-system consistency — one decision model</div>
          <div style="font-size:11px;color:var(--text);padding:6px 10px;background:rgba(38,192,255,0.07);border-radius:6px;border-left:2px solid var(--blue);">Routes decisions to the right team</div>
        </div>
        <div style="font-size:12px;font-weight:600;color:var(--blue);">Answers: "Is this the right action for the business right now — and does the right person know?"</div>
      </div>
    </div>

  </div>
</section>'''

content = content[:start_idx] + new_section + content[end_idx:]

with open(filepath, "w") as f:
    f.write(content)

print("✅ Landscape section replaced with tighter 3-col layout")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'landscape v2: tighter 3-col, brighter headers, blue failure lines' && git push")
