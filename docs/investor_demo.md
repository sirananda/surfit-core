# SurFit AI Investor Demo Runbook (5 Minutes)

## Objective
Show that SurFit executes AI workflows safely with policy controls, human approval gates, and full auditability.

## Demo Setup (30 sec)
- Open app: `https://surfit-demo.streamlit.app`
- Use SAW: `Board Metrics Aggregation`
- Keep `Approve write step` enabled
- Human wait: `500 ms`

## Flow A: Happy Path (90 sec)
1. Click `Run SAW`
2. Call out:
- `COMPLETED` status
- `Policy Snapshot` (allowlist/denylist)
- `Execution Graph` (all nodes executed)
- `Cycle-Time Breakdown` (system vs human wait)
3. Click `Export Audit Card (.txt)` and mention this is portable evidence.

## Flow B: Policy Enforcement / Denied Path (90 sec)
1. Enable `Force policy deny demo`
2. Click `Run SAW`
3. Call out:
- `DENIED` status
- explicit denial reason
- graph shows blocked node
- log shows exact deny event and timestamp

## Flow C: Historical Traceability (90 sec)
1. Go to `Run History`
2. Show both `completed` and `denied` runs
3. Paste a run ID into `Run ID drill-down`
4. Call out that the same run can be reconstructed with policy + graph + logs.

## Core Message (30 sec)
SurFit is not a black box:
- Preventive controls: policy allow/deny
- Detective controls: execution graph + logs
- Evidence controls: exportable audit card

## If Asked “What’s Next?”
- Policy fingerprint/hash per run
- Approval metadata (`approved_by`, `approved_at`, note)
- Enterprise auth/RBAC for authorized agent-library access

