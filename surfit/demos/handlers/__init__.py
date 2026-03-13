"""Demo execution handlers separated from product runtime surfaces."""

from ._common import DemoHandlerDeps, DemoHandlerError, DemoHandlerRequest
from .context_router import ContextPrepDecision, ContextPrepError, PreparedWaveContext, prepare_wave_context
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
from .router import dispatch_connector_handler, dispatch_template_handler

__all__ = [
    "DemoHandlerDeps",
    "DemoHandlerError",
    "DemoHandlerRequest",
    "ContextPrepDecision",
    "ContextPrepError",
    "PreparedWaveContext",
    "prepare_wave_context",
    "DEMO4_CASES",
    "DEMO5_CASES",
    "DEMO6_CASES",
    "DEMO7_CASES",
    "DEMO8_CASES",
    "dispatch_connector_handler",
    "dispatch_template_handler",
    "execute_sales_report",
    "execute_marketing_digest",
    "execute_production_config_wave",
    "execute_builder_brief",
    "execute_demo2_change_control",
    "execute_demo3_enterprise_integrations",
    "execute_demo4_case",
    "execute_demo5_case",
    "execute_demo6_case",
    "execute_demo7_case",
    "execute_demo8_case",
]
