# Design Partner Environment Guide

Last updated: March 14, 2026

## Purpose

This guide is the operator runbook for setting up one design-partner tenant, issuing one tenant dashboard link, running one governed scenario, and collecting proof artifacts.

## 1) Configure Tenant Entry

Edit tenant config:

```bash
cd /root/surfit
nano tenants/dashboard_access.json
```

Required per-tenant fields:

- `tenant_id`
- `display_name`
- `logo_url`
- `theme.accent`
- `theme.surface`
- `dashboard_access_key`
- `key_created_at`
- `key_expires_at`
- `key_rotated_at`

Recommended pattern:

- set placeholder key first
- rotate immediately using ops script
- set a finite expiration (for example 30 days)

## 2) Rotate Key and Set Expiry

```bash
cd /root/surfit
python3 scripts/ops/rotate_dashboard_key.py --tenant-id tenant_partner_alpha --expires-days 30
```

Save these outputs securely:

- `dashboard_access_key`
- `key_rotated_at`
- `key_expires_at`

## 3) Build Final Tenant Dashboard Link

```bash
cd /root/surfit
python3 scripts/ops/print_tenant_dashboard_link.py --tenant-id tenant_partner_alpha --base-url https://YOUR_DOMAIN
```

Expected format:

- `https://YOUR_DOMAIN/tenant-dashboard?k=<dashboard_access_key>`

## 4) Verify Tenant Access Works

```bash
cd /root/surfit
curl -s "https://YOUR_DOMAIN/api/tenant/dashboard/context" -H "X-Surfit-Tenant-Access: <dashboard_access_key>" | python3 -m json.tool
```

Success checks:

- tenant id matches partner tenant
- display name/logo/theme resolve correctly
- key metadata returned (`key_created_at`, `key_expires_at`, `key_rotated_at`)

## 5) Run Governed Scenario (API-driven)

Use one repeatable low-risk governed scenario:

```bash
curl -s -X POST https://YOUR_DOMAIN/api/runtime/execution-gateway/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "wave_id":"partner-alpha-wave-1",
    "wave_type":"runtime_check",
    "system":"github",
    "action":"read",
    "risk_level":"low",
    "approval_required":false,
    "required_execution_sequence":[],
    "approval_rules":{},
    "execution_timeout":30,
    "trigger_type":"manual",
    "context":{},
    "agent_id":"partner-agent",
    "tenant_id":"tenant_partner_alpha",
    "orchestrator_id":"partner-orch",
    "token_scope":["read"],
    "pinned_policy_manifest":["read"],
    "runtime_rules":["read"]
  }' | python3 -m json.tool
```

Capture from response:

- `decision`
- `reason_code`
- `artifact.artifact_id`

## 5A) Run Approval-Path Scenario (Required Proof)

Use this request to force approval-required behavior:

```bash
curl -s -X POST https://YOUR_DOMAIN/api/runtime/execution-gateway/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "wave_id":"partner-alpha-approval-wave-1",
    "wave_type":"governed_execution",
    "system":"github",
    "action":"merge_pull_request",
    "risk_level":"high",
    "approval_required":true,
    "approval_rules":{"required_for_actions":["merge_pull_request"]},
    "trigger_type":"manual",
    "context":{"wave_template_id":"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1","runtime_rules":{"allowlisted_actions":["merge_pull_request"]}},
    "agent_id":"gateway_agent",
    "tenant_id":"tenant_partner_alpha",
    "token_scope":["merge_pull_request"],
    "pinned_policy_manifest":["merge_pull_request"],
    "runtime_rules":["merge_pull_request"]
  }' | python3 -m json.tool
```

Expected response:

- `decision = PENDING_APPROVAL`
- `reason_code = APPROVAL_REQUIRED`
- `approval_request_id` present
- `artifact.artifact_id` present
- `artifact.approval_linkage.approval_request_id` matches response `approval_request_id`

## 6) Verify in Operator Console

Open:

- `https://YOUR_DOMAIN/surfit-console`

Check:

- wave appears in recent waves for `tenant_partner_alpha`
- wave decision timeline loads
- approvals queue status is visible

## 7) Verify in Tenant Dashboard

Open tenant link:

- `https://YOUR_DOMAIN/tenant-dashboard?k=<dashboard_access_key>`

Check:

- tenant branding appears
- recent waves list includes `partner-alpha-wave-1`
- wave detail shows decision and timing
- artifact link opens JSON modal

## 8) Endpoint Proof Checks

```bash
curl -s "https://YOUR_DOMAIN/api/runtime/waves/recent?tenant_id=tenant_partner_alpha&limit=20" | python3 -m json.tool
curl -s "https://YOUR_DOMAIN/api/runtime/waves/partner-alpha-wave-1/decisions" | python3 -m json.tool
curl -s "https://YOUR_DOMAIN/api/runtime/approvals/recent?tenant_id=tenant_partner_alpha&limit=20" | python3 -m json.tool
curl -s "https://YOUR_DOMAIN/api/runtime/artifacts/<artifact_id>" | python3 -m json.tool
```

Approval-path success checks:

- latest approval-path wave appears in `/api/runtime/waves/recent`
- `/api/runtime/approvals/recent` includes `approval_request_id` with `approval_status = pending`
- `/api/runtime/waves/{wave_id}/decisions` resolves for the approval-path wave
- artifact payload contains `approval_linkage.approval_request_id`

## 9) Proof Package Checklist

Record these fields:

- tenant dashboard URL
- operator console URL
- `wave_id`
- `artifact_id`
- `approval_request_id` (if present)
- `approval_status`
- `decision`
- `reason_code`
- key expiration timestamp

Capture screenshots:

- tenant dashboard home with branding and metrics
- tenant wave detail pane for scenario wave
- operator console wave timeline entry
- operator console decision drill-down
- artifact JSON view

Archive evidence files:

- evaluate response JSON
- endpoint verification JSON outputs
- screenshot files

Ready criteria:

- tenant link works and is tenant-scoped
- governed scenario can be repeated on demand
- artifact and decisions are retrievable
- key lifecycle is monitored with daily cron and healthy log status

## 10) Operator SLA

- warning key state: rotate within 48 hours
- expired key state: rotate immediately and reissue tenant link
