"""
Insert "The Gap" flow diagram between Agent Integration and Landscape sections.
Shows one agent action passing through every layer — and still reaching production unchecked.
Then shows the same flow WITH Surfit catching it.

Run from ~/Desktop/files/: python3 patch_gap_diagram.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

insert_before = '<!-- COMPARISON TABLE -->'

if insert_before not in content:
    print("❌ Could not find insertion point. NO CHANGES MADE.")
    exit(1)

diagram = '''<!-- THE GAP DIAGRAM -->
<section style="background:var(--dark);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:900px;">
    <div style="text-align:center;margin-bottom:36px;">
      <div class="section-label">The Gap</div>
      <div class="section-title brand-heading" style="">An agent wants to merge a PR to production.</div>
      <p style="color:var(--muted);font-size:14px;font-weight:300;margin-top:12px;">Every existing tool says yes. Nobody asks whether it should happen.</p>
    </div>

    <!-- WITHOUT SURFIT -->
    <div style="margin-bottom:32px;">
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:14px;">Without Surfit</div>

      <div style="display:flex;align-items:center;gap:0;flex-wrap:nowrap;">

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">Guardrails AI</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Checks text output</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Output clean"</div>
        </div>

        <div style="color:var(--muted);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">CTGT / Mentat</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Constrains model</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Model compliant"</div>
        </div>

        <div style="color:var(--muted);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">IronClaw / NemoClaw</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Checks access</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Access granted"</div>
        </div>

        <div style="color:var(--muted);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1;background:rgba(239,68,68,0.08);border:2px solid rgba(239,68,68,0.4);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--red);margin-bottom:4px;font-weight:600;">PRODUCTION</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">PR merges to main</div>
          <div style="font-size:10px;color:var(--red);font-weight:600;">⚠ No one evaluated business impact</div>
        </div>

      </div>

      <div style="text-align:center;margin-top:12px;font-size:12px;color:var(--red);font-weight:500;">Every layer passed. The action was technically valid. It broke the billing pipeline for 3 hours.</div>
    </div>

    <!-- WITH SURFIT -->
    <div>
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:14px;">With Surfit</div>

      <div style="display:flex;align-items:center;gap:0;flex-wrap:nowrap;">

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">Guardrails AI</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Checks text output</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Output clean"</div>
        </div>

        <div style="color:var(--muted);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">CTGT / Mentat</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Constrains model</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Model compliant"</div>
        </div>

        <div style="color:var(--muted);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">IronClaw / NemoClaw</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Checks access</div>
          <div style="font-size:10px;color:var(--green);font-weight:600;">✓ "Access granted"</div>
        </div>

        <div style="color:var(--blue);padding:0 6px;font-size:16px;">→</div>

        <div style="flex:1.3;background:rgba(38,192,255,0.08);border:2px solid rgba(38,192,255,0.4);border-radius:8px;padding:12px 14px;text-align:center;box-shadow:0 0 20px rgba(38,192,255,0.1);">
          <div style="font-size:10px;color:var(--blue);margin-bottom:4px;font-weight:700;">SURFIT</div>
          <div style="font-size:11px;color:var(--text);margin-bottom:4px;">Production merge. Financial system.</div>
          <div style="font-size:10px;color:var(--blue);font-weight:600;">⏸ HELD — Engineering lead notified</div>
        </div>

      </div>

      <div style="text-align:center;margin-top:12px;font-size:12px;color:var(--blue);font-weight:500;">Same action. Same layers. Surfit held it because it evaluated business context — not just safety, access, or compliance.</div>
    </div>

  </div>
</section>

'''

content = content.replace(insert_before, diagram + insert_before)

with open(filepath, "w") as f:
    f.write(content)

print("✅ Gap diagram inserted above Landscape section")
print("If broken: git checkout index.html")
print("If good: git add index.html && git commit -m 'add gap diagram — shows what every tool misses' && git push")
