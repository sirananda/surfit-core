/**
 * ⚠️  NOT SUPPORTED IN M14 RUNTIME
 *
 * This agent requires:
 *   - wave_template_id: marketing_digest_v1  (not yet registered in SurFit M14)
 *   - agent_id: openclaw_marketing_agent_v1  (not yet allowlisted in SurFit M14)
 *
 * File is preserved as a future placeholder.
 * Do not run directly until SurFit runtime adds the template + allowlist entry.
 * Use `npm run finance` for the M14-validated path.
 */

/**
 * agents/marketing-agent.js
 * OpenClaw Marketing Agent — triggers the marketing_digest_v1 SurFit Wave.
 *
 * Wave execution (inside SurFit):
 *   deterministic : fetch allowlisted RSS/URL sources, extract text, store raw
 *                   snapshots under ./data/marketing_snapshots/
 *   probabilistic : Claude clusters themes, summarizes, proposes angles + headlines
 *   output        : ./outputs/marketing_digest.md
 *
 * Agent identity: openclaw_marketing_agent_v1
 * Authorized wave: marketing_digest_v1
 *
 * Trigger modes:
 *   - Manual  : node agents/marketing-agent.js
 *   - Interval: set MARKETING_INTERVAL_MS env var (e.g. 1800000 = 30 min)
 *               node agents/marketing-agent.js --watch
 */

const { runSurfitWave } = require("../surfit-openclaw-tool");

const AGENT_ID         = process.env.MARKETING_AGENT_ID    ?? "openclaw_marketing_agent_v1";
const SNAPSHOT_DIR     = process.env.MARKETING_SNAPSHOT_DIR ?? "./data/marketing_snapshots";
const OUTPUT_DIGEST    = process.env.MARKETING_OUTPUT       ?? "./outputs/marketing_digest.md";
const INTERVAL_MS      = parseInt(process.env.MARKETING_INTERVAL_MS ?? "1800000", 10); // default 30 min

// Allowlisted public sources passed to the wave as context.
// SurFit wave executor fetches and snapshots these; the agent itself does not do I/O.
// Kept to 3 high-reliability feeds for demo stability — expand post-POC.
const SOURCES = [
  "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",  // NYT Tech — very stable
  "https://feeds.hbr.org/harvardbusiness",                         // HBR — very stable
  "https://techcrunch.com/feed/",                                  // TechCrunch native feed (feedburner deprecated)
];

async function run() {
  const runId = new Date().toISOString();
  console.log("=== OpenClaw Marketing Agent ===");
  console.log(`Agent ID : ${AGENT_ID}`);
  console.log(`Run at   : ${runId}`);
  console.log(`Sources  : ${SOURCES.length} feeds`);
  console.log(`Snapshots: ${SNAPSHOT_DIR}`);
  console.log(`Output   : ${OUTPUT_DIGEST}`);
  console.log("================================\n");

  const { waveId, audit } = await runSurfitWave(
    {
      agent_id:         AGENT_ID,
      wave_template_id: "marketing_digest_v1",
      policy_version:   "marketing_digest_policy_v1",
      intent:           "Fetch marketing sources, cluster themes, generate digest with headlines and angles",
      context_refs: {
        sources:              SOURCES,
        snapshot_dir:         SNAPSHOT_DIR,
        output_digest_path:   OUTPUT_DIGEST,
        run_id:               runId,
      },
    },
    {
      approved_by: "andreas@surfit.ai",
      note:        "Marketing agent scheduled run",
    }
  );

  console.log("\n=== Marketing Agent Complete ===");
  console.log(`Wave ID  : ${waveId}`);
  console.log(`Integrity: ${audit.integrity_status ?? "N/A"}`);
  console.log(`Digest   : ${audit.output_path ?? OUTPUT_DIGEST}`);
  console.log("================================\n");

  return { waveId, audit };
}

// ─── Interval / watch mode ────────────────────────────────────────────────────

async function watch() {
  console.log(`[Marketing Agent] Watch mode — running every ${INTERVAL_MS / 60_000} min\n`);

  // Run immediately on start, then on interval
  await run().catch((err) => console.error(`[Marketing Agent ERROR] ${err.message}`));

  setInterval(async () => {
    await run().catch((err) => console.error(`[Marketing Agent ERROR] ${err.message}`));
  }, INTERVAL_MS);
}

// ─── Entry point ──────────────────────────────────────────────────────────────

if (require.main === module) {
  const watchMode = process.argv.includes("--watch");

  if (watchMode) {
    watch().catch((err) => {
      console.error(`[Marketing Agent FATAL] ${err.message}`);
      process.exit(1);
    });
  } else {
    run().catch((err) => {
      console.error(`[Marketing Agent ERROR] ${err.message}`);
      process.exit(1);
    });
  }
}

module.exports = { run, watch };
