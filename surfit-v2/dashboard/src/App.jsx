import { useState, useEffect, useCallback } from "react";


// ============================================================
// API SERVICE — Real Wave Engine at localhost:8000
// ============================================================
const API_BASE = "http://localhost:8000";

const SurfitAPI = {
  async evaluate(payload) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/governance/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[SurfitAPI] Engine not available, using fallback:", err.message);
      return null;
    }
  },
  async ingestSlack(payload) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/ingest/slack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[SurfitAPI] Slack ingestion failed:", err.message);
      return null;
    }
  },
  async health() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/health`);
      return res.ok;
    } catch { return false; }
  },
};

// ============================================================
// SURFIT V2 — Live Engine Integration — Product-Grade Polish
// ============================================================

const WAVES = {
  1: { label: "Wave 1", sub: "Autonomous", color: "#34D399", bg: "rgba(52,211,153,0.08)", ring: "rgba(52,211,153,0.20)", desc: "Executes instantly. No human touch." },
  2: { label: "Wave 2", sub: "Logged", color: "#60A5FA", bg: "rgba(96,165,250,0.08)", ring: "rgba(96,165,250,0.20)", desc: "Executes and records for async review." },
  3: { label: "Wave 3", sub: "Checked", color: "#FBBF24", bg: "rgba(251,191,36,0.08)", ring: "rgba(251,191,36,0.20)", desc: "Verified against rules before executing." },
  4: { label: "Wave 4", sub: "Approval", color: "#F97316", bg: "rgba(249,115,22,0.08)", ring: "rgba(249,115,22,0.20)", desc: "Requires human sign-off to proceed." },
  5: { label: "Wave 5", sub: "Critical", color: "#EF4444", bg: "rgba(239,68,68,0.08)", ring: "rgba(239,68,68,0.20)", desc: "Highest scrutiny. Escalated and gated." },
};

const MOCK_POLICIES = [
  { system: "slack", action: "post_message", wave: 1, handling: "auto", reason: "Low-risk internal message" },
  { system: "slack", action: "post_channel_message", wave: 2, handling: "log", reason: "Broadcast to shared channel" },
  { system: "slack", action: "post_announcement", wave: 4, handling: "approve", reason: "High visibility, company-wide reach" },
  { system: "notion", action: "create_page", wave: 1, handling: "auto", reason: "Standard content creation" },
  { system: "notion", action: "update_page", wave: 2, handling: "log", reason: "Modifies existing shared content" },
  { system: "notion", action: "update_database_entry", wave: 3, handling: "check", reason: "Structured data modification" },
  { system: "github", action: "create_pr", wave: 3, handling: "check", reason: "Code change requires review" },
  { system: "github", action: "merge_pr", wave: 5, handling: "approve", reason: "Irreversible production impact" },
  { system: "github", action: "delete_branch", wave: 4, handling: "approve", reason: "Destructive action on shared repo" },
];

const INITIAL_EXECUTIONS = [
  { id: "exec-001", action: "post_message", system: "slack", status: "completed", timestamp: "2026-03-17T10:23:14Z", wave: 1, decision: "auto", reason: "Low-risk internal message", decidedBy: "system", proof: { channel: "#general", ts: "1742210594.001" } },
  { id: "exec-002", action: "create_page", system: "notion", status: "completed", timestamp: "2026-03-17T10:21:07Z", wave: 1, decision: "auto", reason: "Standard content creation", decidedBy: "system", proof: { page_id: "ntn-8a3f2", url: "https://notion.so/page/8a3f2" } },
  { id: "exec-003", action: "create_pr", system: "github", status: "completed", timestamp: "2026-03-17T10:18:33Z", wave: 3, decision: "check", reason: "Code change requires review", decidedBy: "system", proof: { pr_number: 142, repo: "acme/core-api" } },
  { id: "exec-004", action: "merge_pr", system: "github", status: "pending_approval", timestamp: "2026-03-17T10:15:01Z", wave: 5, decision: "approve", reason: "Irreversible production impact", decidedBy: null, proof: null },
  { id: "exec-005", action: "post_announcement", system: "slack", status: "pending_approval", timestamp: "2026-03-17T10:12:44Z", wave: 4, decision: "approve", reason: "High visibility, company-wide reach", decidedBy: null, proof: null },
  { id: "exec-006", action: "update_database_entry", system: "notion", status: "completed", timestamp: "2026-03-17T09:58:22Z", wave: 3, decision: "check", reason: "Structured data modification", decidedBy: "system", proof: { database: "Sprint Tracker", entry_id: "row-44f1" } },
  { id: "exec-007", action: "post_channel_message", system: "slack", status: "completed", timestamp: "2026-03-17T09:45:11Z", wave: 2, decision: "log", reason: "Broadcast to shared channel", decidedBy: "system", proof: { channel: "#eng-alerts", ts: "1742207111.003" } },
  { id: "exec-008", action: "update_page", system: "notion", status: "completed", timestamp: "2026-03-17T09:30:00Z", wave: 2, decision: "log", reason: "Modifies existing shared content", decidedBy: "system", proof: { page_id: "ntn-c21b8", title: "Q1 Roadmap" } },
];

const SYSTEMS = {
  slack: { name: "Slack", icon: "\u{1F4AC}", color: "#4A154B", status: "connected" },
  notion: { name: "Notion", icon: "\u{1F4DD}", color: "#191919", status: "connected" },
  github: { name: "GitHub", icon: "\u2699\uFE0F", color: "#238636", status: "connected" },
};

const AVAILABLE_ACTIONS = {
  slack: [
    { id: "post_message", label: "Post Message", defaultWave: 1 },
    { id: "post_channel_message", label: "Post Channel Message", defaultWave: 2 },
    { id: "post_announcement", label: "Post Announcement", defaultWave: 4 },
  ],
  notion: [
    { id: "create_page", label: "Create Page", defaultWave: 1 },
    { id: "update_page", label: "Update Page", defaultWave: 2 },
    { id: "update_database_entry", label: "Update Database Entry", defaultWave: 3 },
  ],
  github: [
    { id: "create_pr", label: "Create PR", defaultWave: 3 },
    { id: "merge_pr", label: "Merge PR", defaultWave: 5 },
    { id: "delete_branch", label: "Delete Branch", defaultWave: 4 },
  ],
};

const statusMeta = {
  completed: { bg: "rgba(52,211,153,0.08)", text: "#34D399", label: "Completed" },
  approved: { bg: "rgba(52,211,153,0.08)", text: "#34D399", label: "Approved" },
  pending_approval: { bg: "rgba(249,115,22,0.08)", text: "#F97316", label: "Pending" },
  rejected: { bg: "rgba(239,68,68,0.08)", text: "#EF4444", label: "Rejected" },
  overridden: { bg: "rgba(167,139,250,0.08)", text: "#A78BFA", label: "Overridden" },
};

const c = {
  bg: "#080B0F",
  sf: "#0F1318",
  sf2: "#141A22",
  sfh: "#181F2A",
  bd: "#1A2233",
  bdl: "#243044",
  tx: "#E8ECF4",
  txs: "#C8D0DC",
  txm: "#7D8FA6",
  txd: "#4A5A72",
  ac: "#38BDF8",
  acd: "rgba(56,189,248,0.08)",
  ach: "rgba(56,189,248,0.14)",
  gn: "#34D399",
  gnd: "rgba(52,211,153,0.08)",
  pu: "#A78BFA",
  pud: "rgba(167,139,250,0.08)",
  or: "#F97316",
  ord: "rgba(249,115,22,0.08)",
  rd: "#EF4444",
  rdd: "rgba(239,68,68,0.08)",
  // brand
  brandBlue: "#38BDF8",
  brandOrange: "#F97316",
};

// ============================================================
// BRAND WORDMARK
// ============================================================
function SurfitMark({ size = 16 }) {
  return (
    <span style={{ fontSize: size, fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1 }}>
      <span style={{ color: c.brandBlue }}>Surfit</span><span style={{ color: c.brandOrange }}>AI</span>
    </span>
  );
}

// ============================================================
// PRIMITIVES
// ============================================================
function WaveBadge({ wave, compact }) {
  const w = WAVES[wave];
  if (!w) return null;
  if (compact) return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 9px", borderRadius: 6, fontSize: 10, fontWeight: 600, color: w.color, background: w.bg, border: `1px solid ${w.ring}`, whiteSpace: "nowrap" }}>
      {w.label}
    </span>
  );
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 600, color: w.color, background: w.bg, border: `1px solid ${w.ring}`, whiteSpace: "nowrap" }}>
      {w.label}<span style={{ opacity: 0.65, fontWeight: 500 }}>{w.sub}</span>
    </span>
  );
}

function StatusBadge({ status }) {
  const s = statusMeta[status];
  if (!s) return <span style={{ fontSize: 10, color: c.txd }}>{status}</span>;
  return <span style={{ display: "inline-flex", padding: "3px 9px", borderRadius: 6, fontSize: 10, fontWeight: 600, color: s.text, background: s.bg, whiteSpace: "nowrap" }}>{s.label}</span>;
}

function SI({ system, size = 18 }) {
  const s = SYSTEMS[system];
  if (!s) return null;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: size + 8, height: size + 8, borderRadius: 6, background: s.color + "18", fontSize: size * 0.65 }}>
      {s.icon}
    </span>
  );
}

function Card({ children, style, onClick, hover }) {
  const [hv, setHv] = useState(false);
  return (
    <div onClick={onClick} onMouseEnter={() => setHv(true)} onMouseLeave={() => setHv(false)}
      style={{
        background: hv && hover ? c.sfh : c.sf2,
        border: `1px solid ${hv && hover ? c.bdl : c.bd}`,
        borderRadius: 12, padding: 18,
        transition: "all 0.15s ease",
        cursor: onClick ? "pointer" : "default",
        ...style,
      }}>
      {children}
    </div>
  );
}

function ActionBtn({ label, color, bg, ring, onClick }) {
  const [hv, setHv] = useState(false);
  return (
    <button onClick={e => { e.stopPropagation(); onClick(); }}
      onMouseEnter={() => setHv(true)} onMouseLeave={() => setHv(false)}
      style={{
        padding: "7px 16px", borderRadius: 7,
        border: `1px solid ${hv ? color : ring || color + "44"}`,
        background: hv ? color + "22" : bg,
        color, fontSize: 11, fontWeight: 600, cursor: "pointer",
        transition: "all 0.15s ease", whiteSpace: "nowrap",
        transform: hv ? "translateY(-1px)" : "none",
        boxShadow: hv ? `0 4px 12px ${color}22` : "none",
      }}>
      {label}
    </button>
  );
}

function SectionHead({ children, sub, right }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 12 }}>
      <div>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: c.tx, margin: 0, letterSpacing: "-0.01em" }}>{children}</h2>
        {sub && <p style={{ fontSize: 11, color: c.txm, margin: "3px 0 0 0" }}>{sub}</p>}
      </div>
      {right}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div style={{ fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13, color: c.tx, fontWeight: 500 }}>{children}</div>
    </div>
  );
}

function fmtT(ts) { return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true }); }
function fmtA(a) { return a.replace(/_/g, " ").replace(/\b\w/g, ch => ch.toUpperCase()); }
function fmtFull(ts) { return new Date(ts).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }); }

// ============================================================
// WAVE LADDER
// ============================================================
function WaveLadder({ style }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, ...style }}>
      {[1, 2, 3, 4, 5].map(w => {
        const wv = WAVES[w];
        return (
          <div key={w} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              padding: "7px 12px", borderRadius: 8, background: wv.bg,
              border: `1px solid ${wv.ring}`, minWidth: 68,
            }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: wv.color, letterSpacing: "-0.01em" }}>{wv.label}</span>
              <span style={{ fontSize: 8, color: wv.color, opacity: 0.6, marginTop: 2, fontWeight: 500 }}>{wv.sub}</span>
            </div>
            {w < 5 && <span style={{ color: c.txd, fontSize: 10, margin: "0 1px" }}>{"\u203A"}</span>}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================
// RECEIPT MODAL
// ============================================================
function ReceiptModal({ execution, onClose }) {
  if (!execution) return null;
  const wv = WAVES[execution.wave] || {};
  const sm = statusMeta[execution.status] || {};

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={onClose}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.65)", backdropFilter: "blur(6px)" }} />
      <div onClick={e => e.stopPropagation()} style={{
        position: "relative", width: 500, maxHeight: "85vh", overflowY: "auto",
        background: c.sf, border: `1px solid ${c.bd}`, borderRadius: 16, padding: 0,
        boxShadow: "0 32px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.03) inset",
      }}>
        {/* Modal Header */}
        <div style={{ padding: "22px 26px 16px", borderBottom: `1px solid ${c.bd}`, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: sm.text || c.txd }} />
              <span style={{ fontSize: 10, fontWeight: 700, color: sm.text || c.txm, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Execution Receipt
              </span>
            </div>
            <div style={{ fontSize: 18, fontWeight: 700, color: c.tx, letterSpacing: "-0.02em" }}>{fmtA(execution.action)}</div>
            <div style={{ fontSize: 11, color: c.txd, fontFamily: "'SF Mono', 'Cascadia Code', monospace", marginTop: 4 }}>{execution.id}</div>
          </div>
          <button onClick={onClose} style={{ background: c.sf2, border: `1px solid ${c.bd}`, color: c.txm, width: 28, height: 28, borderRadius: 7, fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>{"\u00D7"}</button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: "20px 26px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 20 }}>
            <Field label="System"><span style={{ display: "flex", alignItems: "center", gap: 6 }}><SI system={execution.system} size={15} />{SYSTEMS[execution.system]?.name}</span></Field>
            <Field label="Action">{fmtA(execution.action)}</Field>
            <Field label="Wave"><WaveBadge wave={execution.wave} /></Field>
            <Field label="Decision"><span style={{ fontWeight: 600, color: sm.text, textTransform: "capitalize" }}>{execution.status === "overridden" ? "Override" : execution.status === "rejected" ? "Rejected" : execution.decision}</span></Field>
            <Field label="Status"><StatusBadge status={execution.status} /></Field>
            <Field label="Decided By"><span style={{ color: execution.decidedBy === "operator" ? c.ac : c.txm }}>{execution.decidedBy === "operator" ? "Operator (you)" : execution.decidedBy || "\u2014"}</span></Field>
          </div>

          {/* WHY */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Why</div>
            <div style={{
              fontSize: 13, color: c.tx, fontWeight: 500, padding: "12px 16px",
              background: wv.bg, borderRadius: 8, borderLeft: `3px solid ${wv.color}`,
              lineHeight: "1.5",
            }}>
              {execution.reason}
            </div>
          </div>

          {/* Timestamp */}
          <div style={{ marginBottom: 20 }}>
            <Field label="Timestamp"><span style={{ fontFamily: "'SF Mono', monospace", fontSize: 11, color: c.txs }}>{fmtFull(execution.timestamp)}</span></Field>
          </div>

          {/* Proof */}
          <div>
            <div style={{ fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Proof</div>
            <div style={{ background: c.bg, borderRadius: 8, padding: 14, border: `1px solid ${c.bd}` }}>
              {execution.proof ? (
                <pre style={{ margin: 0, fontSize: 11, color: c.ac, fontFamily: "'SF Mono', monospace", whiteSpace: "pre-wrap", lineHeight: "1.6" }}>
                  {JSON.stringify(execution.proof, null, 2)}
                </pre>
              ) : (
                <div style={{ fontSize: 11, color: c.txd, fontStyle: "italic" }}>Proof pending — will attach on execution</div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{ padding: "14px 26px 20px", borderTop: `1px solid ${c.bd}`, display: "flex", justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{
            padding: "9px 24px", borderRadius: 8, border: `1px solid ${c.bd}`,
            background: c.sf2, color: c.txm, fontSize: 12, fontWeight: 500, cursor: "pointer",
            transition: "all 0.12s",
          }}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// POLICY EDIT DRAWER
// ============================================================
function PolicyEditDrawer({ policy, onClose, onSave }) {
  const [wave, setWave] = useState(policy?.wave || 1);
  useEffect(() => { if (policy) setWave(policy.wave); }, [policy]);
  if (!policy) return null;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", justifyContent: "flex-end" }} onClick={onClose}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }} />
      <div onClick={e => e.stopPropagation()} style={{
        position: "relative", width: 380, height: "100%", background: c.sf,
        borderLeft: `1px solid ${c.bd}`, padding: 28, overflowY: "auto",
        boxShadow: "-16px 0 48px rgba(0,0,0,0.4)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: c.tx }}>Edit Policy</div>
          <button onClick={onClose} style={{ background: c.sf2, border: `1px solid ${c.bd}`, color: c.txm, width: 28, height: 28, borderRadius: 7, fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>{"\u00D7"}</button>
        </div>

        <div style={{ marginBottom: 18 }}>
          <Field label="System"><span style={{ display: "flex", alignItems: "center", gap: 6 }}><SI system={policy.system} size={15} />{SYSTEMS[policy.system]?.name}</span></Field>
        </div>
        <div style={{ marginBottom: 18 }}><Field label="Action">{fmtA(policy.action)}</Field></div>
        <div style={{ marginBottom: 24 }}><Field label="Current Reason"><span style={{ fontStyle: "italic", color: c.txm }}>{policy.reason}</span></Field></div>

        <div style={{ fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Wave Level</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {[1, 2, 3, 4, 5].map(w => {
            const wv = WAVES[w];
            const sel = wave === w;
            return (
              <div key={w} onClick={() => setWave(w)} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "12px 14px", borderRadius: 8, cursor: "pointer",
                border: `1px solid ${sel ? wv.color + "55" : c.bd}`,
                background: sel ? wv.bg : "transparent",
                transition: "all 0.15s",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: wv.color }}>{wv.label}</span>
                  <span style={{ fontSize: 11, color: sel ? wv.color : c.txd, fontWeight: 500 }}>{wv.sub}</span>
                </div>
                {sel && <div style={{ width: 8, height: 8, borderRadius: "50%", background: wv.color }} />}
              </div>
            );
          })}
        </div>

        <div style={{ marginTop: 28, display: "flex", gap: 10 }}>
          <button onClick={() => { onSave(policy.system, policy.action, wave); onClose(); }} style={{
            flex: 1, padding: "11px 0", borderRadius: 8, border: "none",
            background: c.ac, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
          }}>Save Changes</button>
          <button onClick={onClose} style={{
            padding: "11px 20px", borderRadius: 8, border: `1px solid ${c.bd}`,
            background: "transparent", color: c.txm, fontSize: 13, cursor: "pointer",
          }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// ACTION CONTROL PANEL
// ============================================================
function ActionControlPanel({ policies, onEditPolicy }) {
  const grouped = {};
  policies.forEach(p => { if (!grouped[p.system]) grouped[p.system] = []; grouped[p.system].push(p); });

  return (
    <div style={{ marginBottom: 28 }}>
      <SectionHead sub="Every action, every system — governed by your rules">How your agents are handled</SectionHead>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        {Object.entries(grouped).map(([sys, pols]) => (
          <Card key={sys} style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <SI system={sys} size={17} />
              <span style={{ fontSize: 14, fontWeight: 600, color: c.tx }}>{SYSTEMS[sys]?.name}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {pols.map((pol, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "8px 0",
                  borderTop: i > 0 ? `1px solid ${c.bd}` : "none",
                }}>
                  <span style={{ fontSize: 12, color: c.txs, fontWeight: 500 }}>{fmtA(pol.action)}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <WaveBadge wave={pol.wave} compact />
                    <span onClick={() => onEditPolicy(pol)}
                      style={{ fontSize: 10, color: c.txd, cursor: "pointer", padding: "2px 5px", borderRadius: 4, transition: "all 0.12s" }}
                      onMouseEnter={e => { e.target.style.color = c.ac; e.target.style.background = c.acd; }}
                      onMouseLeave={e => { e.target.style.color = c.txd; e.target.style.background = "transparent"; }}>
                      {"\u270E"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}


// ============================================================
// SIMULATE ACTION PANEL
// ============================================================
const SIMULATE_PRESETS = [
  { label: "Slack DM", system: "slack", action: "post_dm", resource: { channel_id: "D0USER123", channel_name: "dm_user_123" }, context: { env: "prod", visibility: "internal", reversible: true }, content: { text: "Hey, can you review the PR when you get a chance?" } },
  { label: "Slack Team Post", system: "slack", action: "post_message", resource: { channel_id: "C0ENG001", channel_name: "eng-platform" }, context: { env: "prod", visibility: "internal", reversible: true }, content: { text: "CI pipeline is green. All tests passing." } },
  { label: "Slack Announcement", system: "slack", action: "post_announcement", resource: { channel_id: "C0ANN001", channel_name: "company-announcements" }, context: { env: "prod", visibility: "company_wide", reversible: true }, content: { text: "Q1 results are in. Company all-hands tomorrow at 2pm." } },
  { label: "Slack Sensitive", system: "slack", action: "post_message", resource: { channel_id: "C0SEC001", channel_name: "security-incidents" }, context: { env: "prod", visibility: "internal", reversible: true, sensitive_data: true }, content: { text: "Potential credential exposure detected in staging logs." } },
  { label: "Slack External", system: "slack", action: "post_message", resource: { channel_id: "C0EXT001", channel_name: "partner-updates" }, context: { env: "prod", visibility: "external", reversible: true }, content: { text: "Integration milestone completed. API v2 is live." } },
  { label: "Notion DB Update", system: "notion", action: "update_database_entry", resource: { database: "Sprint Tracker" }, context: { env: "prod", visibility: "internal", reversible: true } },
  { label: "GitHub Merge Main", system: "github", action: "merge_pr", resource: { repo: "main" }, context: { env: "prod", visibility: "internal", reversible: false } },
  { label: "GitHub Deploy Prod", system: "github", action: "deploy_production", resource: { repo: "production" }, context: { env: "prod", visibility: "internal", reversible: false } },
];

function SimulatePanel({ onResult }) {
  const [running, setRunning] = useState(null);
  const [engineUp, setEngineUp] = useState(null);

  useEffect(() => { SurfitAPI.health().then(setEngineUp); }, []);

  const run = async (preset, idx) => {
    setRunning(idx);
    const isSlack = preset.system === "slack";
    let result;

    if (isSlack) {
      // Route Slack through ingestion endpoint
      const slackPayload = {
        event_type: "message_attempt",
        system: "slack",
        action: preset.action,
        resource: preset.resource,
        context: preset.context,
        content: preset.content,
      };
      result = await SurfitAPI.ingestSlack(slackPayload);
      setRunning(null);
      if (result) {
        onResult({
          id: result.id,
          system: "slack",
          action: preset.action,
          status: result.status,
          timestamp: result.timestamp,
          wave: result.wave_score,
          decision: result.handling,
          reason: result.reasons?.[result.reasons.length - 2] || result.reasons?.[0] || "Evaluated via Slack ingestion",
          reasons: result.reasons,
          contributing_factors: result.contributing_factors,
          destination_class_resolved: result.destination_class,
          decidedBy: result.decided_by,
          proof: result.proof,
          content_preview: result.content_preview,
          source: "slack_ingestion",
        });
      }
    } else {
      // GitHub/Notion use direct evaluate
      const payload = { system: preset.system, action: preset.action, resource: preset.resource, context: preset.context };
      result = await SurfitAPI.evaluate(payload);
      setRunning(null);
      if (result) {
        onResult({
          id: "sim-" + Date.now(),
          system: preset.system,
          action: preset.action,
          status: result.handling === "approve" ? "pending_approval" : "completed",
          timestamp: new Date().toISOString(),
          wave: result.wave_score,
          decision: result.handling,
          reason: result.reasons?.[result.reasons.length - 2] || result.reasons?.[0] || "Evaluated by engine",
          reasons: result.reasons,
          contributing_factors: result.contributing_factors,
          destination_class_resolved: result.destination_class_resolved,
          decidedBy: result.handling === "approve" ? null : "system",
          proof: result.handling !== "approve" ? { evaluated_at: new Date().toISOString(), wave: result.wave_label } : null,
        });
      }
    }
  };

  return (
    <div style={{ marginBottom: 28 }}>
      <SectionHead
        sub="Send real actions to the Wave Engine and see live decisions"
        right={
          <span style={{ fontSize: 10, fontWeight: 600, color: engineUp ? c.gn : c.rd, display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: engineUp ? c.gn : engineUp === false ? c.rd : c.txd }} />
            {engineUp ? "Engine Live" : engineUp === false ? "Engine Offline" : "Checking..."}
          </span>
        }
      >Simulate Action</SectionHead>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {SIMULATE_PRESETS.map((p, i) => {
          const sysColor = p.system === "slack" ? "#4A154B" : p.system === "notion" ? "#191919" : "#238636";
          return (
            <Card key={i} hover onClick={() => run(p, i)} style={{
              padding: "12px 14px", textAlign: "center",
              opacity: running !== null && running !== i ? 0.4 : 1,
              border: running === i ? `1px solid ${c.ac}` : undefined,
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: c.tx, marginBottom: 3 }}>{p.label}</div>
              <div style={{ fontSize: 10, color: c.txd }}>{p.system}/{p.action}</div>
              {running === i && <div style={{ fontSize: 9, color: c.ac, marginTop: 4 }}>Evaluating...</div>}
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// WAVE BREAKDOWN MODAL — "Why This Wave"
// ============================================================
function WaveBreakdownModal({ execution, onClose }) {
  if (!execution || !execution.contributing_factors) return null;
  const factors = execution.contributing_factors || [];
  const reasons = execution.reasons || [];
  const wv = WAVES[execution.wave] || {};

  // Generate human-readable summary from factors
  const keyFactors = factors.filter(f => f.modifier > 0).map(f => {
    if (f.source === "system_baseline") return `${f.key} system`;
    if (f.source === "action_modifier") return f.key.split("/")[1]?.replace(/_/g, " ");
    if (f.source === "destination_modifier") return f.key.split("/")[1]?.replace(/_/g, " ") + " destination";
    if (f.source === "context_modifier") return f.description.split("(")[1]?.replace(")", "") || f.key;
    return f.key;
  }).filter(Boolean);
  const summary = keyFactors.length > 0
    ? `This action was assigned ${wv.label || "Wave " + execution.wave} because of: ${keyFactors.join(", ")}.`
    : `This action was assigned ${wv.label || "Wave " + execution.wave}.`;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1001, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={onClose}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.65)", backdropFilter: "blur(6px)" }} />
      <div onClick={e => e.stopPropagation()} style={{
        position: "relative", width: 520, maxHeight: "85vh", overflowY: "auto",
        background: c.sf, border: `1px solid ${c.bd}`, borderRadius: 16, padding: 0,
        boxShadow: "0 32px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.03) inset",
      }}>
        <div style={{ padding: "22px 26px 16px", borderBottom: `1px solid ${c.bd}`, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: wv.color || c.ac, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
              Why This Wave
            </div>
            <div style={{ fontSize: 18, fontWeight: 700, color: c.tx }}>{fmtA(execution.action)}</div>
            <div style={{ fontSize: 11, color: c.txd, marginTop: 2 }}>{SYSTEMS[execution.system]?.name} {"\u2014"} {execution.destination_class_resolved || "unknown"}</div>
          </div>
          <button onClick={onClose} style={{ background: c.sf2, border: `1px solid ${c.bd}`, color: c.txm, width: 28, height: 28, borderRadius: 7, fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>{"\u00D7"}</button>
        </div>

        <div style={{ padding: "20px 26px" }}>
          {/* Human-readable summary */}
          <div style={{ fontSize: 13, color: c.tx, lineHeight: "1.5", marginBottom: 16, padding: "12px 16px", background: wv.bg, borderRadius: 8, borderLeft: `3px solid ${wv.color}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <WaveBadge wave={execution.wave} />
              <span style={{ fontSize: 13, fontWeight: 600, color: c.tx, textTransform: "capitalize" }}>{execution.decision}</span>
            </div>
            <div style={{ fontSize: 12, color: c.txm }}>{summary}</div>
          </div>

          {/* Factor breakdown */}
          <div style={{ fontSize: 10, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Contributing Factors</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 20 }}>
            {factors.map((f, i) => {
              const isPositive = f.modifier > 0;
              const isNegative = f.modifier < 0;
              const modColor = isPositive ? (f.modifier >= 2 ? c.or : c.txs) : isNegative ? c.gn : c.txd;
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", background: c.sf2, borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 500, color: c.tx }}>{f.description}</div>
                    <div style={{ fontSize: 9, color: c.txd, marginTop: 2 }}>{f.source} {"\u2014"} {f.key}</div>
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 700, color: modColor, fontFamily: "'SF Mono', monospace", minWidth: 32, textAlign: "right" }}>
                    {f.modifier > 0 ? "+" : ""}{f.modifier}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Score math */}
          <div style={{ fontSize: 10, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Score Calculation</div>
          <div style={{ padding: "10px 14px", background: c.bg, borderRadius: 8, border: `1px solid ${c.bd}`, fontFamily: "'SF Mono', monospace", fontSize: 11, color: c.ac, lineHeight: "1.6" }}>
            {factors.map(f => `${f.key}(${f.modifier > 0 ? "+" : ""}${f.modifier})`).join(" + ")}
            {execution.raw_score !== undefined && <> = {execution.raw_score}</>}
            {" \u2192 "}{execution.wave_label || `Wave ${execution.wave}`}
          </div>
        </div>

        <div style={{ padding: "14px 26px 20px", borderTop: `1px solid ${c.bd}`, display: "flex", justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ padding: "9px 24px", borderRadius: 8, border: `1px solid ${c.bd}`, background: c.sf2, color: c.txm, fontSize: 12, fontWeight: 500, cursor: "pointer" }}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// NAV
// ============================================================
const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "\u25C9" },
  { id: "policies", label: "Policies", icon: "\u25EB" },
  { id: "receipts", label: "Receipts", icon: "\u25E7" },
  { id: "onboarding", label: "Setup", icon: "\u25CE" },
  { id: "integration", label: "Integration", icon: "\u25C8" },
];

