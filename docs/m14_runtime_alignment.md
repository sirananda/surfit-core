# Milestone 14 — Runtime Alignment (Pattern 1)

SurFit runtime alignment for Pattern 1 is complete (supports persistent agents executing via bursty, bounded Waves).

## Scope
- Pattern 1 only (explicit /waves/run -> status polling).
- No Pattern 2 (no lease tokens / implicit tool gating).
- No UI redesign. Runtime/API behavior only.

## State-machine invariant (default path)
- approval_request_id = null unless status = needs_approval.

## Changes (api.py)

1) POST /api/waves/run (sales_report_v1 POC template)
- agent_id required.
- Agent↔Wave authorization allowlist:
  - openclaw_poc_agent_v1 -> sales_report_v1
- Unauthorized agents rejected with structured 403 payload:
  - { code, message, node }
- Path guardrails retained:
  - input_csv_path under ./data
  - output_report_path under ./outputs
- sales_report_v1 executes inline (POC-specific behavior) and deterministically transitions:
  - running -> complete (or failed)
- Failures persist structured error fields.

2) DB hardening
- waves table columns added:
  - agent_id, error_code, error_message, error_node
- Minimal ALTER TABLE migration helper for legacy DBs.

3) GET /api/waves/{wave_id}/status
- Default path returns:
  - running | complete | failed
- approval_request_id null in default path.
- Failed runs return structured error details.

4) POST /api/approvals/{approval_request_id}
- Endpoint retained for compatibility.
- Not required for default sales_report_v1 completion path.
- Available for future templates that opt into needs_approval.

5) GET /api/waves/{wave_id}/audit/export
- Includes:
  - agent_id, output_path
- Retains:
  - integrity_status, policy_hash, approvals metadata (if present), events, llm_invocations.

## Validation
- Authorized run completed without approvals call.
- Unauthorized agent rejected with AGENT_NOT_AUTHORIZED.
- Successful run status was complete with approval_request_id=null.
- Audit export included integrity_status=VALID, policy_hash, agent_id, output_path.
- ./outputs/report.md created successfully.

## Commit reference
- main @ 013e9a3
- "M13 runtime alignment: auto-complete default waves with agent binding and deterministic termination"
