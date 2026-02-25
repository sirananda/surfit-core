/**
 * surfit-openclaw-tool.js
 * OpenClaw Node.js tool wrapper for SurFit wave lifecycle manager.
 *
 * Exports three discrete tool functions for OpenClaw agents:
 *   wave_start()   – start a wave (requires agent_id)
 *   wave_status()  – poll wave status
 *   wave_audit()   – fetch audit export after completion
 *
 * Also exports runSurfitWave() as a full lifecycle convenience wrapper.
 */

const BASE_URL = process.env.SURFIT_BASE_URL ?? "http://127.0.0.1:8010";

// ─── Config ───────────────────────────────────────────────────────────────────

const POLL_INITIAL_MS = 2_000;
const POLL_BACKOFF_MS = 5_000;
const POLL_INITIAL_N  = 5;
const HARD_TIMEOUT_MS = 180_000;
const RETRYABLE_STATUS = new Set([408, 429, 500, 502, 503, 504]);

// ─── Utilities ────────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jitter(ms, spread = 300) {
  const delta = Math.floor(Math.random() * (spread * 2 + 1)) - spread;
  return Math.max(0, ms + delta);
}

/**
 * Fetch with exponential backoff retry for transient errors only.
 * Retries: network errors + HTTP 408/429/5xx.
 * Throws immediately on all other HTTP errors.
 */
async function fetchWithRetry(url, options = {}, maxRetries = 4) {
  let attempt = 0;

  while (true) {
    attempt += 1;
    let response;

    try {
      response = await fetch(url, options);
    } catch (err) {
      if (attempt > maxRetries) throw err;
      const backoff = Math.min(1_000 * (2 ** (attempt - 1)), 8_000);
      console.warn(`[retry ${attempt}/${maxRetries}] network error: ${err.message}; retrying in ${backoff}ms`);
      await sleep(backoff);
      continue;
    }

    if (response.ok) return response;

    if (RETRYABLE_STATUS.has(response.status)) {
      if (attempt > maxRetries) {
        throw new Error(`HTTP ${response.status} after ${maxRetries} retries on ${url}`);
      }
      const backoff = Math.min(1_000 * (2 ** (attempt - 1)), 8_000);
      console.warn(`[retry ${attempt}/${maxRetries}] HTTP ${response.status}; retrying in ${backoff}ms`);
      await sleep(backoff);
      continue;
    }

    let body = "";
    try { body = await response.text(); } catch (_) {}
    throw new Error(`HTTP ${response.status} on ${url}: ${body}`);
  }
}

// ─── Tool: wave_start ─────────────────────────────────────────────────────────

/**
 * Start a SurFit wave.
 *
 * @param {object} params
 * @param {string} params.agent_id          – required; must be allowlisted for wave_template_id
 * @param {string} params.wave_template_id  – e.g. "sales_report_v1"
 * @param {string} params.policy_version    – e.g. "sales_report_policy_v1"
 * @param {string} params.intent            – human-readable description of run intent
 * @param {object} params.context_refs      – input/output paths and any extra context
 * @returns {object} SurFit start response (includes wave_id)
 */
async function wave_start({ agent_id, wave_template_id, policy_version, intent, context_refs }) {
  if (!agent_id) throw new Error("wave_start: agent_id is required");

  const res = await fetchWithRetry(`${BASE_URL}/api/waves/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent_id, wave_template_id, policy_version, intent, context_refs }),
  });
  return res.json();
}

// ─── Tool: wave_status ────────────────────────────────────────────────────────

/**
 * Get current status of a running wave.
 *
 * @param {object} params
 * @param {string} params.wave_id
 * @returns {object} { status, approval_request_id?, error? }
 */
async function wave_status({ wave_id }) {
  if (!wave_id) throw new Error("wave_status: wave_id is required");

  const res = await fetchWithRetry(`${BASE_URL}/api/waves/${wave_id}/status`);
  return res.json();
}

// ─── Tool: wave_audit ─────────────────────────────────────────────────────────

/**
 * Fetch audit export for a completed wave.
 *
 * @param {object} params
 * @param {string} params.wave_id
 * @returns {object} { integrity_status, policy_hash, agent_id, output_path, events[] }
 */
async function wave_audit({ wave_id }) {
  if (!wave_id) throw new Error("wave_audit: wave_id is required");

  const res = await fetchWithRetry(`${BASE_URL}/api/waves/${wave_id}/audit/export`);
  return res.json();
}

// ─── Internal: approval (compatibility shim, not used in default v1 flow) ─────

async function _approveWave(approvalRequestId, { approved_by, note }) {
  const res = await fetchWithRetry(`${BASE_URL}/api/approvals/${approvalRequestId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved_by, note }),
  });
  return res.json();
}

