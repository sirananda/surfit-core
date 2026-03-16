const params = new URLSearchParams(window.location.search);
const accessKeyFromUrl = (params.get("k") || "").trim();
const accessKeyFromSession = (sessionStorage.getItem("surfit_tenant_access_key") || "").trim();
const CACHE_KEY = "surfit_tenant_dashboard_cache_v3";

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
  activeTab: "overview",
  atlasCategory: "All",
};

const els = {
  limitInput: document.getElementById("limitInput"),
  refreshBtn: document.getElementById("refreshBtn"),
  tenantDisplayName: document.getElementById("tenantDisplayName"),
  tenantIdLabel: document.getElementById("tenantIdLabel"),
  tenantLogoSlot: document.getElementById("tenantLogoSlot"),
  tenantLogo: document.getElementById("tenantLogo"),

  tabOverview: document.getElementById("tabOverview"),
  tabAtlas: document.getElementById("tabAtlas"),
  tabTrench: document.getElementById("tabTrench"),
  overviewView: document.getElementById("overviewView"),
  atlasView: document.getElementById("atlasView"),
  trenchView: document.getElementById("trenchView"),

  wavesStatus: document.getElementById("wavesStatus"),
  wavesList: document.getElementById("wavesList"),
  approvalsStatus: document.getElementById("approvalsStatus"),
  approvalsList: document.getElementById("approvalsList"),
  selectedWaveBadge: document.getElementById("selectedWaveBadge"),
  waveSummary: document.getElementById("waveSummary"),
  decisionsStatus: document.getElementById("decisionsStatus"),
  decisionsList: document.getElementById("decisionsList"),

  atlasStatus: document.getElementById("atlasStatus"),
  atlasCategories: document.getElementById("atlasCategories"),
  atlasActiveCategory: document.getElementById("atlasActiveCategory"),
  atlasWavesList: document.getElementById("atlasWavesList"),

  trenchStatus: document.getElementById("trenchStatus"),
  trenchList: document.getElementById("trenchList"),
  trenchSelectedWaveBadge: document.getElementById("trenchSelectedWaveBadge"),
  trenchWaveSummary: document.getElementById("trenchWaveSummary"),

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
  els.atlasStatus.textContent = message;
  els.trenchStatus.textContent = message;
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
    document.documentElement.style.setProperty("--bg-grad-b", state.theme.surface);
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

function isRetiredWave(w) {
  const status = String(w.status || "").toUpperCase();
  const approval = String(w.approval_status || "").toUpperCase();
  const decision = String(w.latest_decision || "").toUpperCase();

  if (["RETIRED", "ARCHIVED", "COMPLETED", "CLOSED", "DONE"].includes(status)) return true;
  if (["APPROVED", "REJECTED", "EXPIRED", "CANCELLED"].includes(approval)) return true;
  if (["ALLOW", "DENY"].includes(decision) && approval !== "PENDING") return true;
  return false;
}

function getWaveCategory(w) {
  const decision = String(w.latest_decision || "").toUpperCase();
  const action = String(w.action || "").toLowerCase();
  const risk = String(w.risk_level || "").toLowerCase();

  if (decision === "PENDING_APPROVAL") return "Approval Required";
  if (decision === "DENY") return "Denied";
  if (decision === "ALLOW") return "Allowed";
  if (action.includes("merge") || action.includes("pull_request")) return "GitHub Merge";
  if (risk === "high") return "High Risk";
  return "Other";
}

function computeMetrics() {
  const waves = state.waves;
  const approvals = state.approvals;
  const decisions = state.selectedWave ? state.selectedDecisions : [];

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

  const pendingApprovals = approvals.filter((a) => (a.approval_status || "").toUpperCase() === "PENDING").length;

  els.metricLength.textContent = String(total);
  els.metricHeight.textContent = height;
  els.metricDepth.textContent = state.selectedWave ? String(decisions.length || 0) : "-";
  els.metricFrequency.textContent = String(frequency);
  els.metricDrift.textContent = drift;
  els.metricSplash.textContent = String(pendingApprovals);
}

function saveCache() {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({
      ts: Date.now(),
      waves: state.waves,
      approvals: state.approvals,
      selectedWaveId: state.selectedWave?.wave_id || null,
    }));
  } catch (_err) {
  }
}

