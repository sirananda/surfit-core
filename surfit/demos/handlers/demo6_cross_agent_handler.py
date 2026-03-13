from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest, execute_connector_case

DEMO6_CASES = {
    "cross_agent_openclaw_protected_path",
    "cross_agent_langgraph_pr_workflow",
    "cross_agent_internal_merge_without_approval",
}


def execute_demo6_case(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    return execute_connector_case(request, deps, strict_deny=False)
