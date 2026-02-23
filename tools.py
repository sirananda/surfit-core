"""
SurFit V1 — Tool Stubs
Each tool has signature: (inputs: dict, ctx: RunContext) -> ToolResult
Mock implementations return realistic static data.
"""

from __future__ import annotations

from models import RunContext, ToolResult


# ── Read-only: Salesforce ──────────────────────────────────────────

def tool_salesforce_read_pipeline(
    inputs: dict,  # {"date_range": str, "segment": str}
    ctx: RunContext,
) -> ToolResult:
    """Mock: returns pipeline + bookings for a given period/segment."""
    _ = inputs.get("date_range"), inputs.get("segment")
    return ToolResult(
        tool_name="tool_salesforce_read_pipeline",
        success=True,
        data={
            "pipeline_usd": 4_250_000.00,
            "bookings_usd": 1_875_000.00,
            "notes": "Includes 2 deals awaiting legal review.",
        },
    )


# ── Read-only: Stripe ─────────────────────────────────────────────

def tool_stripe_read_revenue(
    inputs: dict,  # {"date_range": str, "currency": str}
    ctx: RunContext,
) -> ToolResult:
    """Mock: returns gross/refund/net revenue."""
    _ = inputs.get("date_range"), inputs.get("currency")
    return ToolResult(
        tool_name="tool_stripe_read_revenue",
        success=True,
        data={
            "gross_revenue_usd": 2_100_000.00,
            "refunds_usd": 45_000.00,
            "net_revenue_usd": 2_055_000.00,
        },
    )


# ── Deterministic: Reconcile ──────────────────────────────────────

def tool_reconcile_metrics(
    inputs: dict,  # {"salesforce": dict, "stripe": dict}
    ctx: RunContext,
) -> ToolResult:
    """Deterministic reconciliation — no LLM involved."""
    sf = inputs.get("salesforce", {})
    st = inputs.get("stripe", {})

    bookings = sf.get("bookings_usd", 0)
    net_rev = st.get("net_revenue_usd", 0)
    delta = bookings - net_rev

    discrepancies = []
    flags = []

    if abs(delta) > 0:
        discrepancies.append({
            "field": "bookings_vs_net_revenue",
            "salesforce_value": bookings,
            "stripe_value": net_rev,
            "delta_usd": delta,
        })
    if abs(delta) / max(bookings, 1) > 0.10:
        flags.append("LARGE_DELTA: bookings vs net revenue diverges >10%")

    reconciled = {
        "pipeline_usd": sf.get("pipeline_usd", 0),
        "bookings_usd": bookings,
        "gross_revenue_usd": st.get("gross_revenue_usd", 0),
        "refunds_usd": st.get("refunds_usd", 0),
        "net_revenue_usd": net_rev,
        "bookings_revenue_delta_usd": delta,
    }

    return ToolResult(
        tool_name="tool_reconcile_metrics",
        success=True,
        data={
            "discrepancies": discrepancies,
            "flags": flags,
            "reconciled_metrics": reconciled,
        },
    )


# ── Stub LLM: GeneratLLMrd Summary ─────────────────────────────

def tool_generate_summary_llm(
    inputs: dict,  # {"reconciled_metrics": dict, "discrepancies": list}
    ctx: RunContext,
) -> ToolResult:
    """Deterministic governed LLM stub: validates structured input, sanitizes prompt payload, returns fixed-temperature-style summary."""
    metrics = inputs.get("reconciled_metrics", {})

    table = (
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Pipeline | ${metrics.get('pipeline_usd', 0):,.0f} |\n"
        f"| Bookings | ${metrics.get('bookings_usd', 0):,.0f} |\n"
        f"| Gross Revenue | ${metrics.get('gross_revenue_usd', 0):,.0f} |\n"
        f"| Refunds | ${metrics.get('refunds_usd', 0):,.0f} |\n"
        f"| Net Revenue | ${metrics.get('net_revenue_usd', 0):,.0f} |\n"
        f"| Bookings–Revenue Delta | ${metrics.get('bookings_revenue_delta_usd', 0):,.0f} |"
    )

    commentary = (
        "Pipeline remains healthy. Net revenue tracks within expected range. "
        "Bookings-to-revenue delta reflects timing of contract activations; "
        "2 deals pending legal review."
    )

    return ToolResult(
        tool_name="tool_generate_summary_llm",
        success=True,
        data={
            "metrics_table_markdown": table,
            "commentary": commentary,
            "llm_meta": {
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "model_version": "gpt-4o-mini-2025-01-15",
                "temperature": 0,
                "max_tokens": 300,
            },
            "raw_tool_input": inputs,
            "sanitized_prompt_input": {
                "reconciled_metrics": metrics,
                "discrepancy_count": len(inputs.get("discrepancies", [])),
            },
            "llm_output_text": commentary,
        },
    )


