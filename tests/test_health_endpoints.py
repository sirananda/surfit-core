from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_allowlists(path: Path) -> None:
    payload = {
        "policy_manifest_version": "health-contract-v1",
        "agent_wave_allowlist": {},
        "template_policy_allowlist": {},
        "http_proxy_allowlist": {"allowed_domains": [], "allowed_methods": ["GET", "POST"], "allowed_url_prefixes": []},
        "template_runtime_scopes": {},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_api(allowlists_path: Path):
    if "anthropic" not in sys.modules:
        fake = types.ModuleType("anthropic")

        class _FakeAnthropic:
            def __init__(self, *args, **kwargs):
                pass

        fake.Anthropic = _FakeAnthropic
        sys.modules["anthropic"] = fake

    os.environ["SURFIT_ENV"] = "dev"
    os.environ["SURFIT_POLICY_ALLOWLISTS_PATH"] = str(allowlists_path)
    os.environ["DATABASE_URL"] = ""
    os.environ["REDIS_URL"] = ""

    if "api" in sys.modules:
        del sys.modules["api"]
    import api  # type: ignore

    importlib.reload(api)
    return api


class HealthEndpointTests(unittest.TestCase):
    def test_healthz_and_readyz(self):
        with tempfile.TemporaryDirectory() as td:
            allowlists = Path(td) / "allowlists.json"
            _write_allowlists(allowlists)
            api = _load_api(allowlists)
            client = TestClient(api.app)

            health = client.get("/healthz")
            self.assertEqual(health.status_code, 200)
            body = health.json()
            self.assertEqual(body["status"], "ok")
            self.assertEqual(body["service"], "surfit-api")

            ready = client.get("/readyz")
            self.assertEqual(ready.status_code, 200)
            ready_body = ready.json()
            self.assertEqual(ready_body["status"], "ready")
            self.assertTrue(ready_body["checks"]["database"]["ready"])
            self.assertTrue(ready_body["checks"]["policy_manifest_path"]["ready"])


if __name__ == "__main__":
    unittest.main()
