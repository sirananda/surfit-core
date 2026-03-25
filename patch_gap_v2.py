"""
Replace Gap diagram with credential-focused design.
Flow 1: Agent holds keys, passes through babysitters/guards, catastrophe.
Flow 2: Surfit holds keys, massive dominant box, dual output paths.

Run from ~/Desktop/files/: python3 patch_gap_v2.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

old_start = '<!-- THE GAP DIAGRAM -->'
old_end = '<!-- COMPARISON TABLE -->'

if old_start not in content or old_end not in content:
    print("❌ Could not find Gap diagram boundaries. NO CHANGES MADE.")
    exit(1)

start_idx = content.index(old_start)
end_idx = content.index(old_end)

new_diagram = '''<!-- THE GAP DIAGRAM -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:940px;">
    <div style="text-align:center;margin-bottom:40px;">
      <div class="section-label">The Gap</div>
      <div class="section-title brand-heading" style="">The agent has credentials.<br>Who decides what it does with them?</div>
    </div>

    <!-- FLOW 1: WITHOUT SURFIT -->
    <div style="margin-bottom:48px;">
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:16px;">Without Surfit — The agent holds the keys</div>

      <div style="display:flex;align-items:stretch;gap:0;flex-wrap:nowrap;">

        <!-- Agent with key -->
        <div style="flex:0.8;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:14px;text-align:center;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:18px;margin-bottom:4px;">🤖🔑</div>
          <div style="font-size:11px;font-weight:600;color:var(--text);">Agent</div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px;">Holds credentials directly</div>
        </div>

        <div style="color:var(--muted);padding:0 5px;font-size:14px;display:flex;align-items:center;">→</div>

        <!-- Babysitters -->
        <div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;">Output Validation</div>
          <div style="font-size:10px;color:var(--muted);">Guardrails AI · CTGT</div>
          <div style="font-size:10px;color:var(--green);margin-top:4px;">✓ "Text looks safe"</div>
          <div style="font-size:9px;color:var(--muted);margin-top:2px;font-style:italic;">Checks words, not actions</div>
        </div>

        <div style="color:var(--muted);padding:0 5px;font-size:14px;display:flex;align-items:center;">→</div>

        <!-- Guards -->
        <div style="flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;">Sandbox &amp; Access</div>
          <div style="font-size:10px;color:var(--muted);">IronClaw · NemoClaw</div>
          <div style="font-size:10px;color:var(--green);margin-top:4px;">✓ "Access permitted"</div>
          <div style="font-size:9px;color:var(--muted);margin-top:2px;font-style:italic;">Checks the door, not the decision</div>
        </div>

        <div style="color:var(--muted);padding:0 5px;font-size:14px;display:flex;align-items:center;">→</div>

        <!-- NO EVALUATION ZONE -->
        <div style="flex:0.4;display:flex;align-items:center;justify-content:center;">
          <div style="border:2px dashed rgba(239,68,68,0.3);border-radius:8px;padding:10px 8px;text-align:center;width:100%;">
            <div style="font-size:10px;color:var(--red);font-weight:600;">NO LAYER HERE</div>
            <div style="font-size:9px;color:var(--muted);margin-top:2px;">Nobody evaluates<br>business impact</div>
          </div>
        </div>

        <div style="color:var(--red);padding:0 5px;font-size:14px;display:flex;align-items:center;">→</div>

        <!-- CATASTROPHE -->
        <div style="flex:1.2;background:rgba(239,68,68,0.06);border:2px solid rgba(239,68,68,0.4);border-radius:8px;padding:14px;text-align:center;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:18px;margin-bottom:4px;">💥</div>
          <div style="font-size:10px;color:var(--red);font-weight:700;margin-bottom:4px;">PRODUCTION</div>
          <div style="font-size:10px;color:var(--text);line-height:1.4;">Agent deploys untested payment code.</div>
          <div style="font-size:10px;color:var(--red);margin-top:4px;line-height:1.4;font-weight:500;">14,000 transactions fail.<br>$2.3M in failed charges.<br>Legal review initiated.</div>
        </div>

      </div>

      <div style="text-align:center;margin-top:14px;font-size:12px;color:var(--red);font-weight:500;">The babysitters checked the words. The guards checked the door. The agent had the keys the entire time.</div>
    </div>

    <!-- FLOW 2: WITH SURFIT -->
    <div>
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:16px;">With Surfit — Surfit holds the keys</div>

      <div style="display:flex;align-items:stretch;gap:0;flex-wrap:nowrap;">

        <!-- Agent WITHOUT key -->
        <div style="flex:0.7;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:14px;text-align:center;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:18px;margin-bottom:4px;">🤖</div>
          <div style="font-size:11px;font-weight:600;color:var(--text);">Agent</div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px;">Proposes action</div>
          <div style="font-size:9px;color:var(--blue);margin-top:2px;font-style:italic;">No credentials</div>
        </div>

        <div style="color:var(--blue);padding:0 5px;font-size:14px;display:flex;align-items:center;">→</div>

        <!-- SURFIT — DOMINANT -->
        <div style="flex:2.5;background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:10px;padding:16px 20px;position:relative;box-shadow:0 0 30px rgba(38,192,255,0.08);">
          <div style="position:absolute;top:-10px;left:20px;background:var(--blue);color:#000;font-size:9px;font-weight:700;padding:2px 12px;border-radius:10px;letter-spacing:.12em;">SURFIT</div>
          <div style="position:absolute;top:-10px;right:20px;font-size:10px;color:var(--blue);font-weight:600;">🔑 Holds all credentials</div>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:6px;margin-bottom:12px;">
            <div style="background:rgba(38,192,255,0.08);border-radius:6px;padding:8px;text-align:center;">
              <div style="font-size:9px;color:var(--blue);font-weight:600;margin-bottom:2px;">EVALUATE</div>
              <div style="font-size:9px;color:var(--muted);">Business context, risk, destination, content</div>
            </div>
            <div style="background:rgba(38,192,255,0.08);border-radius:6px;padding:8px;text-align:center;">
              <div style="font-size:9px;color:var(--blue);font-weight:600;margin-bottom:2px;">CLASSIFY</div>
              <div style="font-size:9px;color:var(--muted);">Wave 1-5 risk scoring per action</div>
            </div>
            <div style="background:rgba(38,192,255,0.08);border-radius:6px;padding:8px;text-align:center;">
              <div style="font-size:9px;color:var(--blue);font-weight:600;margin-bottom:2px;">ENFORCE</div>
              <div style="font-size:9px;color:var(--muted);">Credential vault, audit trail, routing</div>
            </div>
          </div>

          <!-- Dual output paths -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:6px;padding:10px;text-align:center;">
              <div style="font-size:9px;color:var(--green);font-weight:600;letter-spacing:.1em;margin-bottom:6px;">WAVE 1-3 · AUTO-EXECUTE</div>
              <div style="font-size:10px;color:var(--muted);line-height:1.5;">Slack update to #eng → ✓<br>Notion log entry → ✓<br>PR to dev branch → ✓<br>Gmail internal reply → ✓<br>AWS CloudWatch read → ✓</div>
              <div style="font-size:9px;color:var(--green);margin-top:6px;font-weight:500;">5 actions executed instantly. Full audit trail.</div>
            </div>
            <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.2);border-radius:6px;padding:10px;text-align:center;">
              <div style="font-size:9px;color:var(--blue);font-weight:600;letter-spacing:.1em;margin-bottom:6px;">WAVE 4-5 · HELD</div>
              <div style="font-size:10px;color:var(--muted);line-height:1.5;">PR merge to main → ⏸<br><span style="font-size:9px;">Financial system implications detected</span><br><br>Post to company X → ⏸<br><span style="font-size:9px;">External-facing, unapproved content</span></div>
              <div style="font-size:9px;color:var(--blue);margin-top:6px;font-weight:500;">2 actions held. Right teams notified.</div>
            </div>
          </div>
        </div>

      </div>

      <div style="text-align:center;margin-top:14px;font-size:12px;color:var(--blue);font-weight:500;">The agent never held the credentials. Surfit evaluated every action in business context. Most executed instantly. The dangerous ones were caught.</div>
    </div>

  </div>
</section>

'''

content = content[:start_idx] + new_diagram + content[end_idx:]

with open(filepath, "w") as f:
    f.write(content)

print("✅ Gap diagram replaced with credential-focused design")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'gap diagram v2: credential authority, dual output paths' && git push")
