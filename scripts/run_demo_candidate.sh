#!/usr/bin/env bash
set -euo pipefail

ACCESS_KEY="partner_alpha_fixed_key_20260315"
TS="$(date +%s)"
WAVE_ID="wave-demo-${TS}"
OUT_DIR="/root/surfit/outputs/demo_candidate_${TS}"
mkdir -p "$OUT_DIR"

curl -fsS http://localhost/healthz > "$OUT_DIR/healthz.json"
curl -fsS http://localhost/readyz > "$OUT_DIR/readyz.json"
curl -s -H "X-Surfit-Tenant-Access: ${ACCESS_KEY}" http://localhost/api/tenant/dashboard/context > "$OUT_DIR/context.json"

curl -s -X POST http://localhost/api/runtime/execution-gateway/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"wave_id\":\"${WAVE_ID}\",\"wave_type\":\"governed_execution\",\"system\":\"github\",\"action\":\"merge_pull_request\",\"risk_level\":\"high\",\"agent_id\":\"gateway_agent\",\"tenant_id\":\"tenant_partner_alpha\",\"approval_required\":true,\"approval_rules\":{\"required_for_actions\":[\"merge_pull_request\"]},\"token_scope\":[\"merge_pull_request\"],\"pinned_policy_manifest\":[\"merge_pull_request\"],\"runtime_rules\":[\"merge_pull_request\"],\"context\":{\"wave_template_id\":\"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1\",\"runtime_rules\":{\"allowlisted_actions\":[\"merge_pull_request\"]}}}" \
  > "$OUT_DIR/evaluate.json"

curl -s -H "X-Surfit-Tenant-Access: ${ACCESS_KEY}" "http://localhost/api/tenant/dashboard/waves/recent?limit=20" > "$OUT_DIR/waves_recent.json"
curl -s -H "X-Surfit-Tenant-Access: ${ACCESS_KEY}" "http://localhost/api/tenant/dashboard/approvals/recent?limit=20" > "$OUT_DIR/approvals_recent.json"

echo "WAVE_ID=${WAVE_ID}" | tee "$OUT_DIR/ids.txt"
echo "OUT_DIR=${OUT_DIR}" | tee -a "$OUT_DIR/ids.txt"
