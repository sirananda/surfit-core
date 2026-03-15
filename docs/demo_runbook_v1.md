Surfit Demo Runbook v1

Duration: 10 minutes

1) Problem framing (1 min)
Explain: agent actions need governance before execution.

2) Submit governed action (2 min)
Call execution gateway for tenant_partner_alpha with merge_pull_request.
Capture wave_id from response.

3) Show governance decision (2 min)
Open operator console and show:
- wave in recent list
- decision state
- linked artifact_id
- linked approval_request_id

4) Show evidence artifact (1 min)
Open artifact JSON and point to:
- decision
- reason_code
- approval_linkage

5) Show approval queue (1 min)
Open approvals recent and show pending approval request.

6) Show tenant visibility (2 min)
Open tenant dashboard with key.
Show:
- recent wave
- decision details
- approval row
- artifact link

7) Close (1 min)
Summarize graph:
execution request -> wave -> decision -> artifact -> approval_request -> tenant visibility
