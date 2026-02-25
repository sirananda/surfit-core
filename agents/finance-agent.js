/**
 * agents/finance-agent.js
 * OpenClaw Finance Agent — triggers the sales_report_v1 SurFit Wave.
 *
 * Wave execution (inside SurFit):
 *   deterministic : parse CSV, compute revenue totals / net / margin
 *   probabilistic : Claude generates narrative summary, anomalies, open questions
 *   output        : ./outputs/report.md
 *
 * Agent identity: openclaw_poc_agent_v1
 * Authorized wave: sales_report_v1
 */

const { runSurfitWave } = require("../surfit-openclaw-tool");

const AGENT_ID        = process.env.FINANCE_AGENT_ID ?? "openclaw_poc_agent_v1";
const INPUT_CSV       = process.env.FINANCE_INPUT_CSV ?? "./data/sales.csv";
const OUTPUT_REPORT   = process.env.FINANCE_OUTPUT_REPORT ?? "./outputs/report.md";

async function run() {
  console.log("=== OpenClaw Finance Agent ===");
  console.log(`Agent ID : ${AGENT_ID}`);
  console.log(`Input    : ${INPUT_CSV}`);
  console.log(`Output   : ${OUTPUT_REPORT}`);
  console.log("==============================\n");

  const { waveId, audit } = await runSurfitWave(
    {
      agent_id:         AGENT_ID,
      wave_template_id: "sales_report_v1",
      policy_version:   "sales_report_policy_v1",
      intent:           "Generate weekly sales report with narrative summary and anomaly detection",
      context_refs: {
        input_csv_path:     INPUT_CSV,
        output_report_path: OUTPUT_REPORT,
      },
    },
    // Approval config — not needed for default v1 waves, retained for compatibility
    {
      approved_by: "andreas@surfit.ai",
      note:        "Finance agent POC run",
    }
  );

  console.log("\n=== Finance Agent Complete ===");
  console.log(`Wave ID  : ${waveId}`);
  console.log(`Integrity: ${audit.integrity_status ?? "N/A"}`);
  console.log(`Report   : ${audit.output_path ?? OUTPUT_REPORT}`);
  console.log("==============================\n");
}

// Run directly or export for scheduler
if (require.main === module) {
  run().catch((err) => {
    console.error(`[Finance Agent ERROR] ${err.message}`);
    process.exit(1);
  });
}

module.exports = { run };
