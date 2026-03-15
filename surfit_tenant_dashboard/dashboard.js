const params = new URLSearchParams(window.location.search);
const accessKeyFromUrl = (params.get("k") || "").trim();
const accessKeyFromSession = (sessionStorage.getItem("surfit_tenant_access_key") || "").trim();

const state = {
  accessKey: accessKeyFromUrl || accessKeyFromSession,
  tenantId: null,
  displayName: null,
  logoUrl: null,
  theme: {},
  limit: 20,
  waves: [],
  approvals: [],
  selectedWave: null,
  selectedDecisions: [],
};

const els = {
  limitInput: document.getElementById("limitInput"),
  refreshBtn: document.getElementById("refreshBtn"),
  tenantDisplayName: document.getElementById("tenantDisplayName"),
  tenantIdLabel: document.getElementById("tenantIdLabel"),
  tenantLogoSlot: document.getElementById("tenantLogoSlot"),
  tenantLogo: document.getElementById("tenantLogo"),
  wavesStatus: document.getElementById("wavesStatus"),
  wavesList: document.getElementById("wavesList"),
  approvalsStatus: document.getElementById("approvalsStatus"),
  approvalsList: document.getElementById("approvalsList"),
  selectedWaveBadge: document.getElementById("selectedWaveBadge"),
  waveSummary: document.getElementById("waveSummary"),
  decisionsStatus: document.getElementById("decisionsStatus"),
  decisionsList: document.getElementById("decisionsList"),
  artifactDialog: document.getElementById("artifactDialog"),
  artifactTitle: document.getElementById("artifactTitle"),
  artifactBody: document.getElementById("artifactBody"),
  metricLength: document.getElementById("metricLength"),
  metricHeight: document.getElementById("metricHeight"),
  metricDepth: document.getElementById("metricDepth"),
  metricFrequency: document.getElementById("metricFrequency"),
  metricDrift: document.getElementById("metricDrift"),
  metricSplash: document.getElementById("metricSplash"),
};