# ── Write: Update Slides Template ─────────────────────────────────

def tool_slides_update_template(
    inputs: dict,  # {"template_id": str, "metrics_table_markdown": str, "commentary": str}
    ctx: RunContext,
) -> ToolResult:
    """Mock: pretends to update a Google Slides template."""
    template_id = inputs.get("template_id", "")
    if not template_id:
        return ToolResult(
            tool_name="tool_slides_update_template",
            success=False,
            error="template_id is required",
        )
    return ToolResult(
        tool_name="tool_slides_update_template",
        success=True,
        data={
            "status": "updated",
            "updated_slide_ids": ["slide_3", "slide_4"],
        },
    )


# ── Infra: Logger (exempt from policy checks) ─────────────────────

def tool_logger_write(
    inputs: dict,  # {"event": dict}
    ctx: RunContext,
) -> ToolResult:
    """Infra tool — writes are handled by the logging module, not here.
    This stub exists to satisfy the spec's tool registry."""
    return ToolResult(
        tool_name="tool_logger_write",
        success=True,
        data={"status": "logged"},
    )


# ── Revenue Reconciliation Tools ─────────────────────────────────

def tool_quickbooks_read_expenses(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_quickbooks_read_expenses", success=True, data={
        "total_expenses_usd": 1_240_000.00,
        "payroll_usd": 820_000.00,
        "opex_usd": 420_000.00,
        "period": inputs.get("period", "2025-Q1"),
    })

def tool_stripe_read_payouts(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_stripe_read_payouts", success=True, data={
        "total_payouts_usd": 1_980_000.00,
        "pending_usd": 75_000.00,
        "failed_usd": 12_000.00,
    })

def tool_reconcile_revenue(inputs: dict, ctx) -> ToolResult:
    expenses = inputs.get("expenses", {})
    payouts = inputs.get("payouts", {})
    net = payouts.get("total_payouts_usd", 0) - expenses.get("total_expenses_usd", 0)
    margin = round((net / max(payouts.get("total_payouts_usd", 1), 1)) * 100, 1)
    return ToolResult(tool_name="tool_reconcile_revenue", success=True, data={
        "net_position_usd": net,
        "margin_pct": margin,
        "flagged": margin < 20,
    })

def tool_generate_revenue_report(inputs: dict, ctx) -> ToolResult:
    raw = inputs.get("reconciled", {})
    data = raw.get("data", raw) if isinstance(raw, dict) else {}
    net = data.get("net_position_usd", 0)
    margin = data.get("margin_pct", 0)
    flagged = data.get("flagged", False)
    table = (
        "| Metric | Value |\n"
        "|---|---|\n"
        "| Total Payouts | $1,980,000 |\n"
        "| Total Expenses | $1,240,000 |\n"
        f"| Net Position | ${net:,.0f} |\n"
        f"| Margin | {margin}% |\n"
        f"| Flag | {'⚠️ Below 20% threshold' if flagged else '✅ Within range'} |"
    )
    commentary = (
        f"Net position of ${net:,.0f} reflects a {margin}% margin. "
        + ("Margin is below the 20% threshold — review recommended before write." if flagged
           else "Margin is within expected range. No anomalies detected.")
    )
    return ToolResult(tool_name="tool_generate_revenue_report", success=True, data={
        "metrics_table_markdown": table,
        "commentary": commentary,
    })

def tool_write_revenue_report(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_write_revenue_report", success=True, data={
        "status": "written",
        "destination": "finance_reports/q1_revenue_reconciliation.pdf",
    })


# ── Budget Reforecast Tools ───────────────────────────────────────

def tool_pull_actuals(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_pull_actuals", success=True, data={
        "period": inputs.get("period", "2025-Q1"),
        "actuals": {
            "revenue":    2_055_000.00,
            "cogs":         620_000.00,
            "headcount":    940_000.00,
            "opex":         310_000.00,
            "marketing":    195_000.00,
        }
    })

