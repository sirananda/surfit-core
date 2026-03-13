from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest, execute_connector_case

DEMO4_CASES = {
    "unauthorized_path",
    "unauthorized_action",
    "allowed_pr_workflow",
}


def execute_demo4_case(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    return execute_connector_case(request, deps, strict_deny=True)