function Sidebar({ active, onNav, pendingCount }) {
  return (
    <div style={{
      width: 210, minHeight: "100%", background: c.sf,
      borderRight: `1px solid ${c.bd}`,
      display: "flex", flexDirection: "column", padding: "20px 0", flexShrink: 0,
    }}>
      {/* Brand */}
      <div style={{ padding: "0 18px 20px", borderBottom: `1px solid ${c.bd}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: "#0F1A2E",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <svg width="22" height="16" viewBox="0 0 120 90" xmlns="http://www.w3.org/2000/svg"><path d="M0,18 C15,4 30,4 45,14 C60,24 65,28 80,18 C95,8 105,4 120,14 L120,30 C105,20 95,24 80,34 C65,44 60,40 45,30 C30,20 15,20 0,34 Z" fill="#38BDF8"/><path d="M0,38 C15,24 30,24 45,34 C60,44 65,48 80,38 C95,28 105,24 120,34 L120,50 C105,40 95,44 80,54 C65,64 60,60 45,50 C30,40 15,40 0,54 Z" fill="#38BDF8"/><path d="M0,58 C15,44 30,44 45,54 C60,64 65,68 80,58 C95,48 105,44 120,54 L120,70 C105,60 95,64 80,74 C65,84 60,80 45,70 C30,60 15,60 0,74 Z" fill="#38BDF8"/></svg>
          </div>
          <div>
            <SurfitMark size={16} />
            <div style={{ fontSize: 9, color: c.txd, letterSpacing: "0.05em", textTransform: "uppercase", marginTop: 1 }}>Action Control</div>
          </div>
        </div>

        {/* Connected Workspace */}
        <div style={{
          padding: "10px 12px", border: `1px solid ${c.bd}`, borderRadius: 8,
          background: c.sf2,
        }}>
          <div style={{ fontSize: 9, color: c.txd, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 5 }}>Connected Workspace</div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 24, height: 24, borderRadius: 5, background: c.bdl, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, color: c.txd }}>{"\u25A3"}</div>
            <span style={{ fontSize: 12, color: c.txm, fontWeight: 500 }}>Your Company</span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <div style={{ padding: "14px 10px", flex: 1 }}>
        {NAV.map(item => {
          const act = active === item.id;
          return (
            <div key={item.id} onClick={() => onNav(item.id)}
              style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "9px 12px", borderRadius: 8, marginBottom: 2, cursor: "pointer",
                background: act ? c.ach : "transparent",
                color: act ? c.ac : c.txm,
                fontSize: 13, fontWeight: act ? 600 : 400,
                transition: "all 0.12s",
              }}>
              <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                <span style={{ fontSize: 13, opacity: act ? 1 : 0.45 }}>{item.icon}</span>{item.label}
              </div>
              {item.id === "dashboard" && pendingCount > 0 && (
                <span style={{
                  fontSize: 9, fontWeight: 700, color: "#000", background: c.or,
                  borderRadius: 10, padding: "2px 7px", minWidth: 18, textAlign: "center",
                }}>{pendingCount}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: "14px 18px", borderTop: `1px solid ${c.bd}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: c.gn }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: c.gn, boxShadow: `0 0 6px ${c.gn}66` }} />
          Backend Connected
        </div>
        <div style={{ fontSize: 10, color: c.txd, marginTop: 4 }}>v1.1.0</div>
      </div>
    </div>
  );
}