def tool_pull_budget(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_pull_budget", success=True, data={
        "period": inputs.get("period", "2025-Q1"),
        "budget": {
            "revenue":    2_200_000.00,
            "cogs":         600_000.00,
            "headcount":    820_000.00,
            "opex":         300_000.00,
            "marketing":    180_000.00,
        }
    })

def tool_variance_analysis(inputs: dict, ctx) -> ToolResult:
    actuals = inputs.get("actuals", {})
    budget  = inputs.get("budget", {})
    THRESHOLD = 10.0
    lines = {}
    flags = []
    for key in budget:
        a = actuals.get(key, 0)
        b = budget.get(key, 1)
        if key == "revenue":
            variance_pct = round(((a - b) / b) * 100, 1)
            status = "under" if variance_pct < -THRESHOLD else "over" if variance_pct > THRESHOLD else "on_track"
        else:
            variance_pct = round(((a - b) / b) * 100, 1)
            status = "over" if variance_pct > THRESHOLD else "under" if variance_pct < -THRESHOLD else "on_track"
        lines[key] = {
            "actual": a,
            "budget": b,
            "variance_pct": variance_pct,
            "status": status,
        }
        if status != "on_track":
            flags.append(key)
    return ToolResult(tool_name="tool_variance_analysis", success=True, data={
        "lines": lines,
        "flags": flags,
        "flag_count": len(flags),
    })

def tool_gen_reforecast(inputs: dict, ctx) -> ToolResult:
    lines  = inputs.get("lines", {})
    flags  = inputs.get("flags", [])
    QUARTERS = 4
    rows = "| Category | Actual | Budget | Variance | Status |\n|---|---|---|---|---|\n"
    full_year_delta = 0
    for key, d in lines.items():
        icon = "⚠️" if d["status"] != "on_track" else "✅"
        rows += (
            f"| {key.capitalize()} "
            f"| ${d['actual']:,.0f} "
            f"| ${d['budget']:,.0f} "
            f"| {d['variance_pct']:+.1f}% "
            f"| {icon} {d['status'].replace('_',' ')} |\n"
        )
        full_year_delta += (d["actual"] - d["budget"]) * QUARTERS
    confidence = "High" if len(flags) == 0 else "Medium" if len(flags) <= 2 else "Low"
    flag_names = ", ".join(f.capitalize() for f in flags) if flags else "None"
    commentary = (
        f"Q1 actuals show {len(flags)} line(s) outside the 10% variance threshold: {flag_names}. "
        f"Full-year reforecast delta is ${full_year_delta:+,.0f} vs original plan. "
        f"Reforecast confidence: {confidence}. "
        + ("No material adjustments required." if not flags
           else "Review flagged lines before approving reforecast write.")
    )
    return ToolResult(tool_name="tool_gen_reforecast", success=True, data={
        "metrics_table_markdown": rows,
        "commentary": commentary,
        "confidence": confidence,
        "full_year_delta": full_year_delta,
        "flags": flags,
    })

def tool_update_plan(inputs: dict, ctx) -> ToolResult:
    return ToolResult(tool_name="tool_update_plan", success=True, data={
        "status": "written",
        "destination": "planning_tool/q1_reforecast_2025.xlsx",
        "confidence": inputs.get("confidence", "Medium"),
    })

# ── Tool registry (used by the engine to resolve tool names) ──────

TOOL_REGISTRY: dict[str, callable] = {
    "tool_salesforce_read_pipeline": tool_salesforce_read_pipeline,
    "tool_stripe_read_revenue": tool_stripe_read_revenue,
    "tool_reconcile_metrics": tool_reconcile_metrics,
    "tool_generate_summary_llm": tool_generate_summary_llm,
    "tool_generate_board_summary": tool_generate_summary_llm,
    "tool_slides_update_template": tool_slides_update_template,
    "tool_logger_write": tool_logger_write,
    "tool_quickbooks_read_expenses": tool_quickbooks_read_expenses,
    "tool_stripe_read_payouts": tool_stripe_read_payouts,
    "tool_reconcile_revenue": tool_reconcile_revenue,
    "tool_generate_revenue_report": tool_generate_revenue_report,
    "tool_write_revenue_report": tool_write_revenue_report,
    "tool_pull_actuals": tool_pull_actuals,
    "tool_pull_budget": tool_pull_budget,
    "tool_variance_analysis": tool_variance_analysis,
    "tool_gen_reforecast": tool_gen_reforecast,
    "tool_update_plan": tool_update_plan,
}
