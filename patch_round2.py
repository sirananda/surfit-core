"""
Round 2: Remove Operational Signal section.
Uses exact string match — the full section content from <!-- METRICS --> to </section>.
No boundary walking. No rfind. No index arithmetic.

Run from ~/Desktop/files/: python3 patch_round2.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

old_section = """<!-- METRICS -->
<section class="metrics-section" id="metrics">
  <div class="container">
    <div class="metrics-header">
      <div class="section-label">Operational Signal</div>
      <div class="section-title brand-heading" style="">Every Wave run is measurable.</div>
      <p class="section-body">Every Wave produces structural governance metrics. Not post-hoc analytics — intrinsic measurements of bounded execution.</p>
    </div>
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-val">0.09<span style="font-size:18px"> ms</span></div>
        <div class="metric-lbl">Autonomous Execution Duration</div>
        <div class="metric-desc">Total autonomous execution time across all governed nodes within a Wave.</div>
      </div>
      <div class="metric-card">
        <div class="metric-val orange">∞</div>
        <div class="metric-lbl">Agent Persistence</div>
        <div class="metric-desc">Agents run continuously. Surfit bounds their execution into discrete, governed Waves — not their existence.</div>
      </div>
      <div class="metric-card">
        <div class="metric-val white">SHA256</div>
        <div class="metric-lbl">Policy Hash</div>
        <div class="metric-desc">Canonical fingerprint of the policy bundle governing every run. Immutable at run start.</div>
      </div>
      <div class="metric-card">
        <div class="metric-val">✓</div>
        <div class="metric-lbl">Integrity Status</div>
        <div class="metric-desc">Programmatic verification that no execution record was altered post-run. Valid or flagged — no ambiguity.</div>
      </div>
    </div>
  </div>
</section>"""

if old_section in content:
    content = content.replace(old_section, '')
    with open(filepath, "w") as f:
        f.write(content)
    print("✅ Operational Signal section removed")
    print("If broken: git checkout index.html")
    print("If good: git add index.html && git commit -m 'remove Operational Signal section' && git push")
else:
    print("❌ Exact string not found. NO CHANGES MADE.")
    print("The section content may differ slightly. Run:")
    print("  sed -n '1078,1110p' ~/Desktop/files/index.html")
    print("and share the output so I can match it exactly.")
