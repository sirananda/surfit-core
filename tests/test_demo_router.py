from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surfit.demos.handlers._common import DemoHandlerDeps, DemoHandlerRequest
from surfit.demos.handlers.router import dispatch_connector_handler, dispatch_template_handler


def _deps() -> DemoHandlerDeps:
    return DemoHandlerDeps(
        project_root=ROOT,
        ocean_proxy_http=lambda req: (200, {}),
        commit_output_write=lambda **kwargs: "workspace_output.md",
        log_decision=lambda *args, **kwargs: None,
        dispatch_connector_action=lambda **kwargs: {"allowed": True, "reason_code": "ALLOW", "message": "", "summary": {}},
        sha256_text=lambda x: "hash",
        sha256_file=lambda x: "hash",
        anthropic_module=None,
    )


def _request(**overrides) -> DemoHandlerRequest:
    base = DemoHandlerRequest(
        wave_id="wave-1",
        wave_template_id="sales_report_v1",
        wave_token="tok",
        wave_mutation_token="mtok",
        workspace_dir=str(ROOT / "runs"),
        output_path=str(ROOT / "outputs" / "router_test.md"),
        approved_by="agent",
    )
    payload = {**base.__dict__, **overrides}
    return DemoHandlerRequest(**payload)


class DemoRouterTests(unittest.TestCase):
    def test_dispatch_connector_routes_demo5(self):
        req = _request(connector_type="github", connector_context={"connector_case": "merge_with_approval"})
        deps = _deps()
        with patch("surfit.demos.handlers.router.execute_demo5_case", return_value={"route": "demo5"}) as mock_fn:
            out = dispatch_connector_handler(req, deps)
            self.assertEqual(out, {"route": "demo5"})
            mock_fn.assert_called_once()

    def test_dispatch_template_routes_demo1_sales(self):
        req = _request(wave_template_id="sales_report_v1")
        deps = _deps()
        with patch("surfit.demos.handlers.router.execute_sales_report", return_value={"route": "sales"}) as mock_fn:
            out = dispatch_template_handler(req, deps)
            self.assertEqual(out, {"route": "sales"})
            mock_fn.assert_called_once()

    def test_dispatch_template_unknown_returns_empty(self):
        req = _request(wave_template_id="UNKNOWN_TEMPLATE")
        deps = _deps()
        out = dispatch_template_handler(req, deps)
        self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()

