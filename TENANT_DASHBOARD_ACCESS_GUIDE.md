# Tenant Dashboard Access Guide

Last updated: March 14, 2026

## Overview

Tenant dashboard access uses a lightweight key bound to one tenant.

- Dashboard URL: `/tenant-dashboard?k=<tenant_dashboard_key>`
- API boundary: `/api/tenant/dashboard/*`
- Key header used after page load: `X-Surfit-Tenant-Access`

The customer dashboard does not accept browser-selected `tenant_id` for data scope.

## Tenant Config Source

Config file path:

- default: `tenants/dashboard_access.json`
- override: `SURFIT_TENANT_DASHBOARD_CONFIG_PATH`

Per-tenant fields:

- `tenant_id`
- `display_name`
- `logo_url` (optional)
- `theme` (optional object)
- `dashboard_access_key`
- `key_created_at`
- `key_expires_at` (optional, `null` means non-expiring)
- `key_rotated_at` (optional)

## Key Expiration Behavior

- If `key_expires_at` is set and current UTC time is past that timestamp, access is rejected (`403`, code `TENANT_DASHBOARD_ACCESS_EXPIRED`).
- If `key_expires_at` is missing or `null`, key is treated as non-expiring.
- Context endpoint returns key lifecycle metadata:
  - `key_created_at`
  - `key_expires_at`
  - `key_rotated_at`

## Rotation Procedure

Use helper script:

```bash
cd /root/surfit
python3 scripts/ops/rotate_dashboard_key.py --tenant-id tenant_acme --expires-days 30
```

Options:

- `--config <path>` custom config path
- `--expires-days <N>` sets new expiry to now + N days
- `--clear-expiry` removes expiry

## Dashboard Key Expiration Monitoring

### Run ad-hoc check

```bash
cd /root/surfit
python3 scripts/ops/check_dashboard_key_expiry.py
```

### Run production wrapper (logs + exit codes)

```bash
cd /root/surfit
bash scripts/ops/run_dashboard_key_expiry_check.sh
```

Log path:

- default: `/var/log/surfit/dashboard_key_expiry.log`

### Install daily cron workflow

```bash
cd /root/surfit
bash scripts/ops/install_dashboard_key_expiry_cron.sh
```

Default schedule: `08:00 UTC` daily.

### JSON mode

```bash
python3 scripts/ops/check_dashboard_key_expiry.py --json
```

### Exit codes

- `0`: no warnings
- `1`: at least one key expiring within threshold
- `2`: at least one key already expired

Default warning threshold is 7 days. Override with:

```bash
python3 scripts/ops/check_dashboard_key_expiry.py --threshold-days 14
```

### Optional webhook hook

Set `SURFIT_OPS_WEBHOOK_URL` in the shell/environment before running wrapper script. If set, wrapper posts minimal summary payload for non-zero states.

If unset, wrapper runs log-only mode.

## Operator Response SLA

- `WARNING`: rotate affected key within **48 hours**.
- `EXPIRED`: rotate key **immediately**, redeploy/reload as needed, and reissue dashboard link.

## Recommended Expiration Patterns

- Early design-partner links: 7-30 days
- Active pilot tenant links: 30-90 days with scheduled rotation
- For high-sensitivity use, rotate immediately after support sessions

## Safe Distribution Practices

- Share links out-of-band (encrypted chat/password manager), not broad channels.
- Avoid posting dashboard URLs in tickets/docs with live keys.
- Regenerate keys immediately if exposed.
- Rotate keys on partner offboarding.

## What This Protects Against

- Easy tenant_id swapping in URL/UI controls.
- Direct dashboard reads for another tenant without a valid bound key.
- Tenant wrapper route access to waves/artifacts outside bound tenant.

## What This Does Not Yet Do

- Full user auth (users/sessions/roles)
- OAuth/SSO
- Full key management platform (issuer identity, revocation audit trail, automatic expiry jobs)