function hydrateFromCache() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.waves) || !Array.isArray(data.approvals)) return;

    state.waves = data.waves;
    state.approvals = data.approvals;
    if (data.selectedWaveId) {
      state.selectedWave = state.waves.find((w) => w.wave_id === data.selectedWaveId) || null;
    }

    renderWaves();
    renderApprovals();
    renderAtlas();
    renderTrench();
    computeMetrics();

    els.wavesStatus.textContent = `${state.waves.length} cached`;
    els.approvalsStatus.textContent = `${state.approvals.length} cached`;
  } catch (_err) {
  }
}

function renderWaves() {
  const waves = state.waves;
  if (!waves.length) {
    state.selectedWave = null;
    state.selectedDecisions = [];
    els.selectedWaveBadge.textContent = "No wave selected";
    els.waveSummary.textContent = "No waves for this tenant yet.";
    els.decisionsList.innerHTML = "";
    els.decisionsStatus.textContent = "0 decisions";
    els.wavesList.innerHTML = '<li class="item">No waves found.</li>';
    computeMetrics();
    return;
  }

  els.wavesList.innerHTML = waves.map((w) => `
    <li class="item">
      <button class="link-btn" data-wave-id="${esc(w.wave_id)}">${esc(w.wave_id)}</button>
      <div class="meta">
        <span>category: ${esc(getWaveCategory(w))}</span>
        <span>system/action: ${esc(w.system || "-")}/${esc(w.action || "-")}</span>
        <span>wave status: ${esc(w.status || "-")}</span>
        <span class="${clsDecision(w.latest_decision)}">latest decision: ${esc(w.latest_decision || "-")}</span>
        <span>approval status: ${esc(w.approval_status || "-")}</span>
        <span>created: ${esc(fmtTime(w.created_at))}</span>
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
      saveCache();
    });
  });

  wireArtifactButtons(els.wavesList);
}

async function loadWaves() {
  els.wavesStatus.textContent = "Loading";
  try {
    const payload = await getJson(`/api/tenant/dashboard/waves/recent?limit=${state.limit}`);
    const waves = Array.isArray(payload.waves) ? payload.waves : [];
    state.waves = waves;
    els.wavesStatus.textContent = `${waves.length} waves`;

    if (state.selectedWave && !state.waves.some((w) => w.wave_id === state.selectedWave.wave_id)) {
      state.selectedWave = null;
      state.selectedDecisions = [];
      els.selectedWaveBadge.textContent = "No wave selected";
      els.waveSummary.textContent = "Select a wave to inspect lifecycle and decisions.";
      els.decisionsStatus.textContent = "Idle";
      els.decisionsList.innerHTML = "";
    }

    renderWaves();
    renderAtlas();
    renderTrench();
    computeMetrics();
    saveCache();
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
      `category: ${getWaveCategory(wave)}`,
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

function renderApprovals() {
  const approvals = state.approvals;
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
}

async function loadApprovals() {
  els.approvalsStatus.textContent = "Loading";
  try {
    const payload = await getJson(`/api/tenant/dashboard/approvals/recent?limit=${state.limit}`);
    state.approvals = Array.isArray(payload.approvals) ? payload.approvals : [];
    renderApprovals();
    computeMetrics();
    saveCache();
  } catch (error) {
    els.approvalsStatus.textContent = `Error: ${error.message}`;
  }
}

function renderAtlas() {
  const categoryCounts = new Map();
  state.waves.forEach((w) => {
    const c = getWaveCategory(w);
    categoryCounts.set(c, (categoryCounts.get(c) || 0) + 1);
  });

  const categories = ["All", ...Array.from(categoryCounts.keys()).sort()];
  if (!categories.includes(state.atlasCategory)) {
    state.atlasCategory = "All";
  }

  els.atlasStatus.textContent = `${state.waves.length} waves`;
  els.atlasActiveCategory.textContent = state.atlasCategory;

  els.atlasCategories.innerHTML = categories.map((c) => {
    const count = c === "All" ? state.waves.length : (categoryCounts.get(c) || 0);
    const active = c === state.atlasCategory ? "active" : "";
    return `
      <article class="category-card ${active}" data-category="${esc(c)}">
        <h3>${esc(c)}</h3>
        <p>${count} wave${count === 1 ? "" : "s"}</p>
      </article>
    `;
  }).join("");

  els.atlasCategories.querySelectorAll("[data-category]").forEach((el) => {
    el.addEventListener("click", () => {
      state.atlasCategory = el.getAttribute("data-category") || "All";
      renderAtlas();
    });
  });

  const filtered = state.atlasCategory === "All"
    ? state.waves
    : state.waves.filter((w) => getWaveCategory(w) === state.atlasCategory);

  els.atlasWavesList.innerHTML = filtered.length
    ? filtered.map((w) => `
      <li class="item">
        <strong>${esc(w.wave_id)}</strong>
        <div class="meta">
          <span>category: ${esc(getWaveCategory(w))}</span>
          <span>system/action: ${esc(w.system || "-")}/${esc(w.action || "-")}</span>
          <span class="${clsDecision(w.latest_decision)}">decision: ${esc(w.latest_decision || "-")}</span>
          <span>status: ${esc(w.status || "-")}</span>
          <span>created: ${esc(fmtTime(w.created_at))}</span>
        </div>
      </li>
    `).join("")
    : '<li class="item">No waves in this category.</li>';
}

function renderTrench() {
  const retired = state.waves.filter(isRetiredWave);
  els.trenchStatus.textContent = `${retired.length} retired`;

  if (!retired.length) {
    els.trenchList.innerHTML = '<li class="item">No retired waves yet.</li>';
    els.trenchSelectedWaveBadge.textContent = "No wave selected";
    els.trenchWaveSummary.textContent = "Select a retired wave to inspect lifecycle details.";
    return;
  }

  els.trenchList.innerHTML = retired.map((w) => `
    <li class="item">
      <button class="link-btn" data-trench-wave-id="${esc(w.wave_id)}">${esc(w.wave_id)}</button>
      <div class="meta">
        <span>category: ${esc(getWaveCategory(w))}</span>
        <span>wave status: ${esc(w.status || "-")}</span>
        <span class="${clsDecision(w.latest_decision)}">latest decision: ${esc(w.latest_decision || "-")}</span>
        <span>approval status: ${esc(w.approval_status || "-")}</span>
        <span>updated: ${esc(fmtTime(w.updated_at || w.last_event_at))}</span>
      </div>
      ${artifactButton(w.artifact_id)}
    </li>
  `).join("");

  els.trenchList.querySelectorAll("[data-trench-wave-id]").forEach((el) => {
    el.addEventListener("click", () => {
      const waveId = el.getAttribute("data-trench-wave-id");
      const w = retired.find((r) => r.wave_id === waveId);
      if (!w) return;
      els.trenchSelectedWaveBadge.textContent = w.wave_id;
      els.trenchWaveSummary.textContent = [
        `wave_id: ${w.wave_id || "-"}`,
        `category: ${getWaveCategory(w)}`,
        `system/action: ${w.system || "-"}/${w.action || "-"}`,
        `status: ${w.status || "-"}`,
        `latest decision: ${w.latest_decision || "-"}`,
        `approval status: ${w.approval_status || "-"}`,
        `artifact_id: ${w.artifact_id || "-"}`,
        `created: ${fmtTime(w.created_at)}`,
        `updated: ${fmtTime(w.updated_at || w.last_event_at)}`,
      ].join("\n");
    });
  });

  wireArtifactButtons(els.trenchList);
}

function setActiveTab(name) {
  state.activeTab = name;

  const map = {
    overview: { tab: els.tabOverview, view: els.overviewView },
    atlas: { tab: els.tabAtlas, view: els.atlasView },
    trench: { tab: els.tabTrench, view: els.trenchView },
  };

  Object.keys(map).forEach((key) => {
    const active = key === name;
    map[key].tab.classList.toggle("active", active);
    map[key].tab.setAttribute("aria-selected", active ? "true" : "false");
    map[key].view.classList.toggle("active", active);
  });
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
els.tabOverview.addEventListener("click", () => setActiveTab("overview"));
els.tabAtlas.addEventListener("click", () => setActiveTab("atlas"));
els.tabTrench.addEventListener("click", () => setActiveTab("trench"));

(async () => {
  const ok = await loadContext();
  if (!ok) return;
  hydrateFromCache();
  await refreshAll();
})();