// ============================================================
// DASHBOARD
// ============================================================
function DashboardView({ executions, policies, onAction, onSelectExecution, onNav, onEditPolicy, onSimulateResult, setWaveBreakdown }) {
  const pending = executions.filter(e => e.status === "pending_approval");
  const resolved = executions.filter(e => e.status !== "pending_approval");

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: c.tx, margin: 0, letterSpacing: "-0.02em" }}>
          <SurfitMark size={22} /> <span style={{ fontWeight: 400, color: c.txm, fontSize: 18 }}>{" \u2014 Action Control for Agents"}</span>
        </h1>
        <p style={{ fontSize: 13, color: c.txm, margin: "5px 0 0 0" }}>How your agents take action across your systems</p>
      </div>

      <WaveLadder style={{ marginBottom: 24 }} />

      {/* Simulate */}
      <SimulatePanel onResult={onSimulateResult} />

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 28 }}>
        {[
          { l: "Systems", v: Object.keys(SYSTEMS).length, cl: c.ac },
          { l: "Governed Actions", v: policies.length, cl: c.pu },
          { l: "Awaiting Decision", v: pending.length, cl: c.or },
          { l: "Resolved Today", v: resolved.length, cl: c.gn },
        ].map((s, i) => (
          <Card key={i}>
            <div style={{ fontSize: 10, color: c.txm, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>{s.l}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: s.cl, letterSpacing: "-0.02em" }}>{s.v}</div>
          </Card>
        ))}
      </div>

      {/* Control Panel */}
      <ActionControlPanel policies={policies} onEditPolicy={onEditPolicy} />

      {/* Pending Actions */}
      {pending.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <SectionHead
            sub="These actions require your decision before proceeding"
            right={<span style={{ fontSize: 10, fontWeight: 700, color: "#000", background: c.or, borderRadius: 10, padding: "2px 10px" }}>{pending.length} pending</span>}
          >Actions Awaiting Decision</SectionHead>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {pending.map(e => (
              <Card key={e.id} style={{
                padding: 16,
                borderLeft: `3px solid ${WAVES[e.wave]?.color || c.bd}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1 }}>
                    <SI system={e.system} size={20} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: c.tx, marginBottom: 2 }}>{fmtA(e.action)}</div>
                      <div style={{ fontSize: 11, color: c.txm }}>
                        {SYSTEMS[e.system]?.name} {"\u00B7"} {fmtT(e.timestamp)} {"\u00B7"} <span style={{ fontStyle: "italic", color: c.txd }}>{e.reason}</span>
                      </div>
                    </div>
                    <WaveBadge wave={e.wave} />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: 16 }}>
                    <ActionBtn label="Approve" color={c.gn} bg={c.gnd} ring={WAVES[1].ring} onClick={() => onAction(e.id, "approved")} />
                    <ActionBtn label="Reject" color={c.rd} bg={c.rdd} ring={WAVES[5].ring} onClick={() => onAction(e.id, "rejected")} />
                    <ActionBtn label="Override" color={c.pu} bg={c.pud} ring="rgba(167,139,250,0.20)" onClick={() => onAction(e.id, "overridden")} />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {pending.length === 0 && (
        <Card style={{ marginBottom: 28, textAlign: "center", padding: "24px 18px" }}>
          <div style={{ fontSize: 14, color: c.gn, fontWeight: 600, marginBottom: 3 }}>All clear</div>
          <div style={{ fontSize: 12, color: c.txm }}>No actions awaiting your decision</div>
        </Card>
      )}

      {/* Systems */}
      <SectionHead sub="Connected systems and governance status">Systems</SectionHead>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 28 }}>
        {Object.keys(SYSTEMS).map(s => {
          const sys = SYSTEMS[s];
          const pc = policies.filter(q => q.system === s).length;
          const ec = executions.filter(q => q.system === s).length;
          return (
            <Card key={s} hover onClick={() => onNav("policies")}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                <SI system={s} size={20} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: c.tx }}>{sys.name}</div>
                  <div style={{ fontSize: 11, color: c.gn, fontWeight: 500 }}>{sys.status}</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 14, fontSize: 11, color: c.txm }}>
                <span><strong style={{ color: c.tx }}>{pc}</strong> policies</span>
                <span><strong style={{ color: c.tx }}>{ec}</strong> recent</span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Recent Activity */}
      <SectionHead sub="Latest governed actions across all systems">Recent Activity</SectionHead>
      <Card style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${c.bd}` }}>
              {["System", "Action", "Wave", "Decision", "Why", "Status", "Time"].map(h => (
                <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {executions.slice(0, 8).map(e => (
              <tr key={e.id} onClick={() => onSelectExecution(e)}
                style={{ borderBottom: `1px solid ${c.bd}`, cursor: "pointer", transition: "background 0.1s" }}
                onMouseEnter={ev => ev.currentTarget.style.background = c.sfh}
                onMouseLeave={ev => ev.currentTarget.style.background = "transparent"}>
                <td style={{ padding: "10px 12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                    <SI system={e.system} size={15} />
                    <span style={{ color: c.tx, fontWeight: 500 }}>{SYSTEMS[e.system]?.name}</span>
                  </div>
                </td>
                <td style={{ padding: "10px 12px", color: c.txs }}>{fmtA(e.action)}</td>
                <td style={{ padding: "10px 12px" }}><WaveBadge wave={e.wave} compact /></td>
                <td style={{ padding: "10px 12px" }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: WAVES[e.wave]?.color, textTransform: "capitalize" }}>{e.decision}</span>
                </td>
                <td style={{ padding: "10px 12px", maxWidth: 150 }}>
                  <span onClick={(ev) => { ev.stopPropagation(); if (e.contributing_factors) setWaveBreakdown(e); }} style={{ fontSize: 11, color: e.contributing_factors ? c.ac : c.txd, fontStyle: "italic", cursor: e.contributing_factors ? "pointer" : "default", textDecoration: e.contributing_factors ? "underline dotted" : "none" }}>{e.reason}</span>
                </td>
                <td style={{ padding: "10px 12px" }}><StatusBadge status={e.status} /></td>
                <td style={{ padding: "10px 12px", color: c.txm, fontSize: 11 }}>{fmtT(e.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

// ============================================================
// POLICIES
// ============================================================
function PolicyView({ policies, onEditPolicy }) {
  const [fs, setFs] = useState("all");
  const filtered = fs === "all" ? policies : policies.filter(q => q.system === fs);
  const grouped = {};
  filtered.forEach(q => { if (!grouped[q.system]) grouped[q.system] = []; grouped[q.system].push(q); });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 21, fontWeight: 700, color: c.tx, margin: 0, letterSpacing: "-0.01em" }}>Action Policies</h1>
          <p style={{ fontSize: 12, color: c.txm, margin: "4px 0 0 0" }}>How your company wants agent actions handled</p>
        </div>
        <div style={{ display: "flex", gap: 5 }}>
          {["all", ...Object.keys(SYSTEMS)].map(s => (
            <button key={s} onClick={() => setFs(s)} style={{
              padding: "6px 14px", borderRadius: 7,
              border: `1px solid ${fs === s ? c.ac : c.bd}`,
              background: fs === s ? c.acd : "transparent",
              color: fs === s ? c.ac : c.txm,
              fontSize: 12, fontWeight: 500, cursor: "pointer", textTransform: "capitalize",
            }}>{s === "all" ? "All" : SYSTEMS[s]?.name}</button>
          ))}
        </div>
      </div>

      <WaveLadder style={{ marginBottom: 22 }} />

      {Object.entries(grouped).map(([sys, pols]) => (
        <div key={sys} style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <SI system={sys} size={17} />
            <span style={{ fontSize: 14, fontWeight: 600, color: c.tx }}>{SYSTEMS[sys]?.name}</span>
            <span style={{ fontSize: 11, color: c.txd }}>{pols.length} actions</span>
          </div>
          <Card style={{ padding: 0, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${c.bd}` }}>
                  {["Action", "Wave", "Handling", "Why", ""].map(h => (
                    <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pols.map((q, i) => (
                  <tr key={i} style={{ borderBottom: i < pols.length - 1 ? `1px solid ${c.bd}` : "none" }}>
                    <td style={{ padding: "12px 14px", color: c.tx, fontWeight: 500 }}>{fmtA(q.action)}</td>
                    <td style={{ padding: "12px 14px" }}><WaveBadge wave={q.wave} /></td>
                    <td style={{ padding: "12px 14px" }}><span style={{ fontSize: 12, fontWeight: 600, color: WAVES[q.wave]?.color, textTransform: "capitalize" }}>{q.handling}</span></td>
                    <td style={{ padding: "12px 14px", maxWidth: 200 }}><span style={{ fontSize: 11, color: c.txd, fontStyle: "italic" }}>{q.reason}</span></td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <span onClick={() => onEditPolicy(q)} style={{ fontSize: 11, color: c.ac, cursor: "pointer", fontWeight: 500 }}>{"Edit \u2192"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      ))}

      <Card>
        <div style={{ fontSize: 10, fontWeight: 600, color: c.txm, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>Wave System</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[1, 2, 3, 4, 5].map(w => {
            const wv = WAVES[w];
            return (
              <div key={w} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <WaveBadge wave={w} />
                <span style={{ fontSize: 12, color: c.txm }}>{wv.desc}</span>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

// ============================================================
// RECEIPTS
// ============================================================
function ReceiptView({ executions, selected }) {
  const [detail, setDetail] = useState(selected || null);
  useEffect(() => { if (selected) setDetail(selected); }, [selected]);

  if (detail) {
    const wv = WAVES[detail.wave] || {};
    return (
      <div>
        <button onClick={() => setDetail(null)} style={{ background: "none", border: "none", color: c.ac, cursor: "pointer", fontSize: 12, padding: 0, marginBottom: 8 }}>{"\u2190 All Receipts"}</button>
        <h1 style={{ fontSize: 21, fontWeight: 700, color: c.tx, margin: "0 0 2px" }}>Execution Receipt</h1>
        <div style={{ fontSize: 11, color: c.txd, fontFamily: "'SF Mono', monospace", marginBottom: 20 }}>{detail.id}</div>
        <Card style={{ marginBottom: 18 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
            <Field label="System"><span style={{ display: "flex", alignItems: "center", gap: 6 }}><SI system={detail.system} size={15} />{SYSTEMS[detail.system]?.name}</span></Field>
            <Field label="Action">{fmtA(detail.action)}</Field>
            <Field label="Wave"><WaveBadge wave={detail.wave} /></Field>
            <Field label="Decision"><span style={{ fontWeight: 600, color: (statusMeta[detail.status] || {}).text, textTransform: "capitalize" }}>{detail.decision}</span></Field>
            <div style={{ gridColumn: "1 / -1" }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: c.txd, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 5 }}>Why</div>
              <div style={{ fontSize: 13, color: c.tx, fontWeight: 500, padding: "12px 16px", background: wv.bg, borderRadius: 8, borderLeft: `3px solid ${wv.color}` }}>{detail.reason}</div>
            </div>
            <Field label="Status"><StatusBadge status={detail.status} /></Field>
            <Field label="Decided By"><span style={{ color: detail.decidedBy === "operator" ? c.ac : c.txm }}>{detail.decidedBy === "operator" ? "Operator (you)" : detail.decidedBy || "\u2014"}</span></Field>
            <Field label="Timestamp"><span style={{ fontFamily: "'SF Mono', monospace", fontSize: 11 }}>{fmtFull(detail.timestamp)}</span></Field>
            <Field label="Execution ID"><span style={{ fontFamily: "'SF Mono', monospace", fontSize: 11, color: c.txm }}>{detail.id}</span></Field>
          </div>
        </Card>
        <SectionHead>Proof</SectionHead>
        <Card style={{ background: c.bg, border: `1px solid ${c.bd}` }}>
          {detail.proof ? <pre style={{ margin: 0, fontSize: 11, color: c.ac, fontFamily: "'SF Mono', monospace", whiteSpace: "pre-wrap", lineHeight: "1.6" }}>{JSON.stringify(detail.proof, null, 2)}</pre> : <div style={{ fontSize: 12, color: c.txd, fontStyle: "italic" }}>Proof pending</div>}
        </Card>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 21, fontWeight: 700, color: c.tx, margin: "0 0 2px" }}>Execution Receipts</h1>
      <p style={{ fontSize: 12, color: c.txm, margin: "4px 0 0 0", marginBottom: 22 }}>Audit trail for every governed action</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {executions.map(e => (
          <Card key={e.id} hover onClick={() => setDetail(e)} style={{ borderLeft: `3px solid ${WAVES[e.wave]?.color || c.bd}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <SI system={e.system} size={19} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: c.tx }}>{fmtA(e.action)}</div>
                  <div style={{ fontSize: 11, color: c.txm }}>{SYSTEMS[e.system]?.name} {"\u00B7"} <span style={{ fontStyle: "italic", color: c.txd }}>{e.reason}</span></div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <WaveBadge wave={e.wave} compact />
                <StatusBadge status={e.status} />
                <span style={{ fontSize: 11, color: c.txd, minWidth: 60, textAlign: "right" }}>{fmtT(e.timestamp)}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// ONBOARDING
// ============================================================
function OnboardingView({ onComplete }) {
  const [step, setStep] = useState(1);
  const [agent, setAgent] = useState(null);
  const [selSys, setSelSys] = useState([]);
  const [selAct, setSelAct] = useState({});
  const [rules, setRules] = useState({});
  const [test, setTest] = useState(null);
  const togSys = s => setSelSys(v => v.includes(s) ? v.filter(x => x !== s) : [...v, s]);
  const togAct = (s, a) => setSelAct(v => { const curr = v[s] || []; return { ...v, [s]: curr.includes(a) ? curr.filter(x => x !== a) : [...curr, a] }; });
  const primary = (l, fn, on = true) => <button onClick={fn} disabled={!on} style={{ padding: "10px 26px", borderRadius: 8, border: "none", background: on ? c.ac : c.bd, color: on ? "#fff" : c.txd, fontSize: 13, fontWeight: 600, cursor: on ? "pointer" : "default", transition: "all 0.12s" }}>{l}</button>;
  const secondary = fn => <button onClick={fn} style={{ padding: "10px 20px", borderRadius: 8, border: `1px solid ${c.bd}`, background: "transparent", color: c.txm, fontSize: 13, cursor: "pointer" }}>Back</button>;

  return (
    <div>
      <h1 style={{ fontSize: 21, fontWeight: 700, color: c.tx, margin: "0 0 4px" }}>Setup <SurfitMark size={21} /></h1>
      <p style={{ fontSize: 12, color: c.txm, margin: "0 0 20px" }}>Configure action governance for your agent stack</p>
      <div style={{ height: 3, background: c.bd, borderRadius: 2, marginBottom: 28, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${(step / 5) * 100}%`, background: `linear-gradient(90deg, ${c.brandBlue}, ${c.brandOrange})`, borderRadius: 2, transition: "width 0.3s ease" }} />
      </div>

      {step === 1 && <div>
        <SectionHead sub="Surfit works with your existing agents by sitting between the agent and your systems.">{"1 \u00B7 Agent / Orchestrator"}</SectionHead>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
          {[{ id: "openclaw", n: "OpenClaw", d: "Native orchestrator" }, { id: "langgraph", n: "LangGraph", d: "LangChain framework" }, { id: "custom", n: "Custom Agent", d: "Any HTTP-based agent" }].map(a => (
            <Card key={a.id} hover onClick={() => setAgent(a.id)} style={{ border: `1px solid ${agent === a.id ? c.ac : c.bd}`, background: agent === a.id ? c.acd : c.sf2 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: agent === a.id ? c.ac : c.tx, marginBottom: 4 }}>{a.n}</div>
              <div style={{ fontSize: 11, color: c.txm }}>{a.d}</div>
            </Card>
          ))}
        </div>
        {primary("Continue", () => setStep(2), !!agent)}
      </div>}

      {step === 2 && <div>
        <SectionHead sub="Choose the systems you want Surfit to govern.">{"2 \u00B7 Select Systems"}</SectionHead>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
          {Object.entries(SYSTEMS).map(([key, sys]) => { const sel = selSys.includes(key); return (
            <Card key={key} hover onClick={() => togSys(key)} style={{ border: `1px solid ${sel ? c.ac : c.bd}`, background: sel ? c.acd : c.sf2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}><SI system={key} size={17} /><span style={{ fontSize: 14, fontWeight: 600, color: sel ? c.ac : c.tx }}>{sys.name}</span></div>
              <div style={{ fontSize: 11, color: c.txm }}>{AVAILABLE_ACTIONS[key]?.length} governable actions</div>
            </Card>
          ); })}
        </div>
        <div style={{ display: "flex", gap: 8 }}>{secondary(() => setStep(1))}{primary("Continue", () => setStep(3), selSys.length > 0)}</div>
      </div>}

      {step === 3 && <div>
        <SectionHead sub="Select which actions to govern per system.">{"3 \u00B7 Choose Actions"}</SectionHead>
        {selSys.map(sys => (<div key={sys} style={{ marginBottom: 20 }}><div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}><SI system={sys} size={16} /><span style={{ fontSize: 13, fontWeight: 600, color: c.tx }}>{SYSTEMS[sys]?.name}</span></div><div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>{(AVAILABLE_ACTIONS[sys] || []).map(act => { const sel = (selAct[sys] || []).includes(act.id); return <div key={act.id} onClick={() => togAct(sys, act.id)} style={{ padding: "8px 14px", borderRadius: 8, cursor: "pointer", border: `1px solid ${sel ? c.ac : c.bd}`, background: sel ? c.acd : c.sf2, color: sel ? c.ac : c.txm, fontSize: 12, fontWeight: 500, transition: "all 0.12s" }}>{act.label}</div>; })}</div></div>))}
        <div style={{ display: "flex", gap: 8 }}>{secondary(() => setStep(2))}{primary("Continue", () => setStep(4))}</div>
      </div>}

      {step === 4 && <div>
        <SectionHead sub="Assign a wave level to each action.">{"4 \u00B7 Set Wave Levels"}</SectionHead>
        <WaveLadder style={{ marginBottom: 18 }} />
        {selSys.map(sys => { const acts = selAct[sys] || []; if (!acts.length) return null; return (<div key={sys} style={{ marginBottom: 20 }}><div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}><SI system={sys} size={16} /><span style={{ fontSize: 13, fontWeight: 600, color: c.tx }}>{SYSTEMS[sys]?.name}</span></div><Card style={{ padding: 0, overflow: "hidden" }}>{acts.map((actId, i) => { const info = (AVAILABLE_ACTIONS[sys] || []).find(a => a.id === actId); const cur = rules[`${sys}:${actId}`] || info?.defaultWave || 1; return (<div key={actId} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 14px", borderBottom: i < acts.length - 1 ? `1px solid ${c.bd}` : "none" }}><span style={{ fontSize: 13, color: c.tx, fontWeight: 500 }}>{info?.label || actId}</span><div style={{ display: "flex", gap: 4 }}>{[1, 2, 3, 4, 5].map(w => { const wv = WAVES[w]; const isCur = cur === w; return <button key={w} onClick={() => setRules(v => ({ ...v, [`${sys}:${actId}`]: w }))} style={{ padding: "5px 10px", borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: "pointer", border: isCur ? `1px solid ${wv.ring}` : `1px solid ${c.bd}`, background: isCur ? wv.bg : "transparent", color: isCur ? wv.color : c.txd, transition: "all 0.12s" }}>W{w}</button>; })}</div></div>); })}</Card></div>); })}
        <div style={{ display: "flex", gap: 8 }}>{secondary(() => setStep(3))}{primary("Continue", () => setStep(5))}</div>
      </div>}

      {step === 5 && <div>
        <SectionHead sub="Verify your configuration works end to end.">{"5 \u00B7 Test Connection"}</SectionHead>
        <Card style={{ textAlign: "center", padding: "28px 20px" }}>
          {!test && <><div style={{ fontSize: 14, color: c.tx, fontWeight: 500, marginBottom: 5 }}>Ready to test your configuration</div><div style={{ fontSize: 12, color: c.txm, marginBottom: 20 }}>Simulates a governed action through your selected systems.</div><button onClick={() => { setTest("run"); setTimeout(() => setTest("ok"), 1800); }} style={{ padding: "10px 32px", borderRadius: 8, border: "none", background: c.ac, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>Run Test</button></>}
          {test === "run" && <div><div style={{ fontSize: 14, color: c.ac, fontWeight: 500 }}>Running test...</div><div style={{ width: 120, height: 3, background: c.bd, borderRadius: 2, margin: "14px auto", overflow: "hidden" }}><div style={{ height: "100%", width: "60%", background: `linear-gradient(90deg, ${c.brandBlue}, ${c.brandOrange})`, borderRadius: 2 }} /></div></div>}
          {test === "ok" && <div><div style={{ fontSize: 32, marginBottom: 8, color: c.gn }}>{"\u2713"}</div><div style={{ fontSize: 15, color: c.gn, fontWeight: 600, marginBottom: 4 }}>Test Passed</div><div style={{ fontSize: 12, color: c.txm, marginBottom: 20 }}>Your governance configuration is working correctly.</div><button onClick={onComplete} style={{ padding: "10px 32px", borderRadius: 8, border: "none", background: c.gn, color: "#000", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>Go to Dashboard</button></div>}
        </Card>
        <div style={{ marginTop: 14 }}>{secondary(() => setStep(4))}</div>
      </div>}
    </div>
  );
}

// ============================================================
// INTEGRATION
// ============================================================
function IntegrationView() {
  return (
    <div>
      <h1 style={{ fontSize: 21, fontWeight: 700, color: c.tx, margin: "0 0 4px" }}>Integration</h1>
      <p style={{ fontSize: 12, color: c.txm, margin: "0 0 24px" }}>How <SurfitMark size={13} /> works with your existing agent stack</p>

      <Card style={{ marginBottom: 24, background: `linear-gradient(135deg, ${c.acd}, ${c.pud})`, border: `1px solid ${c.ac}22` }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: c.tx, marginBottom: 8, lineHeight: "1.4" }}>Your agent decides <em style={{ color: c.txs }}>what</em> it wants to do.</div>
        <div style={{ fontSize: 16, fontWeight: 700, lineHeight: "1.4" }}><SurfitMark size={16} /> decides <em style={{ color: c.brandOrange }}>how</em> that action should happen.</div>
        <div style={{ fontSize: 12, color: c.txm, marginTop: 14, lineHeight: "1.6" }}>Surfit sits between your agent's intent and system execution. Every action is evaluated through the Wave system — from autonomous execution to critical approval gates.</div>
      </Card>

      <SectionHead>The Wave System</SectionHead>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[1, 2, 3, 4, 5].map(w => (
            <div key={w} style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <WaveBadge wave={w} />
              <span style={{ fontSize: 12, color: c.txm }}>{WAVES[w].desc}</span>
            </div>
          ))}
        </div>
      </Card>

      <SectionHead>How It Works</SectionHead>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 28 }}>
        {[
          { n: "1", t: "Agent Intent", d: "Your agent decides to take an action — Slack message, Notion update, GitHub PR.", cl: c.ac },
          { n: "2", t: "Wave Evaluation", d: "Surfit assigns a wave level, evaluates risk, and determines the right handling.", cl: c.pu },
          { n: "3", t: "Governed Execution", d: "Action proceeds per your rules. Everything receipted. You stay in control.", cl: c.gn },
        ].map(s => (
          <Card key={s.n}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: s.cl + "18", color: s.cl, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, marginBottom: 12 }}>{s.n}</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: c.tx, marginBottom: 5 }}>{s.t}</div>
            <div style={{ fontSize: 12, color: c.txm, lineHeight: "1.5" }}>{s.d}</div>
          </Card>
        ))}
      </div>

      <SectionHead sub="Surfit is not tied to any single agent framework">Agent Compatibility</SectionHead>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
          {[
            { n: "OpenClaw", d: "Native orchestrator with built-in integration", t: "Native" },
            { n: "LangGraph", d: "LangChain framework — middleware hook", t: "Supported" },
            { n: "Custom Agents", d: "Any HTTP agent — add Surfit as gateway", t: "Supported" },
          ].map(a => (
            <div key={a.n}>
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 5 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: c.tx }}>{a.n}</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: c.gn, background: c.gnd, padding: "3px 8px", borderRadius: 5 }}>{a.t}</span>
              </div>
              <div style={{ fontSize: 12, color: c.txm, lineHeight: "1.5" }}>{a.d}</div>
            </div>
          ))}
        </div>
      </Card>

      <SectionHead>Quick Start</SectionHead>
      <Card style={{ padding: 0, overflow: "hidden" }}>
        <pre style={{ margin: 0, fontSize: 12, color: c.ac, fontFamily: "'SF Mono', 'Cascadia Code', monospace", whiteSpace: "pre-wrap", lineHeight: "1.6", padding: 18 }}>{`surfit.execute(
    system="slack",
    action="post_message",
    params={"channel": "#general", "text": "Deploy complete"},
    agent_id="your-agent-id"
)
# Surfit evaluates wave level, applies your policy,
# and handles execution accordingly.`}</pre>
      </Card>
    </div>
  );
}

// ============================================================
// MAIN APP
// ============================================================
export default function SurfitApp() {
  const [view, setView] = useState("dashboard");
  const [execs, setExecs] = useState(INITIAL_EXECUTIONS);
  const [policies, setPolicies] = useState(MOCK_POLICIES);
  const [selExec, setSelExec] = useState(null);
  const [receiptModal, setReceiptModal] = useState(null);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [waveBreakdown, setWaveBreakdown] = useState(null);

  const pendingCount = execs.filter(e => e.status === "pending_approval").length;
  const nav = useCallback(v => { setSelExec(null); setView(v); }, []);
  const selE = useCallback(e => { setSelExec(e); setView("receipts"); }, []);

  const handleSimulateResult = useCallback((result) => {
    setExecs(prev => [result, ...prev]);
    if (result.status !== "pending_approval") {
      setReceiptModal(result);
    }
  }, []);

  const handleAction = useCallback((execId, newStatus) => {
    const now = new Date().toISOString();
    let updated = null;
    setExecs(prev => prev.map(e => {
      if (e.id !== execId) return e;
      updated = {
        ...e, status: newStatus, decidedBy: "operator", timestamp: now,
        proof: newStatus === "approved" ? { result: "executed", confirmed_at: now } :
               newStatus === "overridden" ? { override: true, operator_decision: true, at: now } :
               { rejected: true, at: now },
      };
      return updated;
    }));
    setTimeout(() => { if (updated) setReceiptModal(updated); }, 60);
  }, []);

  const handlePolicySave = useCallback((system, action, newWave) => {
    setPolicies(prev => prev.map(p =>
      p.system === system && p.action === action
        ? { ...p, wave: newWave, handling: WAVES[newWave]?.sub.toLowerCase() || p.handling }
        : p
    ));
  }, []);

  return (
    <div style={{
      display: "flex", height: "100vh", background: c.bg, color: c.tx,
      fontFamily: "'DM Sans', 'Segoe UI', -apple-system, system-ui, sans-serif",
      overflow: "hidden", fontSize: 14,
    }}>
      <Sidebar active={view} onNav={nav} pendingCount={pendingCount} />
      <div style={{ flex: 1, padding: "28px 40px", overflowY: "auto" }}>
        <div style={{ maxWidth: 920 }}>
          {view === "dashboard" && <DashboardView executions={execs} policies={policies} onAction={handleAction} onSelectExecution={selE} onNav={nav} onEditPolicy={setEditingPolicy} onSimulateResult={handleSimulateResult} setWaveBreakdown={setWaveBreakdown} />}
          {view === "policies" && <PolicyView policies={policies} onEditPolicy={setEditingPolicy} />}
          {view === "receipts" && <ReceiptView executions={execs} selected={selExec} />}
          {view === "onboarding" && <OnboardingView onComplete={() => nav("dashboard")} />}
          {view === "integration" && <IntegrationView />}
        </div>
      </div>
      <ReceiptModal execution={receiptModal} onClose={() => setReceiptModal(null)} />
      <PolicyEditDrawer policy={editingPolicy} onClose={() => setEditingPolicy(null)} onSave={handlePolicySave} />
      <WaveBreakdownModal execution={waveBreakdown} onClose={() => setWaveBreakdown(null)} />
    </div>
  );
}
