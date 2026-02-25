# SurFit × OpenClaw — Agent POC

OpenClaw agents that trigger bounded SurFit Waves. Agents run persistently and
dispatch discrete, auditable Wave containers for every execution — keeping
deterministic compute and probabilistic AI calls cleanly separated and verifiable.

---

## M14 validated path

**Finance agent only.** The marketing agent is a future placeholder and will not
run against M14 (see below).

```
npm run finance
```

Expected console output:

```
=== OpenClaw Finance Agent ===
Agent ID : openclaw_poc_agent_v1
Input    : ./data/sales.csv
Output   : ./outputs/report.md
==============================

Wave started: <wave_id>
Wave status: running
Wave status: running
Wave status: complete
Audit integrity_status: VALID
Audit policy_hash: <hash>
Audit agent_id: openclaw_poc_agent_v1
Output path: ./outputs/report.md

=== Finance Agent Complete ===
Wave ID  : <wave_id>
Integrity: VALID
Report   : ./outputs/report.md
==============================
```

---

## Repo structure

```
surfit-openclaw/
├── surfit-openclaw-tool.js        # shared tool wrapper (wave_start / wave_status / wave_audit)
├── agents/
│   ├── finance-agent.js           # ✅ M14 validated — openclaw_poc_agent_v1 → sales_report_v1
│   └── marketing-agent.js         # ⏳ future placeholder — not runnable in M14
├── data/
│   ├── sales.csv                  # Finance agent input (M14 schema: units, unit_price_usd)
│   └── marketing_snapshots/       # Marketing agent snapshot dir (future use)
├── outputs/                       # Wave-generated reports written here
└── package.json
```

---

## Prerequisites

- Node.js ≥ 22
- SurFit runtime API running and accessible on port 8010

---

## Environment variables

| Variable                   | Default                          | Description                        |
|----------------------------|----------------------------------|------------------------------------|
| `SURFIT_BASE_URL`          | `http://127.0.0.1:8010`          | SurFit runtime base URL            |
| `FINANCE_AGENT_ID`         | `openclaw_poc_agent_v1`          | Finance agent identity             |
| `FINANCE_INPUT_CSV`        | `./data/sales.csv`               | Input CSV path                     |
| `FINANCE_OUTPUT_REPORT`    | `./outputs/report.md`            | Output report path                 |

---

## Running

### 1. Start SurFit runtime

Ensure the SurFit API is running and listening on port 8010 before running any agent.

### 2. Finance Agent — Sales Report (M14 validated)

```bash
npm run finance
# or directly:
node agents/finance-agent.js
```

### 3. Marketing Agent — ⏳ not available in M14

```bash
npm run marketing
# → prints: "Marketing agent not available in M14 runtime"
```

The marketing agent (`openclaw_marketing_agent_v1 → marketing_digest_v1`) requires
a template and allowlist entry not yet present in the M14 runtime. The file is
preserved for when that support lands.

---

## Tool API

The shared wrapper exports three discrete tools for OpenClaw:

```js
const { wave_start, wave_status, wave_audit, runSurfitWave } = require("./surfit-openclaw-tool");

// Discrete tools (for OpenClaw tool registry)
await wave_start({ agent_id, wave_template_id, policy_version, intent, context_refs });
await wave_status({ wave_id });
await wave_audit({ wave_id });

// Full lifecycle convenience wrapper
await runSurfitWave(waveParams, approvalConfig);
```

---

## Agent authorization (M14)

| agent_id                         | wave_template_id       | Status         |
|----------------------------------|------------------------|----------------|
| `openclaw_poc_agent_v1`          | `sales_report_v1`      | ✅ M14 active  |
| `openclaw_marketing_agent_v1`    | `marketing_digest_v1`  | ⏳ pending     |

---

## sales.csv schema (M14 contract)

```
date, region, product, units, unit_price_usd, rep
```

`units` and `unit_price_usd` match the field names expected by the
`sales_report_v1` wave template in SurFit M14.
