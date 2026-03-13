from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surfit.demos.handlers.context_router import prepare_wave_context


class ContextRouterTests(unittest.TestCase):
    def test_production_config_missing_fields(self):
        prepared, err = prepare_wave_context(
            wave_template_id="production_config_change_v1",
            context_refs={},
            intent="",
            connector_type=None,
            market_intel_templates={"marketing_digest_v1"},
            prod_config_target="demo_artifacts/prod_config.json",
            normalize_repo_relative=lambda p: p.strip("./"),
            is_under=lambda base, target: True,
            prepare_connector_context=lambda *args, **kwargs: {},
        )
        self.assertIsNone(prepared)
        self.assertIsNotNone(err)
        self.assertEqual(err.code, "BAD_CONTEXT")
        self.assertEqual(err.rule, "context_required_fields")

    def test_enterprise_integration_context_updates(self):
        prepared, err = prepare_wave_context(
            wave_template_id="ENTERPRISE_INTEGRATION_GOVERNANCE_V1",
            context_refs={"integration_case": "github", "integration_base_url": "http://127.0.0.1:8040"},
            intent="",
            connector_type=None,
            market_intel_templates=set(),
            prod_config_target="demo_artifacts/prod_config.json",
            normalize_repo_relative=lambda p: p.strip("./"),
            is_under=lambda base, target: True,
            prepare_connector_context=lambda *args, **kwargs: {},
        )
        self.assertIsNone(err)
        assert prepared is not None
        self.assertIn("allowed_integration_prefixes", prepared.context_updates)
        self.assertEqual(prepared.integration_case, "github")

    def test_connector_context_error_passthrough(self):
        class _Err(Exception):
            code = "BAD_CONTEXT"
            message = "connector invalid"
            rule = "connector_context_validation"

        prepared, err = prepare_wave_context(
            wave_template_id="ENTERPRISE_GITHUB_GOVERNANCE_V1",
            context_refs={},
            intent="",
            connector_type="github",
            market_intel_templates=set(),
            prod_config_target="demo_artifacts/prod_config.json",
            normalize_repo_relative=lambda p: p.strip("./"),
            is_under=lambda base, target: True,
            prepare_connector_context=lambda *args, **kwargs: (_ for _ in ()).throw(_Err()),
        )
        self.assertIsNone(prepared)
        self.assertIsNotNone(err)
        self.assertEqual(err.code, "BAD_CONTEXT")
        self.assertEqual(err.message, "connector invalid")


if __name__ == "__main__":
    unittest.main()

