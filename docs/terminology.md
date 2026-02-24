# SurFit Terminology (Non-Breaking Mapping)

## Core
- `SAW` (legacy/internal term in code): Secure Agent Wave
- `run` (legacy/internal runtime instance): Wave execution instance

## IDs
- `saw_id` (internal): `wave_template_id` (API-facing)
- `run_id` (internal): `wave_id` (API-facing)

## Runtime
- `run_saw(...)` (internal function): execute Secure Agent Wave
- `execution_log` (internal DB table): wave execution event log

## Governance
- approval gate (internal): Anchor (product term)
- write action (internal): mutation event (product term)

## Metrics Mapping (Working)
- `system_time_ms`: Wave Length (excluding Anchor wait)
- `total_ms`: Wave Time (including Anchor wait)
- node count: Wave Depth
- integrity verifier `valid`: Integrity Status