function esc(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function clsDecision(v) {
  if (v === "ALLOW") return "ok";
  if (v === "DENY") return "bad";
  if (v === "PENDING_APPROVAL") return "warn";
  return "";
}

function fmtTime(v) {
  if (!v) return "-";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? String(v) : d.toLocaleString();
}

function authHeaders() {
  return state.accessKey ? { "X-Surfit-Tenant-Access": state.accessKey } : {};
}

async function getJson(url) {
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

function showFatal(message) {
  els.wavesStatus.textContent = message;
  els.approvalsStatus.textContent = message;
  els.decisionsStatus.textContent = message;
  els.waveSummary.textContent = message;
}

function applyBranding(context) {
  state.tenantId = context.tenant_id;
  state.displayName = context.display_name || context.tenant_id;
  state.logoUrl = context.logo_url || null;
  state.theme = context.theme || {};

  els.tenantDisplayName.textContent = `${state.displayName} Dashboard`;
  els.tenantIdLabel.textContent = `tenant: ${state.tenantId}`;

  if (state.logoUrl) {
    els.tenantLogo.src = state.logoUrl;
    els.tenantLogo.classList.remove("hidden");
    els.tenantLogoSlot.classList.add("hidden");
  } else {
    els.tenantLogo.classList.add("hidden");
    els.tenantLogoSlot.classList.remove("hidden");
  }

  if (state.theme?.accent) {
    document.documentElement.style.setProperty("--brand", state.theme.accent);
  }
  if (state.theme?.surface) {
    document.documentElement.style.setProperty("--bg", state.theme.surface);
  }
}

function artifactButton(artifactId) {
  if (!artifactId) return "";
  return `<div class=\"link-row\"><button class=\"link-btn\" data-artifact-id=\"${esc(artifactId)}\">View artifact ${esc(artifactId)}</button></div>`;
}

function wireArtifactButtons(root) {
  root.querySelectorAll("[data-artifact-id]").forEach((btn) => {
    btn.addEventListener("click", async (event) => {
      const artifactId = event.currentTarget.getAttribute("data-artifact-id");
      if (!artifactId) return;
      els.artifactTitle.textContent = `Artifact ${artifactId}`;
      els.artifactBody.textContent = "Loading...";
      els.artifactDialog.showModal();
      try {
        const payload = await getJson(`/api/tenant/dashboard/artifacts/${encodeURIComponent(artifactId)}`);
        els.artifactBody.textContent = JSON.stringify(payload, null, 2);
      } catch (error) {
        els.artifactBody.textContent = `Artifact fetch failed: ${error.message}`;
      }
    });
  });
}

function computeMetrics() {
  const waves = state.waves;
  const approvals = state.approvals;
  const decisions = state.selectedDecisions;

  const total = waves.length;
  const nonAllow = waves.filter((w) => (w.latest_decision || "") !== "ALLOW").length;
  const height = total ? `${Math.round((nonAllow / total) * 100)}%` : "0%";

  const dayAgo = Date.now() - (24 * 60 * 60 * 1000);
  const frequency = waves.filter((w) => {
    const t = Date.parse(w.created_at || "");
    return !Number.isNaN(t) && t >= dayAgo;
  }).length;

  const driftNumerator = waves.filter((w) => {
    const code = w.latest_reason_code || "";
    return code && code !== "POLICY_ALLOW";
  }).length;
  const drift = total ? `${Math.round((driftNumerator / total) * 100)}%` : "0%";

  const pendingApprovals = approvals.filter((a) => (a.approval_status || "").toUpperCase() === "pending".toUpperCase()).length;

  els.metricLength.textContent = String(total);
  els.metricHeight.textContent = height;
  els.metricDepth.textContent = String(decisions.length || 0);
  els.metricFrequency.textContent = String(frequency);
  els.metricDrift.textContent = drift;
  els.metricSplash.textContent = String(pendingApprovals);
}

async function loadWaves() {
  els.wavesStatus.textContent = "Loading";
  els.wavesList.innerHTML = "";
  try {
    const payload = await getJson(`/api/tenant/dashboard/waves/recent?limit=${state.limit}`);
    const waves = Array.isArray(payload.waves) ? payload.waves : [];
    state.waves = waves;
    els.wavesStatus.textContent = `${waves.length} waves`;

    if (!waves.length) {
      state.selectedWave = null;
      state.selectedDecisions = [];
      els.selectedWaveBadge.textContent = "No wave selected";
      els.waveSummary.textContent = "No waves for this tenant yet.";
      els.decisionsList.innerHTML = "";
      els.decisionsStatus.textContent = "0 decisions";
      computeMetrics();
      return;
    }

    els.wavesList.innerHTML = waves.map((w) => `
      <li class="item">
        <button class="link-btn" data-wave-id="${esc(w.wave_id)}">${esc(w.wave_id)}</button>
        <div class="meta">
          <span>system/action: ${esc(w.system || "-")}/${esc(w.action || "-")}</span>
          <span>wave status: ${esc(w.status || "-")}</span>
          <span class="${clsDecision(w.latest_decision)}">latest decision: ${esc(w.latest_decision || "-")}</span>
          <span>approval status: ${esc(w.approval_status || "-")}</span>
          <span>created: ${esc(fmtTime(w.created_at))}</span>
          <span>updated: ${esc(fmtTime(w.updated_at || w.last_event_at))}</span>
        </div>
        ${artifactButton(w.artifact_id)}
      </li>
    `).join("");

    els.wavesList.querySelectorAll("[data-wave-id]").forEach((el) => {
      el.addEventListener("click", async (event) => {
        const waveId = event.currentTarget.getAttribute("data-wave-id");
        const wave = state.waves.find((item) => item.wave_id === waveId) || null;
        state.selectedWave = wave;
        els.selectedWaveBadge.textContent = waveId || "No wave selected";
        await loadDecisionsForSelected();
      });
    });

    wireArtifactButtons(els.wavesList);

    if (!state.selectedWave || !state.waves.some((w) => w.wave_id === state.selectedWave.wave_id)) {
      state.selectedWave = state.waves[0];
      els.selectedWaveBadge.textContent = state.selectedWave.wave_id;
      await loadDecisionsForSelected();
    }

    computeMetrics();
  } catch (error) {
    els.wavesStatus.textContent = `Error: ${error.message}`;
  }
}

async function loadDecisionsForSelected() {
  const wave = state.selectedWave;
  if (!wave?.wave_id) {
    state.selectedDecisions = [];
    els.waveSummary.textContent = "Select a wave to inspect lifecycle and decisions.";
    els.decisionsStatus.textContent = "0 decisions";
    els.decisionsList.innerHTML = "";
    computeMetrics();
    return;
  }

  els.decisionsStatus.textContent = "Loading";
  try {
    const payload = await getJson(`/api/tenant/dashboard/waves/${encodeURIComponent(wave.wave_id)}/decisions`);
    const decisions = Array.isArray(payload.decisions) ? payload.decisions : [];
    state.selectedDecisions = decisions;

    els.waveSummary.textContent = [
      `wave_id: ${payload.wave_id || "-"}`,
      `tenant_id: ${payload.tenant_id || "-"}`,
      `system/action: ${wave.system || "-"}/${wave.action || "-"}`,
      `wave status: ${wave.status || "-"}`,
      `latest decision: ${wave.latest_decision || "-"}`,
      `approval status: ${wave.approval_status || "-"}`,
      `artifact_id: ${wave.artifact_id || "-"}`,
      `created: ${fmtTime(payload.created_at || wave.created_at)}`,
      `updated: ${fmtTime(payload.updated_at || wave.updated_at || wave.last_event_at)}`,
    ].join("\n");

    els.decisionsStatus.textContent = `${decisions.length} decisions`;
    els.decisionsList.innerHTML = decisions.length
      ? decisions.map((d) => `
        <li class="item">
          <strong class="${clsDecision(d.decision)}">${esc(d.decision || "-")}</strong>
          <div class="meta">
            <span>reason: ${esc(d.reason_code || "-")}</span>
            <span>policy ref: ${esc(d.policy_reference || d.policy_manifest_hash || "-")}</span>
            <span>approval: ${esc(d.approval_request_id || "-")}</span>
            <span>time: ${esc(fmtTime(d.timestamp || d.created_at))}</span>
          </div>
          ${artifactButton(d.artifact_id)}
        </li>
      `).join("")
      : '<li class="item">No decisions recorded.</li>';

    wireArtifactButtons(els.decisionsList);
    computeMetrics();
  } catch (error) {
    els.decisionsStatus.textContent = `Error: ${error.message}`;
  }
}

async function loadApprovals() {
  els.approvalsStatus.textContent = "Loading";
  els.approvalsList.innerHTML = "";
  try {
    const payload = await getJson(`/api/tenant/dashboard/approvals/recent?limit=${state.limit}`);
    const approvals = Array.isArray(payload.approvals) ? payload.approvals : [];
    state.approvals = approvals;
    els.approvalsStatus.textContent = `${approvals.length} approvals`;

    els.approvalsList.innerHTML = approvals.length
      ? approvals.map((a) => `
        <li class="item">
          <strong>${esc(a.approval_request_id || "-")}</strong>
          <div class="meta">
            <span>wave_id: ${esc(a.wave_id || a.linked_wave_id || "-")}</span>
            <span>approval status: ${esc(a.approval_status || "-")}</span>
            <span>latest decision: ${esc(a.latest_decision || "-")}</span>
            <span>system/action: ${esc(a.system || "-")}/${esc(a.action || "-")}</span>
            <span>created: ${esc(fmtTime(a.created_at))}</span>
            <span>updated: ${esc(fmtTime(a.updated_at || a.last_event_at))}</span>
          </div>
          ${artifactButton(a.artifact_id)}
        </li>
      `).join("")
      : '<li class="item">No approvals found.</li>';

    wireArtifactButtons(els.approvalsList);
    computeMetrics();
  } catch (error) {
    els.approvalsStatus.textContent = `Error: ${error.message}`;
  }
}

async function loadContext() {
  if (!state.accessKey) {
    showFatal("Missing dashboard access key. Open with ?k=<tenant_dashboard_key>");
    return false;
  }

  if (accessKeyFromUrl) {
    sessionStorage.setItem("surfit_tenant_access_key", accessKeyFromUrl);
  }

  try {
    const payload = await getJson("/api/tenant/dashboard/context");
    applyBranding(payload);

    if (accessKeyFromUrl) {
      const cleanUrl = `${window.location.pathname}`;
      window.history.replaceState({}, document.title, cleanUrl);
    }
    return true;
  } catch (error) {
    showFatal(`Dashboard access denied: ${error.message}`);
    return false;
  }
}

async function refreshAll() {
  state.limit = Math.max(1, Math.min(100, Number(els.limitInput.value) || 20));
  els.limitInput.value = String(state.limit);
  await Promise.all([loadWaves(), loadApprovals()]);
}

els.refreshBtn.addEventListener("click", refreshAll);
els.limitInput.addEventListener("keydown", (e) => { if (e.key === "Enter") refreshAll(); });

(async () => {
  const ok = await loadContext();
  if (!ok) return;
  await refreshAll();
})();

(function surfitWaveAtlasTabFix() {
  if (window.__surfitWaveAtlasTabFixApplied) return;
  window.__surfitWaveAtlasTabFixApplied = true;

  function applyTab(mode) {
    const overviewBtn = document.getElementById("tabOverview");
    const atlasBtn = document.getElementById("tabAtlas");
    const overviewSection = document.getElementById("overviewSection");
    const atlasSection = document.getElementById("atlasSection");
    if (!overviewBtn || !atlasBtn || !overviewSection || !atlasSection) return;

    const showOverview = mode !== "atlas";
    overviewBtn.classList.toggle("active", showOverview);
    atlasBtn.classList.toggle("active", !showOverview);
    overviewSection.classList.toggle("hidden", !showOverview);
    atlasSection.classList.toggle("hidden", showOverview);
  }

  function bind() {
    const overviewBtn = document.getElementById("tabOverview");
    const atlasBtn = document.getElementById("tabAtlas");
    if (!overviewBtn || !atlasBtn) return;
    overviewBtn.addEventListener("click", function () { applyTab("overview"); }, { passive: true });
    atlasBtn.addEventListener("click", function () { applyTab("atlas"); }, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind, { once: true });
  } else {
    bind();
  }
  setTimeout(bind, 300);
})();


(function surfitAtlasForcePatch() {
  if (window.__surfitAtlasForcePatchApplied) return;
  window.__surfitAtlasForcePatchApplied = true;

  function ensureAtlasSection() {
    let atlas = document.getElementById("atlasSection");
    if (atlas) return atlas;

    const overview = document.getElementById("overviewSection");
    if (!overview || !overview.parentElement) return null;

    atlas = document.createElement("section");
    atlas.id = "atlasSection";
    atlas.className = "section hidden";
    atlas.innerHTML = `
      <div class="atlas-grid">
        <section class="panel">
          <header class="panel-head"><h2>Observed Wave Types</h2><span id="atlasStatus" class="status">0 wave types</span></header>
          <ul id="atlasList" class="list"><li class="item">No wave types observed yet.</li></ul>
        </section>
        <section class="panel">
          <header class="panel-head"><h2>Future Wave Templates</h2></header>
          <ul class="list">
            <li class="item"><strong>GitHub Pull Request Merge Wave</strong></li>
            <li class="item"><strong>Terraform Apply Wave</strong></li>
            <li class="item"><strong>Slack Channel Invite Wave</strong></li>
          </ul>
        </section>
      </div>
    `;
    overview.parentElement.appendChild(atlas);
    return atlas;
  }

  function renderAtlasFromWaves() {
    const atlasList = document.getElementById("atlasList");
    const atlasStatus = document.getElementById("atlasStatus");
    if (!atlasList || !atlasStatus || !window.state || !Array.isArray(window.state.waves)) return;

    const map = new Map();
    for (const w of window.state.waves) {
      const system = w.system || "unknown_system";
      const action = w.action || "unknown_action";
      const k = system + "__" + action;
      const t = w.last_event_at || w.updated_at || w.created_at || null;
      if (!map.has(k)) map.set(k, { system, action, count: 0, last: t });
      const row = map.get(k);
      row.count += 1;
      if (t && (!row.last || new Date(t) > new Date(row.last))) row.last = t;
    }

    const rows = Array.from(map.values()).sort((a,b)=>b.count-a.count);
    atlasStatus.textContent = rows.length + " wave types";
    if (!rows.length) {
      atlasList.innerHTML = '<li class="item">No wave types observed yet.</li>';
      return;
    }

    atlasList.innerHTML = rows.map(r => `
      <li class="item">
        <strong>${r.system} — ${r.action}</strong>
        <div class="meta">
          <span>Observed: ${r.count} waves</span>
          <span>Last observed: ${r.last ? new Date(r.last).toLocaleString() : "-"}</span>
        </div>
      </li>
    `).join("");
  }

  function activate(mode) {
    const overviewBtn = document.getElementById("tabOverview");
    const atlasBtn = document.getElementById("tabAtlas");
    const overview = document.getElementById("overviewSection");
    const atlas = ensureAtlasSection();
    if (!overviewBtn || !atlasBtn || !overview || !atlas) return;

    const showOverview = mode !== "atlas";
    overview.classList.toggle("hidden", !showOverview);
    atlas.classList.toggle("hidden", showOverview);
    overviewBtn.classList.toggle("active", showOverview);
    atlasBtn.classList.toggle("active", !showOverview);

    if (!showOverview) renderAtlasFromWaves();
  }

  function bind() {
    const overviewBtn = document.getElementById("tabOverview");
    const atlasBtn = document.getElementById("tabAtlas");
    if (!overviewBtn || !atlasBtn) return;
    overviewBtn.onclick = () => activate("overview");
    atlasBtn.onclick = () => activate("atlas");
    ensureAtlasSection();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind, { once: true });
  } else {
    bind();
  }
  setTimeout(bind, 200);
  setTimeout(bind, 800);
})();