// ─── Lifecycle Wrapper ────────────────────────────────────────────────────────

/**
 * Full wave lifecycle: start → poll → (approve if needed) → complete → audit.
 *
 * Default v1 waves complete without approval. Approval logic is retained as a
 * compatibility shim for any future templates that require it.
 *
 * @param {object} waveParams      – passed directly to wave_start (must include agent_id)
 * @param {object} approvalConfig  – { approved_by, note } used only if needs_approval occurs
 * @returns {{ waveId: string, audit: object }}
 */
async function runSurfitWave(waveParams, approvalConfig = {}) {
  const approved_by = approvalConfig.approved_by ?? "andreas@surfit.ai";
  const note        = approvalConfig.note ?? "POC approval";
  const deadline    = Date.now() + HARD_TIMEOUT_MS;
  const approvedIds = new Set();

  // 1. Start
  const startResult = await wave_start(waveParams);
  const waveId = startResult.wave_id ?? startResult.id;
  if (!waveId) throw new Error(`Start response missing wave_id: ${JSON.stringify(startResult)}`);
  console.log(`Wave started: ${waveId}`);

  // 2. Poll
  let pollCount = 0;

  while (true) {
    if (Date.now() > deadline) {
      throw new Error(`Hard timeout (${HARD_TIMEOUT_MS / 1000}s) for wave ${waveId}`);
    }

    const statusData  = await wave_status({ wave_id: waveId });
    const status      = statusData.status;
    const approvalId  = statusData.approval_request_id ?? null;

    // Fast-fail: server flagged needs_approval but gave us nothing to act on.
    if (status === "needs_approval" && !approvalId) {
      throw new Error(`Wave ${waveId}: status is needs_approval but approval_request_id is null`);
    }

    // Approve if explicitly required OR if approval_request_id appears during running
    // (defensive guard against state-machine lag in SurFit runtime).
    if ((status === "needs_approval" || (status === "running" && approvalId)) && approvalId) {
      if (status === "needs_approval") {
        console.log(`Wave status: needs_approval (${approvalId})`);
      } else {
        // Compat path: status still "running" but approval_request_id already set
        console.log(`Wave status: running (approval_request_id present; approving compat)`);
      }
      if (!approvedIds.has(approvalId)) {
        console.log(`Approving as ${approved_by}`);
        await _approveWave(approvalId, { approved_by, note });
        approvedIds.add(approvalId);
      }
    } else if (status === "running") {
      console.log("Wave status: running");
    } else if (status === "complete") {
      console.log("Wave status: complete");

      // 3. Audit
      const audit      = await wave_audit({ wave_id: waveId });
      const integrity  = audit.integrity_status ?? "N/A";
      const policyHash = audit.policy_hash ?? "N/A";
      const agentId    = audit.agent_id ?? waveParams.agent_id ?? "N/A";
      const outputPath = audit.output_path ?? waveParams?.context_refs?.output_report_path ?? "N/A";

      console.log(`Audit integrity_status: ${integrity}`);
      console.log(`Audit policy_hash: ${policyHash}`);
      console.log(`Audit agent_id: ${agentId}`);
      console.log(`Output path: ${outputPath}`);

      return { waveId, audit };
    } else if (status === "failed") {
      // Support both nested { error: { code, message, node } } and flat { error_code, error_message, error_node }
      const err = statusData.error ?? {
        code:    statusData.error_code,
        message: statusData.error_message,
        node:    statusData.error_node,
      };
      throw new Error(
        `Wave ${waveId} failed — code: ${err.code ?? "N/A"}, node: ${err.node ?? "N/A"}, message: ${err.message ?? "N/A"}`
      );
    } else {
      console.warn(`Unknown wave status "${status}"`);
    }

    pollCount += 1;
    const baseInterval = pollCount <= POLL_INITIAL_N ? POLL_INITIAL_MS : POLL_BACKOFF_MS;
    await sleep(jitter(baseInterval, 300));
  }
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { wave_start, wave_status, wave_audit, runSurfitWave };
