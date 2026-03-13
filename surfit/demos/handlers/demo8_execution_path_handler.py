from __future__ import annotations

from ._common import DemoHandlerDeps, DemoHandlerRequest, execute_connector_case

DEMO8_CASES = {
    "execution_path_merge_without_required_path",
    "execution_path_review_commit",
    "execution_path_merge_after_review",
    "execution_path_full_path_sequence",
}


def execute_demo8_case(request: DemoHandlerRequest, deps: DemoHandlerDeps) -> dict[str, object]:
    return execute_connector_case(request, deps, strict_deny=False)
