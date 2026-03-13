from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest
from .demo1_runtime_enforcement_handler import (
    execute_builder_brief,
    execute_marketing_digest,
    execute_production_config_wave,
    execute_sales_report,
)
from .demo2_deterministic_governance_handler import execute_demo2_change_control
from .demo3_enterprise_integrations_handler import execute_demo3_enterprise_integrations
from .demo4_governed_github_execution_handler import DEMO4_CASES, execute_demo4_case
from .demo5_execution_handler import DEMO5_CASES, execute_demo5_case
from .demo6_cross_agent_handler import DEMO6_CASES, execute_demo6_case
from .demo7_policy_escalation_handler import DEMO7_CASES, execute_demo7_case
from .demo8_execution_path_handler import DEMO8_CASES, execute_demo8_case


def dispatch_connector_handler(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    case = str(request.connector_context.get("connector_case", "")).strip().lower()
    if case in DEMO4_CASES:
        return execute_demo4_case(request, deps)
    if case in DEMO5_CASES:
        return execute_demo5_case(request, deps)
    if case in DEMO6_CASES:
        return execute_demo6_case(request, deps)
    if case in DEMO7_CASES:
        return execute_demo7_case(request, deps)
    if case in DEMO8_CASES:
        return execute_demo8_case(request, deps)
    return {}


def dispatch_template_handler(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    template = str(request.wave_template_id or "").strip()
    if template == "sales_report_v1":
        return execute_sales_report(request, deps)
    if template == "production_config_change_v1":
        return execute_production_config_wave(request, deps)
    if template in {"marketing_digest_v1", "market_intelligence_digest_v1"}:
        return execute_marketing_digest(request, deps)
    if template == "surfit_builder_brief_v1":
        return execute_builder_brief(request, deps)
    if template == "ENTERPRISE_CHANGE_CONTROL_V1":
        return execute_demo2_change_control(request, deps)
    if template == "ENTERPRISE_INTEGRATION_GOVERNANCE_V1":
        return execute_demo3_enterprise_integrations(request, deps)
    if request.connector_type:
        out = dispatch_connector_handler(request, deps)
        if out:
            return out
    return {}
