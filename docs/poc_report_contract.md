# POC Report Contract (sales_report_v1)

Output path: `./outputs/report.md`

Required sections:
1. Title: "Weekly Sales Report"
2. Date range / generated timestamp
3. Deterministic metrics summary (from CSV)
4. One LLM summary paragraph (single call)
5. Approval metadata line (approved_by, approved_at, note)

Notes:
- Write is gated by approval endpoint.
- This is a POC contract for OpenClaw integration.
