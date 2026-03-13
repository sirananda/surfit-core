from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest, execute_connector_case

DEMO7_CASES = {
    "policy_escalation_routine_operations",
    "policy_escalation_sensitive_operation",
    "policy_escalation_create_approval_artifact",
    "policy_escalation_sensitive_with_approval",
}


def execute_demo7_case(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    return execute_connector_case(request, deps, strict_deny=True)
