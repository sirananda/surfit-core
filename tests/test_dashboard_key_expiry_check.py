from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ops" / "check_dashboard_key_expiry.py"


class DashboardKeyExpiryCheckTests(unittest.TestCase):
    def _run(self, config: dict, *args: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "dashboard_access.json"
            cfg.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
            cmd = ["python3.11", str(SCRIPT), "--config", str(cfg), *args]
            return subprocess.run(cmd, capture_output=True, text=True)

    def test_valid_key_detection(self):
        config = {
            "tenants": [
                {
                    "tenant_id": "tenant_ok",
                    "display_name": "Tenant OK",
                    "dashboard_access_key": "k1",
                    "key_expires_at": "2099-01-01T00:00:00+00:00",
                }
            ]
        }
        result = self._run(config)
        self.assertEqual(result.returncode, 0)
        self.assertIn("OK: Tenant OK dashboard key valid", result.stdout)

    def test_expiring_soon_detection(self):
        config = {
            "tenants": [
                {
                    "tenant_id": "tenant_warn",
                    "display_name": "Tenant Warn",
                    "dashboard_access_key": "k2",
                    "key_expires_at": "2026-03-16T00:00:00+00:00",
                }
            ]
        }
        result = self._run(config, "--threshold-days", "7")
        self.assertEqual(result.returncode, 1)
        self.assertIn("WARNING: Tenant Warn dashboard key expires in", result.stdout)

    def test_expired_detection(self):
        config = {
            "tenants": [
                {
                    "tenant_id": "tenant_expired",
                    "display_name": "Tenant Expired",
                    "dashboard_access_key": "k3",
                    "key_expires_at": "2025-01-01T00:00:00+00:00",
                }
            ]
        }
        result = self._run(config)
        self.assertEqual(result.returncode, 2)
        self.assertIn("EXPIRED: Tenant Expired dashboard key expired", result.stdout)

    def test_json_mode(self):
        config = {
            "tenants": [
                {
                    "tenant_id": "tenant_ok",
                    "display_name": "Tenant OK",
                    "dashboard_access_key": "k1",
                    "key_expires_at": None,
                }
            ]
        }
        result = self._run(config, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["ok"], 1)
        self.assertEqual(payload["summary"]["warning"], 0)
        self.assertEqual(payload["summary"]["expired"], 0)
        self.assertEqual(payload["tenants"][0]["tenant_id"], "tenant_ok")


if __name__ == "__main__":
    unittest.main()
