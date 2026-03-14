from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ops" / "print_tenant_dashboard_link.py"


class PrintTenantDashboardLinkTests(unittest.TestCase):
    def test_prints_expected_link(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "dashboard_access.json"
            cfg.write_text(
                json.dumps(
                    {
                        "tenants": [
                            {
                                "tenant_id": "tenant_partner_alpha",
                                "display_name": "Partner Alpha",
                                "dashboard_access_key": "abc123",
                                "key_expires_at": "2026-04-13T00:00:00+00:00",
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3.11",
                    str(SCRIPT),
                    "--tenant-id",
                    "tenant_partner_alpha",
                    "--base-url",
                    "https://surfit.example.com",
                    "--config",
                    str(cfg),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("tenant_dashboard_url=https://surfit.example.com/tenant-dashboard?k=abc123", proc.stdout)


if __name__ == "__main__":
    unittest.main()
