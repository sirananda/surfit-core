from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest, execute_connector_case

DEMO5_CASES = {
    "pr_proposal",
    "merge_without_approval",
    "create_approval_artifact",
    "merge_with_approval",
}


def execute_demo5_case(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    return execute_connector_case(request, deps, strict_deny=True)
