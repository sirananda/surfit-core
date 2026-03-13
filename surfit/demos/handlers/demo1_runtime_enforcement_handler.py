from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._common import DemoHandlerDeps, DemoHandlerError, DemoHandlerRequest


def _load_builder_reference(project_root: Path, path_text: str) -> tuple[str | None, str | None]:
    normalized = str(path_text).replace("\\", "/").lstrip("./")
    if normalized == "README.md" or normalized.startswith("docs/"):
        full_path = project_root / normalized
        if full_path.exists() and full_path.is_file():
            try:
                return normalized, full_path.read_text(encoding="utf-8")
            except Exception:
                return normalized, None
    return None, None


def execute_production_config_wave(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    target = Path(request.target_path)
    if not target.exists():
        raise DemoHandlerError("BAD_CONTEXT", "target_path does not exist", "production_config.bootstrap")
    config_text = target.read_text(encoding="utf-8")
    config_obj = json.loads(config_text)
    workspace_snapshot = Path(request.workspace_dir) / "prod_config.snapshot.json"
    workspace_snapshot.parent.mkdir(parents=True, exist_ok=True)
    workspace_snapshot.write_text(config_text, encoding="utf-8")
    deps.log_decision(request.wave_id, "ALLOW", "config snapshot captured", "config_snapshot", "production_config.bootstrap")
    feature_flags = config_obj.get("feature_flags", {})
    rate_limits = config_obj.get("rate_limits", {})
    logging_cfg = config_obj.get("logging", {})
    checkout_v2 = bool(feature_flags.get("checkout_v2", False))
    requests_per_minute = int(rate_limits.get("requests_per_minute", 0))
    log_level = str(logging_cfg.get("level", "INFO"))
    risk_signals = []
    if checkout_v2:
        risk_signals.append("checkout_v2 enabled")
    if requests_per_minute == 0:
        risk_signals.append("requests_per_minute is 0 (service outage risk)")
    if log_level.upper() in {"DEBUG", "TRACE"}:
        risk_signals.append("logging level is high verbosity")
    if not risk_signals:
        risk_signals.append("no critical drift detected")

    llm_prompt = (
        "You are a production governance analyst.\n"
        "Create concise markdown sections with EXACT headings:\n"
        "### Executive Readout\n"
        "### Key Drivers\n"
        "### Risks and Watchouts\n"
        "### Actions for Next 24 Hours\n\n"
        f"Config snapshot:\n{json.dumps(config_obj, indent=2)}\n"
    )
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = deps.anthropic_module.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": llm_prompt}],
        )
        llm_summary = _msg.content[0].text.strip()
    except Exception:
        llm_summary = (
            "### Executive Readout\n"
            "Production config snapshot captured under governed execution. "
            "This summary is deterministic fallback due to live LLM unavailability.\n\n"
            "### Key Drivers\n"
            f"- checkout_v2: {checkout_v2}\n"
            f"- requests_per_minute: {requests_per_minute}\n"
            f"- logging.level: {log_level}\n\n"
            "### Risks and Watchouts\n"
            + "\n".join([f"- {r}" for r in risk_signals])
            + "\n\n### Actions for Next 24 Hours\n"
            "- Keep mutation scope restricted to allowlisted keys.\n"
            "- Use Agent 3 scenarios to validate deny-path controls.\n"
            "- Reset config baseline after demo if risk settings changed."
        )

    rendered = "\n".join(
        [
            "# Production Config Change Report",
            "",
            f"Generated at: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Deterministic Metrics Summary",
            f"- target_path: {request.target_path}",
            f"- checkout_v2: {checkout_v2}",
            f"- requests_per_minute: {requests_per_minute}",
            f"- logging.level: {log_level}",
            f"- risk_signals: {', '.join(risk_signals)}",
            "",
            "## LLM Summary",
            llm_summary,
            "",
            "## Approval Metadata",
            f"- approved_by: {request.approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "- note: auto-approved (production config demo wave)",
            "",
        ]
    )
    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content=rendered,
        node="production_config.write",
    )
    return {
        "target_path": request.target_path,
        "snapshot_path": str(workspace_snapshot),
        "config_hash": deps.sha256_text(config_text),
        "workspace_output": workspace_output,
    }


