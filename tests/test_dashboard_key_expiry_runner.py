from __future__ import annotations

import subprocess
import tempfile
import unittest
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "ops" / "run_dashboard_key_expiry_check.sh"


class DashboardKeyExpiryRunnerTests(unittest.TestCase):
    def test_runner_writes_log_and_returns_checker_exit(self):
        with tempfile.TemporaryDirectory() as td:
            log_file = Path(td) / "dashboard_key_expiry.log"
            env = {
                **os.environ,
                "APP_DIR": str(ROOT),
                "SURFIT_LOG_DIR": str(Path(td) / "logs"),
                "SURFIT_DASHBOARD_KEY_EXPIRY_LOG": str(log_file),
                "SURFIT_DASHBOARD_KEY_THRESHOLD_DAYS": "7",
            }
            proc = subprocess.run(["bash", str(RUNNER)], capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(log_file.exists())
            content = log_file.read_text(encoding="utf-8")
            self.assertIn("[DASHBOARD_KEY_EXPIRY_CHECK]", content)
            self.assertIn("status=OK", content)


if __name__ == "__main__":
    unittest.main()
