# Surfit Operator Console Guide

Last updated: March 14, 2026

## Access

- URL path: `/surfit-console`
- Live base URL pattern: `https://<your-domain>/surfit-console` (or `http://<server-ip>/surfit-console` before TLS cutover)
- Console API calls are same-origin and hit:
  - `GET /api/runtime/waves/recent`
  - `GET /api/runtime/waves/{wave_id}/decisions`
  - `GET /api/runtime/approvals/recent`
  - `GET /api/runtime/artifacts/{artifact_id}`

## Pane Overview

- Left pane: **Recent Waves**
  - Shows wave id, system/action, lifecycle status, latest decision, created time.
- Center pane: **Wave Detail + Decision Timeline**
  - Shows selected wave metadata and decision timeline (oldest-first).
- Right pane: **Approvals Queue**
  - Shows approval request id, linked wave id, approval status, system/action, created time.
- Artifact modal:
  - Opens raw JSON for any artifact id link.

## Typical Operator Flow

1. Open `/surfit-console`.
2. Set `Tenant` and `Limit`, then click **Refresh**.
3. In **Recent Waves**, click a wave id.
4. Confirm decision progression in center timeline:
   - reason codes
   - timestamps
   - policy reference/hash fields when present
5. Check **Approvals Queue** for pending approvals linked to the tenant.
6. Open artifact links to inspect stored evidence JSON.

## What To Check First When Something Looks Wrong

1. Health endpoints:

```bash
curl -s http://localhost/healthz | python3 -m json.tool
curl -s http://localhost/readyz | python3 -m json.tool
```

2. Readiness dependency details (DB/Redis/policy path) from `/readyz`.
3. API logs:

```bash
cd /root/surfit
docker-compose logs --tail=200 surfit-api
```

4. Nginx logs if UI loads but API calls fail:

```bash
cd /root/surfit
docker-compose logs --tail=200 surfit-nginx
```

## Known Good Indicators

- `/healthz.status` is `ok`
- `/readyz.status` is `ready`
- Waves list loads for target tenant
- Wave click loads decision timeline
- Approvals pane loads without API errors
- Artifact modal renders JSON for valid artifact ids