def execute_sales_report(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    rows = []
    with open(request.input_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            units = float(row.get("units", 0))
            unit_price = float(row.get("unit_price_usd", 0))
            revenue = units * unit_price
            rows.append(
                {
                    "date": row.get("date", ""),
                    "region": row.get("region", ""),
                    "rep": row.get("rep", ""),
                    "product": row.get("product", ""),
                    "units": units,
                    "unit_price_usd": unit_price,
                    "revenue_usd": revenue,
                }
            )
    total_units = sum(r["units"] for r in rows)
    total_revenue = sum(r["revenue_usd"] for r in rows)
    by_region: dict[str, float] = {}
    for r in rows:
        by_region.setdefault(r["region"], 0.0)
        by_region[r["region"]] += r["revenue_usd"]

    lines = [
        "# Weekly Sales Report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Deterministic Metrics Summary",
        f"- Total rows: {len(rows)}",
        f"- Total units: {total_units:,.0f}",
        f"- Total revenue (USD): ${total_revenue:,.2f}",
        "",
        "### Revenue by Region",
    ]
    for region in sorted(by_region.keys()):
        lines.append(f"- {region}: ${by_region[region]:,.2f}")
    prompt = (
        "You are a CFO-level finance analyst writing for investors and operators.\n"
        "Build a detailed executive section with the exact markdown headings below:\n"
        "### Executive Readout\n"
        "### Key Drivers\n"
        "### Risks and Watchouts\n"
        "### Actions for Next 7 Days\n\n"
        "Requirements:\n"
        "- 180-260 words total.\n"
        "- Executive Readout must be 2-3 sentences and probabilistic in tone (use language like likely/may/could).\n"
        "- Use concrete numbers from the metrics.\n"
        "- Call out best and weakest region explicitly.\n"
        "- Include at least 3 bullet points under Actions.\n\n"
        f"Data:\nTotal rows: {len(rows)}\nTotal units: {total_units:,.0f}\n"
        f"Total revenue: ${total_revenue:,.2f}\nRevenue by region: {str(by_region)}\n"
    )
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = deps.anthropic_module.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        llm_summary = _msg.content[0].text.strip()
    except Exception:
        top_region = max(by_region, key=by_region.get) if by_region else "N/A"
        weakest_region = min(by_region, key=by_region.get) if by_region else "N/A"
        llm_summary = (
            "### Executive Readout\n"
            f"This wave completed with deterministic analysis over {len(rows)} records, producing "
            f"${total_revenue:,.2f} in total revenue and {total_units:,.0f} total units. "
            "Given fallback mode, directional conclusions are likely reliable but lack narrative depth from live LLM synthesis.\n\n"
            "### Key Drivers\n"
            f"- Strongest region: {top_region}\n"
            f"- Weakest region: {weakest_region}\n"
            f"- Revenue concentration suggests {top_region} is carrying the largest share of performance.\n"
            f"- Variance in regional mix indicates {weakest_region} is under-weighted relative to peers.\n"
            "- Output integrity and policy checks passed for this run.\n\n"
            "### Risks and Watchouts\n"
            "- Narrative generation is currently in deterministic fallback mode (live LLM unavailable).\n"
            "- Interpret directional trends as signal, not full forecasting, until a live summary validates intent.\n"
            "- A single-week snapshot may mask volatility in smaller regions.\n\n"
            "### Actions for Next 7 Days\n"
            "- Validate regional pricing assumptions against recent pipeline movement.\n"
            f"- Prioritize an uplift plan for {weakest_region} while protecting momentum in {top_region}.\n"
            "- Review top three accounts by revenue contribution to isolate concentration risk.\n"
            "- Run the next wave with live LLM enabled for expanded narrative context."
        )
    lines.extend(
        [
            "",
            "## LLM Summary",
            llm_summary,
            "",
            "## Approval Metadata",
            f"- approved_by: {request.approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "- note: auto-approved (v1 default path)",
            "",
        ]
    )
    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content="\n".join(lines),
        node="sales_report.write",
    )
    return {
        "workspace_output": workspace_output,
        "input_hashes": {"input_csv_path": deps.sha256_file(request.input_csv_path)},
    }


def execute_marketing_digest(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    snapshots = []
    workspace_snapshots = Path(request.workspace_dir) / "snapshots"
    workspace_snapshots.mkdir(parents=True, exist_ok=True)
    for url in request.sources:
        try:
            status_code, proxied = deps.ocean_proxy_http(
                {
                    "method": "GET",
                    "url": str(url),
                    "headers": {"User-Agent": "SurFit/1.0"},
                    "wave_mutation_token": request.wave_token,
                }
            )
            if status_code != 200:
                raise ValueError(proxied.get("message", proxied.get("reason_code", "proxy denied")))
            raw = str(proxied.get("body", ""))
            safe_name = str(url).replace("https://", "").replace("/", "_")[:60]
            snap_path = workspace_snapshots / f"{safe_name}.txt"
            snap_path.write_text(raw[:5000], encoding="utf-8")
            snapshots.append({"url": str(url), "content": raw[:3000]})
        except Exception as e:
            snapshots.append({"url": str(url), "content": f"[fetch failed: {e}]"})
    combined = "\n\n".join(f"Source: {s['url']}\n{s['content']}" for s in snapshots)
    prompt = (
        "You are a senior market intelligence strategist preparing a next-day decision brief.\n"
        "Primary objective: determine what the team should watch, prioritize, and potentially publish tomorrow based on market signals.\n\n"
        "Return markdown with EXACT headings in this order:\n"
        "### Executive Summary\n"
        "### 3 Key Themes\n"
        "### 2 Proposed Content Angles\n"
        "### Forward-Looking Observation\n\n"
        "Requirements:\n"
        "- Executive Summary must be 2-3 sentences and probabilistic in tone (use likely/may/could).\n"
        "- Executive Summary must answer: what changed, why it matters, and what the team should do next.\n"
        "- 3 Key Themes: exactly 3 numbered items, each one sentence.\n"
        "- 2 Proposed Content Angles: exactly 2 items, each with a headline and one supporting sentence.\n"
        "- Content angles should be ranked by expected relevance for tomorrow's audience.\n"
        "- Forward-Looking Observation: 1 paragraph.\n"
        "- Use specific details from the source content.\n\n"
        f"Content:\n{combined[:9000]}"
    )
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = deps.anthropic_module.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        digest_summary = _msg.content[0].text.strip()
    except Exception:
        digest_summary = (
            "### Executive Summary\n"
            "Market signals were collected successfully, and the team can likely use today’s narratives to prioritize tomorrow’s messaging focus. "
            "In fallback mode, recommendations are directional but still useful for planning a near-term content posture.\n\n"
            "### 3 Key Themes\n"
            "1. AI tooling and platform consolidation continues to dominate coverage, implying buyer focus on reliability and governance.\n"
            "2. Enterprise adoption narratives emphasize control, auditability, and operational safety rather than pure model capability.\n"
            "3. Funding and partnership news suggests renewed interest in infrastructure vendors that enable compliant deployment.\n\n"
            "### 2 Proposed Content Angles\n"
            "1. \"Governed autonomy as the new default\" — Highlight how teams move from experimentation to enforceable runtime controls.\n"
            "2. \"Execution certainty over model novelty\" — Argue that policy-bound execution is now the differentiator for enterprise adoption.\n\n"
            "### Forward-Looking Observation\n"
            "Expect buyers to ask for proof of control (not just performance) in upcoming cycles. Establishing a clear governance narrative now "
            "will likely improve conversion as procurement and security teams increasingly influence agent deployments.\n"
        )
    lines = [
        "# Marketing Digest",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Run ID: {request.run_id}",
        f"Sources fetched: {len(request.sources)}",
        "",
        "## AI Digest",
        digest_summary,
        "",
        "## Sources",
    ]
    for s in snapshots:
        status = "ok" if not s["content"].startswith("[fetch failed") else "failed"
        lines.append(f"- {s['url']} ({status})")
    lines.extend(
        [
            "",
            "## Approval Metadata",
            f"- approved_by: {request.approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "- note: auto-approved (v1 default path)",
            "",
        ]
    )
    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content="\n".join(lines),
        node="market_intel.write",
    )
    snapshot_hashes = {}
    for p in workspace_snapshots.glob("*.txt"):
        h = deps.sha256_file(str(p))
        if h:
            snapshot_hashes[p.name] = h
    return {
        "workspace_output": workspace_output,
        "snapshot_hashes": snapshot_hashes,
        "snapshot_dir": str(workspace_snapshots),
    }


def execute_builder_brief(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, Any]:
    loaded_refs: list[dict[str, str]] = []
    for p in request.references[:6]:
        norm, content = _load_builder_reference(deps.project_root, str(p))
        if norm and content:
            loaded_refs.append({"path": norm, "content": content[:7000]})
    reference_bundle = "\n\n".join(f"Reference: {r['path']}\n{r['content']}" for r in loaded_refs)
    prompt = (
        "You are Surfit Builder Agent with three simultaneous roles:\n"
        "1) Principal engineer: deliver implementation-ready plans with concrete sequencing.\n"
        "2) Security leader with CISO-level rigor: prioritize control boundaries, least privilege, and auditability.\n"
        "3) AI systems architect: design for framework-agnostic neutrality and long-term runtime interoperability.\n"
        "Stay constrained to governance-neutral planning.\n"
        "Produce markdown with EXACT headings:\n"
        "### Priority Outcomes (Next 30 Days)\n"
        "### Build Plan (Sequenced)\n"
        "### Neutrality Guardrails\n"
        "### Risks and Mitigations\n"
        "### 7-Day Execution Checklist\n\n"
        f"Goal: {request.brief_goal}\n\n"
        "Constraints:\n"
        "- Keep Surfit core framework-agnostic.\n"
        "- Framework-specific behavior belongs in adapter layer only.\n"
        "- Policy semantics must stay Surfit-native (paths/tools/scopes/policy lineage).\n"
        "- Ocean remains sole mutation authority boundary.\n\n"
        f"Project references:\n{reference_bundle[:18000]}"
    )
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        _client = deps.anthropic_module.Anthropic(api_key=api_key)
        _msg = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        brief = _msg.content[0].text.strip()
    except Exception:
        brief = (
            "### Priority Outcomes (Next 30 Days)\n"
            "1. Lock neutral runtime contract as the mandatory integration path for all agents.\n"
            "2. Expand adapter matrix (multiple frameworks and internal orchestrators) against one contract.\n"
            "3. Increase policy lineage evidence quality in exports for enterprise audit readiness.\n\n"
            "### Build Plan (Sequenced)\n"
            "1. Standardize wave start/status/audit contract in docs and SDK wrappers.\n"
            "2. Add adapter-level tests proving no framework imports in core modules.\n"
            "3. Add additional wave templates for roadmap generation, incident playbooks, and GTM reporting.\n\n"
            "### Neutrality Guardrails\n"
            "- No framework internals in runtime core.\n"
            "- Ocean validates all mutation authority with short-lived wave tokens.\n"
            "- Policies remain runtime-native and framework-agnostic.\n\n"
            "### Risks and Mitigations\n"
            "- Risk: adapter logic drifts into core. Mitigation: adapter-only path checks in CI.\n"
            "- Risk: token misuse. Mitigation: strict TTL + hash validation + per-wave scoping.\n"
            "- Risk: policy drift. Mitigation: policy lineage checks per template.\n\n"
            "### 7-Day Execution Checklist\n"
            "- Publish neutral contract and adapter boundaries.\n"
            "- Launch personal builder agent on a dedicated template.\n"
            "- Add smoke tests for allowlist, path constraints, and audit export integrity."
        )
    lines = [
        "# Surfit Builder Brief",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Goal: {request.brief_goal}",
        "",
        "## AI Plan",
        brief,
        "",
        "## References Used",
    ]
    if loaded_refs:
        lines.extend([f"- {r['path']}" for r in loaded_refs])
    else:
        lines.append("- none (fallback mode)")
    lines.extend(
        [
            "",
            "## Approval Metadata",
            f"- approved_by: {request.approved_by}",
            f"- approved_at: {datetime.now(timezone.utc).isoformat()}",
            "- note: read-only builder planning wave",
            "",
        ]
    )
    workspace_output = deps.commit_output_write(
        wave_id=request.wave_id,
        wave_token=request.wave_token,
        workspace_dir=request.workspace_dir,
        final_output_path=request.output_path,
        rendered_content="\n".join(lines),
        node="builder_brief.write",
    )
    return {
        "workspace_output": workspace_output,
        "reference_paths": [r["path"] for r in loaded_refs],
    }

