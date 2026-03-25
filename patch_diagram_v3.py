"""
Surfit Site Patch — Aggressive positioning diagram redesign
Surfit must DOMINATE. Other layers must look incomplete without it.
Run from ~/Desktop/files/: python3 patch_diagram_v3.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

old_section_start = '''<!-- WHERE SURFIT FITS -->'''
old_section_end = '''<!-- CTA -->'''

if old_section_start in content and old_section_end in content:
    start_idx = content.index(old_section_start)
    end_idx = content.index(old_section_end)
    
    new_section = '''<!-- WHERE SURFIT FITS -->
<section style="background:var(--darker);border-top:1px solid var(--border);padding:80px 48px;">
  <div class="container" style="max-width:1020px;">
    <div class="section-label">Where Surfit Fits</div>
    <div class="section-title brand-heading" style="">Every agent action passes through three layers.<br>Only one decides what should happen.</div>

    <div style="margin-top:40px;">

      <!-- LAYER 1: AGENT RUNTIME — looks incomplete -->
      <div style="display:grid;grid-template-columns:52px 1fr;gap:16px;align-items:start;margin-bottom:6px;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding-top:16px;">
          <div style="width:44px;height:44px;border-radius:50%;background:rgba(249,115,22,0.15);border:1px solid rgba(249,115,22,0.3);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;color:var(--orange);">1</div>
        </div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:10px;padding:20px 24px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--orange);font-weight:600;">Agent Runtime</div>
            <div style="display:flex;gap:6px;">
              <span style="font-size:10px;color:var(--muted);background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:3px;">OpenClaw</span>
              <span style="font-size:10px;color:var(--muted);background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:3px;">LangChain</span>
              <span style="font-size:10px;color:var(--muted);background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:3px;">CrewAI</span>
              <span style="font-size:10px;color:var(--muted);background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:3px;">AutoGen</span>
            </div>
          </div>
          <div style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:6px;">Decides what to do</div>
          <div style="font-size:12px;color:var(--muted);line-height:1.6;">Plans, reasons, selects tools, generates intent. Produces an action the agent wants to take — but has no ability to evaluate whether that action is correct for the business, appropriate for the context, or safe to execute across real systems.</div>
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);">
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Cannot evaluate business correctness</span>
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Cannot enforce cross-system consistency</span>
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Cannot route decisions to the right team</span>
            </div>
          </div>
        </div>
      </div>

      <!-- CONNECTOR -->
      <div style="padding-left:26px;height:28px;display:flex;align-items:center;">
        <div style="width:2px;height:100%;background:linear-gradient(to bottom, var(--orange), var(--blue));opacity:0.4;"></div>
        <div style="color:var(--muted);font-size:11px;margin-left:12px;">Agent proposes action — but cannot execute it directly</div>
      </div>

      <!-- LAYER 2: SURFIT — DOMINATES -->
      <div style="display:grid;grid-template-columns:52px 1fr;gap:16px;align-items:start;margin-bottom:6px;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding-top:16px;">
          <div style="width:52px;height:52px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:20px;color:#000;box-shadow:0 0 24px rgba(38,192,255,0.35);">2</div>
        </div>
        <div style="background:rgba(38,192,255,0.06);border:2px solid rgba(38,192,255,0.4);border-radius:10px;padding:24px 28px;position:relative;box-shadow:0 0 40px rgba(38,192,255,0.08);">
          <div style="position:absolute;top:-12px;right:24px;background:var(--blue);color:#000;font-size:10px;font-weight:800;padding:3px 14px;border-radius:10px;letter-spacing:.12em;">SURFIT</div>

          <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);font-weight:600;margin-bottom:8px;">Decision Infrastructure — The Execution Boundary</div>
          <div style="font-size:20px;font-weight:700;color:var(--blue);margin-bottom:10px;">Decides what should happen</div>

          <div style="font-size:13px;color:var(--text);line-height:1.8;margin-bottom:14px;">Every action the agent proposes is intercepted at this layer — before it reaches any system. Surfit evaluates the action in full business context: What are the implications of this action? Which team should this decision involve? Does this need a human decision or can it proceed automatically? Is this consistent with how the organization handles this type of action across all systems?</div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
            <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.15);border-radius:6px;padding:12px 14px;">
              <div style="font-size:11px;color:var(--blue);font-weight:700;margin-bottom:4px;">Business Context Evaluation</div>
              <div style="font-size:11px;color:var(--muted);line-height:1.5;">Every action is classified by content, destination, sensitivity, and organizational impact. A message to #eng-platform is different from one to #company-announcements. A PR to dev is different from one to main. Context determines the decision.</div>
            </div>
            <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.15);border-radius:6px;padding:12px 14px;">
              <div style="font-size:11px;color:var(--blue);font-weight:700;margin-bottom:4px;">Decision Routing</div>
              <div style="font-size:11px;color:var(--muted);line-height:1.5;">High-risk actions are surfaced to the right team member — engineering decisions to engineering, communications to comms, operations to ops. Routine actions flow automatically with full logging. Every decision is accountable.</div>
            </div>
            <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.15);border-radius:6px;padding:12px 14px;">
              <div style="font-size:11px;color:var(--blue);font-weight:700;margin-bottom:4px;">Cross-System Consistency</div>
              <div style="font-size:11px;color:var(--muted);line-height:1.5;">One decision model across every system. Whether the agent acts on Slack, GitHub, Notion, Gmail, AWS, or any enterprise platform — the same evaluation logic, the same routing, the same audit trail. No fragmentation.</div>
            </div>
            <div style="background:rgba(38,192,255,0.06);border:1px solid rgba(38,192,255,0.15);border-radius:6px;padding:12px 14px;">
              <div style="font-size:11px;color:var(--blue);font-weight:700;margin-bottom:4px;">Execution Authority</div>
              <div style="font-size:11px;color:var(--muted);line-height:1.5;">Surfit holds the credentials to every downstream system. The agent doesn't. This isn't a suggestion layer — it's an enforcement boundary. The agent cannot bypass Surfit because it physically cannot reach the systems without it.</div>
            </div>
          </div>

          <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(38,192,255,0.2);border-radius:8px;padding:16px 20px;margin-bottom:14px;">
            <div style="font-size:12px;font-weight:700;color:var(--blue);margin-bottom:8px;">Why this layer cannot be replicated</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div>
                <div style="font-size:11px;color:var(--text);font-weight:600;margin-bottom:3px;">Not by agent runtimes</div>
                <div style="font-size:11px;color:var(--muted);line-height:1.5;">Self-regulation is not enforcement. The same system that executes cannot neutrally judge its own actions. Internal controls are optional and framework-bound.</div>
              </div>
              <div>
                <div style="font-size:11px;color:var(--text);font-weight:600;margin-bottom:3px;">Not by security platforms</div>
                <div style="font-size:11px;color:var(--muted);line-height:1.5;">Security decides what's allowed at the infrastructure level. It has no concept of business context, organizational routing, or whether an action is correct — only whether it's permitted.</div>
              </div>
              <div>
                <div style="font-size:11px;color:var(--text);font-weight:600;margin-bottom:3px;">Not by internal builds</div>
                <div style="font-size:11px;color:var(--muted);line-height:1.5;">Building this internally means rebuilding decision logic for every agent, every framework, and every system. It fragments immediately and becomes the most expensive infrastructure you maintain.</div>
              </div>
            </div>
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <span style="font-size:10px;color:var(--blue);background:rgba(38,192,255,0.1);padding:3px 10px;border-radius:4px;font-weight:600;">Framework-agnostic</span>
            <span style="font-size:10px;color:var(--blue);background:rgba(38,192,255,0.1);padding:3px 10px;border-radius:4px;font-weight:600;">Vendor-neutral</span>
            <span style="font-size:10px;color:var(--blue);background:rgba(38,192,255,0.1);padding:3px 10px;border-radius:4px;font-weight:600;">Architecturally independent</span>
            <span style="font-size:10px;color:var(--blue);background:rgba(38,192,255,0.1);padding:3px 10px;border-radius:4px;font-weight:600;">Hash-chained audit trail</span>
            <span style="font-size:10px;color:var(--blue);background:rgba(38,192,255,0.1);padding:3px 10px;border-radius:4px;font-weight:600;">Real-time decisioning</span>
          </div>
        </div>
      </div>

      <!-- CONNECTOR -->
      <div style="padding-left:26px;height:28px;display:flex;align-items:center;">
        <div style="width:2px;height:100%;background:linear-gradient(to bottom, var(--blue), var(--green));opacity:0.4;"></div>
        <div style="color:var(--green);font-size:11px;margin-left:12px;">Approved action executes with full audit trail →</div>
      </div>

      <!-- DESTINATION (de-emphasized) -->
      <div style="display:grid;grid-template-columns:52px 1fr;gap:16px;align-items:start;margin-bottom:28px;">
        <div style="display:flex;flex-direction:column;align-items:center;padding-top:10px;">
          <div style="width:32px;height:32px;border-radius:50%;background:rgba(34,197,94,0.1);display:flex;align-items:center;justify-content:center;">
            <span style="color:var(--green);font-size:14px;">✓</span>
          </div>
        </div>
        <div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:12px 18px;opacity:0.6;">
          <div style="font-size:10px;color:var(--green);font-weight:600;letter-spacing:.1em;margin-bottom:2px;">DESTINATION</div>
          <div style="font-size:12px;color:var(--muted);">Slack · GitHub · Notion · Gmail · Outlook · AWS · CRMs · ERPs · Any API-based system</div>
        </div>
      </div>

      <!-- HARD DIVIDER -->
      <div style="border-top:1px solid var(--border);margin:24px 0;position:relative;">
        <span style="position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:var(--darker);padding:0 16px;font-size:10px;color:var(--muted);letter-spacing:.1em;">SEPARATE CONCERN</span>
      </div>

      <!-- INFRASTRUCTURE LAYER — clearly different -->
      <div style="display:grid;grid-template-columns:52px 1fr;gap:16px;align-items:start;">
        <div style="display:flex;flex-direction:column;align-items:center;padding-top:12px;">
          <div style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.04);display:flex;align-items:center;justify-content:center;">
            <span style="color:var(--muted);font-size:12px;font-weight:600;">◆</span>
          </div>
        </div>
        <div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:16px 22px;">
          <div style="display:flex;align-items:start;justify-content:space-between;flex-wrap:wrap;gap:12px;">
            <div>
              <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:4px;">Infrastructure Layer</div>
              <div style="font-size:13px;font-weight:600;color:var(--text);">Security &amp; Endpoint Platforms</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">CrowdStrike · Palo Alto · Okta · Endpoint protection · Identity management</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:12px;color:var(--muted);font-weight:600;">Decides what is allowed</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Network, process, identity, access control</div>
            </div>
          </div>
          <div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);">
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Cannot evaluate business correctness</span>
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Cannot route decisions to business teams</span>
              <span style="font-size:11px;color:var(--red);font-weight:600;">✗ Has no concept of organizational context</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div style="display:flex;justify-content:center;gap:28px;margin-top:28px;">
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--orange);opacity:0.7;"></span>
          Agents decide what to do
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--blue);font-weight:600;">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--blue);box-shadow:0 0 8px rgba(38,192,255,0.4);"></span>
          Surfit decides what should happen
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);">
          <span style="width:8px;height:8px;border-radius:50%;background:var(--muted);opacity:0.5;"></span>
          Security decides what is allowed
        </div>
      </div>

    </div>
  </div>
</section>

'''
    
    content = content[:start_idx] + new_section + content[end_idx:]
    changes += 1
    print("✅ 'Where Surfit Fits' section completely rebuilt — Surfit dominates")
else:
    print("⚠️  Could not find section boundaries")

with open(filepath, "w") as f:
    f.write(content)

print(f"\n✅ Done — {changes} changes applied")
print("Now: git add index.html && git commit -m 'aggressive positioning diagram — surfit dominates' && git push")
