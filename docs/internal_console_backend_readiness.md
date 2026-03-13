# Internal Inspection Console Backend Readiness

## Existing read surfaces

- `GET /api/runtime/artifacts/{artifact_id}`
- `GET /api/runtime/artifacts?tenant_id=...&limit=...`
- `GET /api/waves/{wave_id}/status`
- `GET /api/waves/{wave_id}/audit/export`
- `GET /api/waves/{wave_id}/audit/verify`
- `GET /api/approvals/{approval_request_id}`
- `GET /api/metrics/summary`
- `GET /api/metrics/waves`

## Console needs already covered

- Artifact details
- Tenant-scoped artifact list
- Wave status and audit verification
- Summary/time-window metrics

## Gaps to close next

- Tenant-scoped recent wave timeline endpoint with unified decision + approval + artifact pointers
- Decision history endpoint by wave id (normalized schema for UI)
- Approval queue listing endpoint by tenant

## Recommended next backend step

Add one read-only endpoint:

- `GET /api/runtime/waves/recent?tenant_id=...&limit=...`

Response should include:

- `wave_id`, `created_at`, `status`
- latest decision + reason_code
- linked artifact ids
- approval state if present
